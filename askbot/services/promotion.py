from __future__ import annotations

import logging
import time
import json
from dataclasses import dataclass
from datetime import date, datetime, time as dt_time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlmodel import Session, select

from askbot.config import Settings, get_settings
from askbot.models import AppRecord, BufferChannel, GeneratedPost, PromotionRun, RunLog
from askbot.services.buffer_client import BufferClient, BufferPostResult, configured_buffer_clients
from askbot.services.cloudinary_client import CloudinaryMediaClient
from askbot.services.content import ContentGenerator, PLATFORM_BY_SERVICE
from askbot.services.image_generator import PromoImageGenerator
from askbot.services.marketing_planner import MarketingPlanner
from askbot.services.video_generator import PromoVideoGenerator
from askbot.services.play_store import refresh_catalog
from askbot.services.qc import QualityControl
from askbot.services.rotation import select_next_apps
from askbot.services.time_advisor import AITimeAdvisor
from askbot.services.settings_store import (
    SETTING_AUTO_PUBLISH,
    SETTING_DAILY_POST_TIME,
    SETTING_DAILY_VIDEO_TIME,
    SETTING_DEVELOPER_URL,
    SETTING_REQUIRE_IMAGE,
    SETTING_TIMEZONE,
    SETTING_POSTS_PER_DAY,
    SETTING_IMAGE_PROVIDER,
    SETTING_GEMINI_MODEL,
    SETTING_GROQ_MODEL,
    runtime_config,
)

promo_logger = logging.getLogger("askbot.promotion")


@dataclass
class PromotionResult:
    status: str
    message: str
    run_key: str
    app_title: str = ""
    queued_count: int = 0


class PromotionService:
    def __init__(
        self,
        settings: Settings | None = None,
        content_generator: ContentGenerator | None = None,
        image_generator: PromoImageGenerator | None = None,
        video_generator: PromoVideoGenerator | None = None,
        media_client: CloudinaryMediaClient | None = None,
        buffer_client: BufferClient | None = None,
        qc: QualityControl | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.content_generator = content_generator or ContentGenerator(self.settings)
        self.image_generator = image_generator or PromoImageGenerator(settings=self.settings)
        self.video_generator = video_generator or PromoVideoGenerator(settings=self.settings)
        self.marketing_planner = MarketingPlanner(self.settings)
        self.media_client = media_client or CloudinaryMediaClient(self.settings)
        if buffer_client:
            self.buffer_clients = {"primary": buffer_client}
            self.buffer_client = buffer_client
        else:
            self.buffer_clients = configured_buffer_clients(self.settings)
            self.buffer_client = next(iter(self.buffer_clients.values()), BufferClient(self.settings))
        self.qc = qc or QualityControl()

    def publish_manual(
        self,
        session: Session,
        app_id: int,
        posts: dict[str, str],
        image_url: str,
        hashtags: str = "",
        ai_prompt: str = ""
    ) -> str:
        app = session.get(AppRecord, app_id)
        if not app:
            return "App not found."

        channels = session.exec(select(BufferChannel).where(BufferChannel.enabled == True)).all() # noqa: E712
        if not channels:
            return "No enabled Buffer channels found."

        run_key = f"manual-{int(time.time())}"
        total_queued = 0
        
        cfg = runtime_config(session, self.settings)
        zone = ZoneInfo(str(cfg[SETTING_TIMEZONE]))
        due_at = datetime.now(zone) + timedelta(minutes=2)

        for channel in channels:
            platform = PLATFORM_BY_SERVICE.get(channel.service, "generic")
            text = posts.get(platform) or posts.get("generic", "")
            if not text:
                continue

            buffer_client = self._client_for_channel(channel)
            if not buffer_client:
                continue

            try:
                result = self._buffer_create_with_retry(
                    client=buffer_client,
                    channel_id=channel.buffer_channel_id,
                    service=channel.service,
                    text=text,
                    due_at=due_at,
                    image_url=image_url,
                )
                
                self._create_local_post(
                    session,
                    app=app,
                    run_key=run_key,
                    platform=platform,
                    text=text,
                    image_path=Path("manual"), # No local path for manual publish via URL
                    image_url=image_url,
                    hashtags=hashtags,
                    ai_prompt_used=ai_prompt,
                    status="queued",
                    qc_score=100,
                    buffer_account_label=channel.buffer_account_label,
                    buffer_post_id=result.post_id
                )
                total_queued += 1
            except Exception as exc:
                promo_logger.error(f"Manual publish failed for {channel.name}: {exc}")

        session.commit()
        return f"Successfully queued {total_queued} posts to Buffer."

    def refresh_catalog(self, session: Session) -> str:
        cfg = runtime_config(session, self.settings)
        result = refresh_catalog(session, str(cfg[SETTING_DEVELOPER_URL]))
        if result.warning:
            return result.warning
        return f"Discovered {result.discovered} apps and updated {result.updated} records."

    def sync_buffer_channels(self, session: Session) -> str:
        if not self.buffer_clients:
            message = "Buffer API key is not configured."
            session.add(RunLog(level="warning", message=message))
            session.commit()
            return message

        all_channels = []
        for account_label, client in self.buffer_clients.items():
            try:
                all_channels.extend(client.list_channels())
            except Exception as exc:
                session.add(
                    RunLog(
                        level="error",
                        message=f"Buffer channel sync failed for account '{account_label}': {exc}",
                    )
                )

        now = datetime.now(timezone.utc)
        for channel in all_channels:
            existing = session.exec(
                select(BufferChannel).where(BufferChannel.buffer_channel_id == channel.id)
            ).first()
            if existing:
                existing.name = channel.name
                existing.service = channel.service
                existing.buffer_account_label = channel.account_label
                existing.updated_at = now
                session.add(existing)
            else:
                session.add(
                    BufferChannel(
                        buffer_channel_id=channel.id,
                        buffer_account_label=channel.account_label,
                        name=channel.name,
                        service=channel.service,
                    )
                )
        session.commit()
        return f"Synced {len(all_channels)} Buffer channels from {len(self.buffer_clients)} Buffer accounts."

    def run_daily(self, session: Session, target_date: date | None = None, dry_run: bool = False, media_focus: str = "image", force: bool = False) -> PromotionResult:
        promo_logger.info(f"Starting promotion run - media_focus={media_focus}, dry_run={dry_run}, force={force}")
        cfg = runtime_config(session, self.settings)
        zone = ZoneInfo(str(cfg[SETTING_TIMEZONE]))
        today = target_date or datetime.now(zone).date()
        
        if force:
            run_key = f"{today.isoformat()}-{media_focus}-manual-{int(time.time())}"
        else:
            run_key = f"{today.isoformat()}-{media_focus}"
            
        promo_logger.info(f"Run key: {run_key}")

        if not force:
            existing = session.exec(
                select(PromotionRun).where(PromotionRun.run_key == run_key)
            ).first()
            if existing and existing.status in {"queued", "completed", "blocked"}:
                promo_logger.info(f"Skipping run {run_key}: already finished today.")
                return PromotionResult(
                    status=existing.status,
                    message=f"Daily run {run_key} already finished: {existing.message}",
                    run_key=run_key,
                )

        run = PromotionRun(run_key=run_key)
        run.status = "started"
        run.started_at = datetime.now(timezone.utc)
        session.add(run)
        session.commit()

        self.refresh_catalog(session)
        
        limit = int(cfg.get(SETTING_POSTS_PER_DAY, 3))
        apps = select_next_apps(session, run_key, limit=limit)
        if not apps:
            return self._finish(session, run, "blocked", "No enabled apps are available.", "")

        time_advisor = AITimeAdvisor(self.settings)
        total_queued = 0
        total_skipped = 0
        app_titles = []

        for app in apps:
            run.app_id = app.id
            session.add(run)
            session.commit()
            app_titles.append(app.title)

            plan = self.marketing_planner.create_campaign_plan(app)
            content = self.content_generator.generate(app, plan)
            
            image_path, ai_prompt_used, model_used = self.image_generator.create(
                app, 
                content, 
                run_key, 
                selected_feature=content.selected_feature,
                provider_override=str(cfg[SETTING_IMAGE_PROVIDER]),
                model_override=str(cfg[SETTING_GEMINI_MODEL])
            )
            
            image_url = self._upload_with_retry(image_path, session)
            video_path = None
            video_url = ""
            if media_focus == "video":
                video_path = self.video_generator.create(app, content, run_key, selected_feature=content.selected_feature, image_url=image_url)
                if video_path:
                    video_url = self._upload_video_with_retry(video_path, session)

            optimal_times = time_advisor.get_optimal_posting_times(app, plan, today)

            channels = session.exec(select(BufferChannel).where(BufferChannel.enabled == True)).all()  # noqa: E712
            require_image = bool(cfg[SETTING_REQUIRE_IMAGE])
            auto_publish = bool(cfg[SETTING_AUTO_PUBLISH])

            if not channels:
                self._create_local_post(
                    session,
                    app=app,
                    run_key=run_key,
                    platform="generic",
                    text=content.posts["generic"],
                    image_path=image_path,
                    image_url=image_url,
                    video_path=video_path,
                    video_url=video_url,
                    hashtags=content.hashtags,
                    ai_prompt_used=ai_prompt_used,
                    status="draft",
                    qc_score=0,
                    error="No enabled Buffer channels. Sync and enable at least one channel.",
                )
                continue

            for channel in channels:
                platform = PLATFORM_BY_SERVICE.get(channel.service, "generic")
                text = content.posts.get(platform) or content.posts["generic"]
                due_at = optimal_times.get(platform, optimal_times.get("generic", datetime.now(zone)))
                
                media_url = video_url if media_focus == "video" and video_url else image_url
                qc = self.qc.check(
                    session=session,
                    run_key=run_key,
                    platform=platform,
                    text=text,
                    app_link=app.app_link,
                    require_image=require_image,
                    image_url=media_url,
                )

                status = "ready"
                error = "; ".join(qc.reasons)
                buffer_post_id = ""
                if dry_run:
                    status = "draft"
                    error = "Dry run — not posted to Buffer."
                elif qc.approved and auto_publish:
                    buffer_client = self._client_for_channel(channel)
                    if not buffer_client:
                        status = "blocked"
                        error = f"Buffer API key is not configured for account '{channel.buffer_account_label}'."
                    else:
                        try:
                            result = self._buffer_create_with_retry(
                                client=buffer_client,
                                channel_id=channel.buffer_channel_id,
                                service=channel.service,
                                text=text,
                                due_at=due_at,
                                image_url=image_url,
                                video_url=video_url if media_focus == "video" else "",
                                video_title=app.title,
                            )
                            status = "queued"
                            buffer_post_id = result.post_id
                            total_queued += 1
                        except Exception as exc:
                            status = "blocked"
                            error = f"Buffer publish failed: {exc}"
                elif not qc.approved:
                    status = "rejected"

                self._create_local_post(
                    session,
                    app=app,
                    run_key=run_key,
                    platform=platform,
                    text=text,
                    image_path=image_path,
                    image_url=image_url,
                    video_path=video_path,
                    video_url=video_url,
                    hashtags=content.hashtags,
                    ai_prompt_used=ai_prompt_used,
                    status=status,
                    qc_score=qc.score,
                    buffer_account_label=channel.buffer_account_label,
                    buffer_post_id=buffer_post_id,
                    error=error,
                )

            app.last_promoted_at = datetime.now(timezone.utc)
            session.add(app)
            
        session.commit()
        return self._finish(session, run, "queued" if total_queued else "blocked", f"Queued {total_queued} manual posts.", ", ".join(app_titles), total_queued)

    def _finish(self, session: Session, run: PromotionRun, status: str, message: str, app_title: str, queued_count: int = 0) -> PromotionResult:
        run.status = status
        run.message = message
        run.finished_at = datetime.now(timezone.utc)
        session.add(run)
        session.add(RunLog(level="info" if status != "blocked" else "warning", message=message))
        session.commit()
        return PromotionResult(status=status, message=message, run_key=run.run_key, app_title=app_title, queued_count=queued_count)

    def _upload_with_retry(self, image_path: Path, session: Session) -> str:
        if not self.media_client.configured:
            session.add(RunLog(level="warning", message="Cloudinary is not configured; generated image remains local."))
            session.commit()
            return ""

        last_error = ""
        for attempt in range(3):
            try:
                return self.media_client.upload_image(image_path)
            except Exception as exc:
                last_error = str(exc)
                time.sleep(2**attempt)
        session.add(RunLog(level="error", message=f"Cloudinary upload failed after retries: {last_error}"))
        session.commit()
        return ""

    def _upload_video_with_retry(self, video_path: Path, session: Session) -> str:
        if not self.media_client.configured:
            session.add(RunLog(level="warning", message="Cloudinary is not configured; generated video remains local."))
            session.commit()
            return ""

        last_error = ""
        for attempt in range(3):
            try:
                return self.media_client.upload_video(video_path)
            except Exception as exc:
                last_error = str(exc)
                time.sleep(2**attempt)
        session.add(RunLog(level="error", message=f"Cloudinary video upload failed after retries: {last_error}"))
        session.commit()
        return ""

    def _buffer_create_with_retry(self, *, client: BufferClient, channel_id: str, service: str = "", text: str, due_at: datetime, image_url: str, video_url: str = "", video_title: str = "") -> BufferPostResult:
        last_error = ""
        for attempt in range(3):
            try:
                return client.create_post(channel_id=channel_id, text=text, due_at=due_at, image_url=image_url, video_url=video_url, video_title=video_title, mode="customScheduled", service=service)
            except Exception as exc:
                last_error = str(exc)
                time.sleep(2**attempt)
        raise RuntimeError(last_error)

    def _client_for_channel(self, channel: BufferChannel) -> BufferClient | None:
        if channel.buffer_account_label in self.buffer_clients:
            return self.buffer_clients[channel.buffer_account_label]
        if len(self.buffer_clients) == 1:
            return next(iter(self.buffer_clients.values()))
        return None

    @staticmethod
    def _create_local_post(session: Session, *, app: AppRecord, run_key: str, platform: str, text: str, image_path: Path, image_url: str, video_path: Path | None = None, video_url: str = "", hashtags: str = "", ai_prompt_used: str = "", status: str, qc_score: int, buffer_account_label: str = "", error: str = "", buffer_post_id: str = "") -> None:
        session.add(GeneratedPost(app_id=app.id or 0, run_key=run_key, platform=platform, text=text, hashtags=hashtags, image_path=str(image_path), image_url=image_url, video_path=str(video_path or ""), video_url=video_url, ai_prompt_used=ai_prompt_used, qc_score=qc_score, status=status, buffer_account_label=buffer_account_label, buffer_post_id=buffer_post_id, error=error))
        session.commit()
