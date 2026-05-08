from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, col, func, select

from askbot.config import PROJECT_ROOT, get_settings
from askbot.database import get_session
from askbot.models import AppRecord, BufferChannel, GeneratedPost, PromotionRun, RunLog, PostMetrics
from askbot.services.marketing_planner import MarketingPlanner
from askbot.services.content import ContentGenerator
from askbot.services.image_generator import PromoImageGenerator
from askbot.services.play_store import normalize_app_link, package_from_link
from askbot.services.promotion import PromotionService
from askbot.services.settings_store import (
    SETTING_AUTO_PUBLISH,
    SETTING_DAILY_POST_TIME,
    SETTING_DAILY_VIDEO_TIME,
    SETTING_DEVELOPER_URL,
    SETTING_REQUIRE_IMAGE,
    SETTING_TIMEZONE,
    SETTING_IMAGE_PROVIDER,
    SETTING_GEMINI_MODEL,
    SETTING_GROQ_MODEL,
    SETTING_POSTS_PER_DAY,
    runtime_config,
    set_setting,
)
from askbot.scheduler import refresh_scheduler


router = APIRouter()
templates = Jinja2Templates(directory=str(PROJECT_ROOT / "askbot" / "templates"))
settings = get_settings()


def redirect(path: str) -> RedirectResponse:
    return RedirectResponse(path, status_code=303)


def flash(session: Session, message: str, level: str = "info") -> None:
    session.add(RunLog(level=level, message=message))
    session.commit()


@router.get("/")
def home(request: Request, session: Session = Depends(get_session)):
    app_count = session.exec(select(func.count(AppRecord.id))).one()
    enabled_app_count = session.exec(
        select(func.count(AppRecord.id)).where(AppRecord.enabled == True)  # noqa: E712
    ).one()
    channel_count = session.exec(select(func.count(BufferChannel.id))).one()
    queued_count = session.exec(
        select(func.count(GeneratedPost.id)).where(GeneratedPost.status == "queued")
    ).one()
    latest_runs = session.exec(
        select(PromotionRun).order_by(PromotionRun.started_at.desc()).limit(5)
    ).all()
    latest_posts = session.exec(
        select(GeneratedPost).order_by(GeneratedPost.created_at.desc()).limit(8)
    ).all()
    logs = session.exec(select(RunLog).order_by(RunLog.created_at.desc()).limit(4)).all()
    cfg = runtime_config(session, settings)
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "request": request,
            "stats": {
                "apps": app_count,
                "enabled_apps": enabled_app_count,
                "channels": channel_count,
                "queued": queued_count,
            },
            "runs": latest_runs,
            "posts": latest_posts,
            "logs": logs,
            "cfg": cfg,
            "now": datetime.now(),
        },
    )


@router.post("/actions/run-now")
def run_now(session: Session = Depends(get_session)):
    result = PromotionService(settings).run_daily(session, force=True)
    flash(session, result.message, "info" if result.status == "queued" else "warning")
    return redirect("/")


@router.post("/actions/refresh-apps")
def refresh_apps(session: Session = Depends(get_session)):
    message = PromotionService(settings).refresh_catalog(session)
    flash(session, message)
    return redirect("/apps")


@router.post("/actions/sync-buffer")
def sync_buffer(session: Session = Depends(get_session)):
    message = PromotionService(settings).sync_buffer_channels(session)
    flash(session, message)
    return redirect("/channels")


@router.get("/apps")
def apps(request: Request, session: Session = Depends(get_session)):
    records = session.exec(select(AppRecord).order_by(AppRecord.title)).all()
    logs = session.exec(select(RunLog).order_by(RunLog.created_at.desc()).limit(3)).all()
    cfg = runtime_config(session, settings)
    return templates.TemplateResponse(
        request,
        "apps.html",
        {"request": request, "apps": records, "logs": logs, "cfg": cfg},
    )


@router.post("/apps/manual")
def add_manual_app(
    title: str = Form(...),
    app_link: str = Form(...),
    short_description: str = Form(""),
    session: Session = Depends(get_session),
):
    package = package_from_link(app_link)
    if not package:
        flash(session, "Could not add app: Play Store link must include a package id.", "error")
        return redirect("/apps")

    existing = session.exec(select(AppRecord).where(AppRecord.package_name == package)).first()
    if existing:
        existing.title = title.strip() or package
        existing.short_description = short_description.strip()
        existing.app_link = normalize_app_link(package)
        session.add(existing)
        flash(session, f"Updated {existing.title}.")
    else:
        session.add(
            AppRecord(
                package_name=package,
                title=title.strip() or package,
                app_link=normalize_app_link(package),
                short_description=short_description.strip(),
            )
        )
        flash(session, f"Added {title.strip() or package}.")
    session.commit()
    return redirect("/apps")


@router.post("/apps/{app_id}/toggle")
def toggle_app(app_id: int, session: Session = Depends(get_session)):
    app = session.get(AppRecord, app_id)
    if app:
        app.enabled = not app.enabled
        session.add(app)
        session.commit()
        flash(session, f"{app.title} is now {'enabled' if app.enabled else 'disabled'}.")
    return redirect("/apps")


@router.post("/apps/{app_id}/update")
def update_app(
    app_id: int,
    title: str = Form(...),
    short_description: str = Form(""),
    app_link: str = Form(...),
    session: Session = Depends(get_session),
):
    app = session.get(AppRecord, app_id)
    package = package_from_link(app_link)
    if not app or not package:
        flash(session, "Could not update app. Check the Play Store link.", "error")
        return redirect("/apps")
    app.title = title.strip() or app.title
    app.short_description = short_description.strip()
    app.package_name = package
    app.app_link = normalize_app_link(package)
    session.add(app)
    session.commit()
    flash(session, f"Updated {app.title}.")
    return redirect("/apps")


@router.get("/channels")
def channels(request: Request, session: Session = Depends(get_session)):
    records = session.exec(select(BufferChannel).order_by(BufferChannel.service, BufferChannel.name)).all()
    logs = session.exec(select(RunLog).order_by(RunLog.created_at.desc()).limit(3)).all()
    return templates.TemplateResponse(
        request,
        "channels.html",
        {"request": request, "channels": records, "logs": logs, "buffer_configured": settings.buffer_configured},
    )


@router.post("/channels/{channel_id}/toggle")
def toggle_channel(channel_id: int, session: Session = Depends(get_session)):
    channel = session.get(BufferChannel, channel_id)
    if channel:
        channel.enabled = not channel.enabled
        session.add(channel)
        session.commit()
        flash(session, f"{channel.name} is now {'enabled' if channel.enabled else 'disabled'}.")
    return redirect("/channels")


@router.get("/posts")
def posts(request: Request, session: Session = Depends(get_session)):
    records = session.exec(select(GeneratedPost).order_by(GeneratedPost.created_at.desc()).limit(100)).all()
    app_map = {app.id: app for app in session.exec(select(AppRecord)).all()}
    return templates.TemplateResponse(
        request,
        "posts.html",
        {"request": request, "posts": records, "app_map": app_map},
    )


@router.get("/settings")
def settings_page(request: Request, session: Session = Depends(get_session)):
    cfg = runtime_config(session, settings)
    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "request": request,
            "cfg": cfg,
            "keys": {
                "groq": bool(settings.groq_api_key),
                "buffer": settings.buffer_configured,
                "cloudinary": settings.cloudinary_configured,
            },
        },
    )


@router.post("/settings")
def update_settings(
    request: Request,
    developer_url: str = Form(...),
    daily_post_time: str = Form(...),
    daily_video_time: str = Form(...),
    timezone: str = Form(...),
    auto_publish_after_qc: str = Form("false"),
    require_image_asset: str = Form("false"),
    posts_per_day: str = Form("3"),
    creative_image_provider: str = Form("gemini"),
    gemini_image_model: str = Form("gemini-2.0-flash"),
    groq_model: str = Form("llama-3.3-70b-versatile"),
    session: Session = Depends(get_session),
):
    set_setting(session, SETTING_DEVELOPER_URL, developer_url.strip())
    set_setting(session, SETTING_DAILY_POST_TIME, daily_post_time.strip())
    set_setting(session, SETTING_DAILY_VIDEO_TIME, daily_video_time.strip())
    set_setting(session, SETTING_TIMEZONE, timezone.strip())
    set_setting(session, SETTING_AUTO_PUBLISH, auto_publish_after_qc)
    set_setting(session, SETTING_REQUIRE_IMAGE, require_image_asset)
    set_setting(session, SETTING_POSTS_PER_DAY, posts_per_day.strip())
    set_setting(session, SETTING_IMAGE_PROVIDER, creative_image_provider.strip())
    set_setting(session, SETTING_GEMINI_MODEL, gemini_image_model.strip())
    set_setting(session, SETTING_GROQ_MODEL, groq_model.strip())
    
    # Refresh scheduler to pick up timing changes
    scheduler = getattr(request.app.state, "scheduler", None)
    if scheduler:
        refresh_scheduler(scheduler, settings, session)
        
    flash(session, "Settings updated and bot synchronized.")
    return redirect("/settings")


@router.get("/logs")
def logs(request: Request, session: Session = Depends(get_session)):
    records = session.exec(select(RunLog).order_by(RunLog.created_at.desc()).limit(200)).all()
    runs = session.exec(select(PromotionRun).order_by(PromotionRun.started_at.desc()).limit(50)).all()
    return templates.TemplateResponse(
        request,
        "logs.html",
        {"request": request, "logs": records, "runs": runs},
    )


@router.get("/gallery")
def gallery(request: Request, session: Session = Depends(get_session)):
    records = session.exec(
        select(GeneratedPost)
        .where(GeneratedPost.image_path != "")
        .order_by(GeneratedPost.created_at.desc())
    ).all()
    
    seen = set()
    unique_posts = []
    for p in records:
        if p.image_path not in seen:
            seen.add(p.image_path)
            unique_posts.append(p)
            
    apps = session.exec(select(AppRecord)).all()
    app_map = {app.id: app for app in apps}
    
    return templates.TemplateResponse(
        request,
        "gallery.html",
        {"request": request, "posts": unique_posts, "app_map": app_map},
    )


@router.get("/history")
def history(request: Request, session: Session = Depends(get_session)):
    records = session.exec(select(GeneratedPost).order_by(GeneratedPost.created_at.desc()).limit(100)).all()
    
    apps = session.exec(select(AppRecord)).all()
    app_map = {app.id: app for app in apps}
    
    metrics = session.exec(select(PostMetrics)).all()
    metrics_map = {m.post_id: m for m in metrics}
    
    return templates.TemplateResponse(
        request,
        "history.html",
        {"request": request, "posts": records, "app_map": app_map, "metrics_map": metrics_map},
    )


@router.get("/preview")
def preview(request: Request, session: Session = Depends(get_session)):
    apps = session.exec(select(AppRecord).where(AppRecord.enabled == True).order_by(AppRecord.title)).all()
    return templates.TemplateResponse(
        request,
        "preview.html",
        {"request": request, "apps": apps, "preview_data": None},
    )


@router.post("/preview/generate")
def generate_preview(request: Request, app_id: int = Form(...), session: Session = Depends(get_session)):
    app = session.get(AppRecord, app_id)
    if not app:
        flash(session, "App not found.", "error")
        return redirect("/preview")
        
    apps = session.exec(select(AppRecord).where(AppRecord.enabled == True).order_by(AppRecord.title)).all()
    
    # Use runtime config for models/providers
    cfg = runtime_config(session, settings)
    
    content_gen = ContentGenerator(settings=settings)
    image_gen = PromoImageGenerator(settings=settings)
    
    try:
        content = content_gen.generate(app, {})
        run_key = f"preview-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        preview_data = {
            "app_id": app.id,
            "app_title": app.title,
            "posts": content.posts,
            "hashtags": content.hashtags,
            "ai_prompt": "",
            "image_url": "",
            "image_model": "",
        }
        try:
            image_path, prompt_used, model_name = image_gen.create(
                app, 
                content, 
                run_key, 
                selected_feature=content.selected_feature,
                provider_override=str(cfg[SETTING_IMAGE_PROVIDER]),
                model_override=str(cfg[SETTING_GEMINI_MODEL])
            )
            filename = Path(image_path).name
            preview_data["image_url"] = f"/api/images/{filename}"
            preview_data["ai_prompt"] = prompt_used
            preview_data["image_model"] = model_name
        except Exception:
            import traceback, logging
            img_err = traceback.format_exc()
            logging.error(f"Image generation failed for preview (app {app_id}):\n{img_err}")
            preview_data["image_error"] = "Image generation failed — all providers exhausted. Posts generated successfully below."

        return templates.TemplateResponse(
            request,
            "preview.html",
            {"request": request, "apps": apps, "preview_data": preview_data, "selected_app": app_id},
        )
    except Exception:
        import traceback, logging
        err_msg = traceback.format_exc()
        logging.error(f"Preview generation failed for app {app_id}:\n{err_msg}")
        return templates.TemplateResponse(
            request,
            "preview.html",
            {
                "request": request,
                "apps": apps,
                "preview_data": None,
                "selected_app": app_id,
                "error_message": f"Preview generation failed: {err_msg[-500:]}",
            },
        )


@router.post("/preview/publish")
def publish_preview(
    app_id: int = Form(...),
    posts_json: str = Form(...),
    image_url: str = Form(...),
    hashtags: str = Form(""),
    ai_prompt: str = Form(""),
    session: Session = Depends(get_session)
):
    try:
        posts = json.loads(posts_json)
        service = PromotionService(settings)
        message = service.publish_manual(
            session=session,
            app_id=app_id,
            posts=posts,
            image_url=image_url,
            hashtags=hashtags,
            ai_prompt=ai_prompt
        )
        flash(session, message)
    except Exception as e:
        flash(session, f"Publishing failed: {e}", "error")
        
    return redirect("/preview")


@router.get("/api/images/{filename}")
def serve_image(filename: str):
    from askbot.config import ASSET_DIR
    path = ASSET_DIR / filename
    if path.exists() and path.is_file():
        return FileResponse(path)
    return {"detail": "Image not found"}, 404


@router.get("/analytics")
def analytics(request: Request, session: Session = Depends(get_session)):
    try:
        layout_stats = session.exec(
            select(
                GeneratedPost.layout_used,
                func.avg(PostMetrics.impressions).label("avg_impressions"),
                func.avg(PostMetrics.clicks).label("avg_clicks"),
                func.count(GeneratedPost.id).label("post_count")
            )
            .join(PostMetrics, GeneratedPost.id == PostMetrics.post_id)
            .where(GeneratedPost.layout_used != "")
            .group_by(GeneratedPost.layout_used)
            .order_by(func.avg(PostMetrics.clicks).desc())
        ).all()
    except Exception:
        layout_stats = []
        
    return templates.TemplateResponse(
        request,
        "analytics.html",
        {"request": request, "layout_stats": layout_stats},
    )

@router.post("/actions/sync-analytics")
def sync_analytics(session: Session = Depends(get_session)):
    from askbot.services.analytics import AnalyticsFetcher
    fetcher = AnalyticsFetcher()
    fetcher.sync_metrics(session)
    flash(session, "Analytics sync completed successfully.", "info")
    return redirect("/analytics")
