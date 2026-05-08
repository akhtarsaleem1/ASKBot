from __future__ import annotations

from pathlib import Path

from askbot.models import AppRecord, BufferChannel, GeneratedPost
from askbot.services.buffer_client import BufferPostResult
from askbot.services.content import GeneratedContent
from askbot.services.promotion import PromotionService
from sqlmodel import select


class FakeContentGenerator:
    def generate(self, app, plan=None):
        text = f"Try {app.title} today.\n\nDownload: {app.app_link}"
        return GeneratedContent(
            posts={
                "linkedin": text,
                "twitter": text,
                "facebook": text,
                "threads": text,
                "instagram": text,
                "generic": text,
            },
            headline=app.title,
            subheadline="Useful Android app",
            cta="Get it on Google Play",
            selected_feature="Smart Tasks",
        )


class FakeImageGenerator:
    def __init__(self, tmp_path: Path):
        self.tmp_path = tmp_path

    def create(self, app, content, run_key, selected_feature=""):
        path = self.tmp_path / f"{run_key}-{app.package_name}.png"
        path.write_bytes(b"fake-png")
        return path, "fake-prompt"


class FakeMediaClient:
    configured = True

    def upload_image(self, image_path):
        return "https://cdn.example.com/promo.png"

    def upload_video(self, video_path):
        return "https://cdn.example.com/promo.mp4"


class FakeVideoGenerator:
    def __init__(self, tmp_path: Path):
        self.tmp_path = tmp_path

    def create(self, app, content, run_key, image_url="", selected_feature=""):
        path = self.tmp_path / f"{run_key}-{app.package_name}.mp4"
        path.write_bytes(b"fake-mp4")
        return path


class FakeBufferClient:
    configured = True

    def __init__(self):
        self.created = []

    def create_post(self, **kwargs):
        self.created.append(kwargs)
        return BufferPostResult(post_id=f"post-{len(self.created)}", status="scheduled")


class NoRefreshPromotionService(PromotionService):
    def refresh_catalog(self, session):
        return "skipped"


def seed_app_and_channel(session):
    app = AppRecord(
        package_name="com.example.app",
        title="Example App",
        app_link="https://play.google.com/store/apps/details?id=com.example.app",
        short_description="A helpful app for daily tasks.",
    )
    channel = BufferChannel(
        buffer_channel_id="channel-1",
        name="LinkedIn",
        service="linkedin",
    )
    session.add(app)
    session.add(channel)
    session.commit()


def seed_app_and_two_channels(session):
    app = AppRecord(
        package_name="com.example.app",
        title="Example App",
        app_link="https://play.google.com/store/apps/details?id=com.example.app",
        short_description="A helpful app for daily tasks.",
    )
    session.add(app)
    session.add(
        BufferChannel(
            buffer_channel_id="channel-primary",
            buffer_account_label="primary",
            name="LinkedIn Primary",
            service="linkedin",
        )
    )
    session.add(
        BufferChannel(
            buffer_channel_id="channel-account2",
            buffer_account_label="account2",
            name="LinkedIn Second",
            service="linkedin",
        )
    )
    session.commit()


def test_daily_promotion_queues_post_and_stores_buffer_id(session, test_settings):
    seed_app_and_channel(session)
    asset_dir = Path("data/test-assets")
    asset_dir.mkdir(parents=True, exist_ok=True)
    buffer_client = FakeBufferClient()
    service = NoRefreshPromotionService(
        settings=test_settings,
        content_generator=FakeContentGenerator(),
        image_generator=FakeImageGenerator(asset_dir),
        media_client=FakeMediaClient(),
        buffer_client=buffer_client,
    )

    result = service.run_daily(session, target_date=__import__("datetime").date(2026, 5, 7))

    posts = session.exec(select(GeneratedPost)).all()
    assert result.status == "queued"
    assert result.queued_count == 1
    assert len(posts) == 1
    assert posts[0].buffer_post_id == "post-1"
    assert posts[0].image_url == "https://cdn.example.com/promo.png"
    assert len(buffer_client.created) == 1


def test_daily_promotion_does_not_duplicate_same_day_after_restart(session, test_settings):
    seed_app_and_channel(session)
    asset_dir = Path("data/test-assets")
    asset_dir.mkdir(parents=True, exist_ok=True)
    buffer_client = FakeBufferClient()
    service = NoRefreshPromotionService(
        settings=test_settings,
        content_generator=FakeContentGenerator(),
        image_generator=FakeImageGenerator(asset_dir),
        media_client=FakeMediaClient(),
        buffer_client=buffer_client,
    )
    target_date = __import__("datetime").date(2026, 5, 7)

    first = service.run_daily(session, target_date=target_date)
    second = service.run_daily(session, target_date=target_date)

    posts = session.exec(select(GeneratedPost)).all()
    assert first.status == "queued"
    assert second.status == "queued"
    assert len(posts) == 1
    assert len(buffer_client.created) == 1


def test_daily_promotion_routes_channels_to_matching_buffer_accounts(session, test_settings):
    seed_app_and_two_channels(session)
    asset_dir = Path("data/test-assets")
    asset_dir.mkdir(parents=True, exist_ok=True)
    primary_client = FakeBufferClient()
    second_client = FakeBufferClient()
    service = NoRefreshPromotionService(
        settings=test_settings,
        content_generator=FakeContentGenerator(),
        image_generator=FakeImageGenerator(asset_dir),
        media_client=FakeMediaClient(),
        buffer_client=primary_client,
    )
    service.buffer_clients = {"primary": primary_client, "account2": second_client}

    result = service.run_daily(session, target_date=__import__("datetime").date(2026, 5, 8))

    posts = session.exec(select(GeneratedPost)).all()
    assert result.status == "queued"
    assert result.queued_count == 2
    assert len(primary_client.created) == 1
    assert len(second_client.created) == 1
    assert primary_client.created[0]["channel_id"] == "channel-primary"
    assert second_client.created[0]["channel_id"] == "channel-account2"
    assert {post.buffer_account_label for post in posts} == {"primary", "account2"}


def test_daily_promotion_sets_post_type_for_facebook_and_instagram(session, test_settings):
    app = AppRecord(
        package_name="com.example.app",
        title="Example App",
        app_link="https://play.google.com/store/apps/details?id=com.example.app",
        short_description="A helpful app for daily tasks.",
    )
    session.add(app)
    session.add(
        BufferChannel(
            buffer_channel_id="facebook-channel",
            buffer_account_label="primary",
            name="Facebook",
            service="facebook",
        )
    )
    session.add(
        BufferChannel(
            buffer_channel_id="instagram-channel",
            buffer_account_label="primary",
            name="Instagram",
            service="instagram",
        )
    )
    session.commit()
    asset_dir = Path("data/test-assets")
    asset_dir.mkdir(parents=True, exist_ok=True)
    buffer_client = FakeBufferClient()
    service = NoRefreshPromotionService(
        settings=test_settings,
        content_generator=FakeContentGenerator(),
        image_generator=FakeImageGenerator(asset_dir),
        media_client=FakeMediaClient(),
        buffer_client=buffer_client,
    )

    result = service.run_daily(session, target_date=__import__("datetime").date(2026, 5, 9))

    assert result.status == "queued"
    assert result.queued_count == 2
    assert [created["service"] for created in buffer_client.created] == ["facebook", "instagram"]


def test_daily_promotion_skips_youtube_image_posts(session, test_settings):
    app = AppRecord(
        package_name="com.example.app",
        title="Example App",
        app_link="https://play.google.com/store/apps/details?id=com.example.app",
        short_description="A helpful app for daily tasks.",
    )
    session.add(app)
    session.add(
        BufferChannel(
            buffer_channel_id="youtube-channel",
            buffer_account_label="primary",
            name="YouTube",
            service="youtube",
        )
    )
    session.commit()
    asset_dir = Path("data/test-assets")
    asset_dir.mkdir(parents=True, exist_ok=True)
    buffer_client = FakeBufferClient()
    service = NoRefreshPromotionService(
        settings=test_settings,
        content_generator=FakeContentGenerator(),
        image_generator=FakeImageGenerator(asset_dir),
        media_client=FakeMediaClient(),
        buffer_client=buffer_client,
    )

    result = service.run_daily(session, target_date=__import__("datetime").date(2026, 5, 10))

    posts = session.exec(select(GeneratedPost)).all()
    assert result.status == "skipped"
    assert result.queued_count == 0
    assert len(buffer_client.created) == 0
    assert posts[0].status == "skipped"


def test_video_generated_even_without_youtube_channel(session, test_settings):
    """Video should be generated for all runs, not only when a YouTube channel exists."""
    app = AppRecord(
        package_name="com.example.app",
        title="Example App",
        app_link="https://play.google.com/store/apps/details?id=com.example.app",
        short_description="A helpful app for daily tasks.",
    )
    session.add(app)
    session.add(
        BufferChannel(
            buffer_channel_id="instagram-channel",
            buffer_account_label="primary",
            name="Instagram",
            service="instagram",
        )
    )
    session.commit()
    asset_dir = Path("data/test-assets")
    asset_dir.mkdir(parents=True, exist_ok=True)
    video_gen = FakeVideoGenerator(asset_dir)
    buffer_client = FakeBufferClient()
    service = NoRefreshPromotionService(
        settings=test_settings,
        content_generator=FakeContentGenerator(),
        image_generator=FakeImageGenerator(asset_dir),
        video_generator=video_gen,
        media_client=FakeMediaClient(),
        buffer_client=buffer_client,
    )

    result = service.run_daily(
        session, target_date=__import__("datetime").date(2026, 5, 11), media_focus="video"
    )

    posts = session.exec(select(GeneratedPost)).all()
    assert result.status == "queued"
    assert len(posts) == 1
    assert posts[0].video_path.endswith(".mp4")
    assert posts[0].video_url == "https://cdn.example.com/promo.mp4"
    # All platforms receive video during video-focus runs
    assert buffer_client.created[0]["image_url"] == "https://cdn.example.com/promo.png"
    assert buffer_client.created[0]["video_url"] == "https://cdn.example.com/promo.mp4"


def test_dry_run_generates_media_without_buffer_post(session, test_settings):
    """Dry-run mode creates image and video but never calls Buffer."""
    app = AppRecord(
        package_name="com.example.app",
        title="Example App",
        app_link="https://play.google.com/store/apps/details?id=com.example.app",
        short_description="A helpful app for daily tasks.",
    )
    session.add(app)
    session.add(
        BufferChannel(
            buffer_channel_id="facebook-channel",
            buffer_account_label="primary",
            name="Facebook",
            service="facebook",
        )
    )
    session.commit()
    asset_dir = Path("data/test-assets")
    asset_dir.mkdir(parents=True, exist_ok=True)
    video_gen = FakeVideoGenerator(asset_dir)
    buffer_client = FakeBufferClient()
    service = NoRefreshPromotionService(
        settings=test_settings,
        content_generator=FakeContentGenerator(),
        image_generator=FakeImageGenerator(asset_dir),
        video_generator=video_gen,
        media_client=FakeMediaClient(),
        buffer_client=buffer_client,
    )

    result = service.run_daily(
        session, target_date=__import__("datetime").date(2026, 5, 12), dry_run=True, media_focus="video"
    )

    posts = session.exec(select(GeneratedPost)).all()
    assert result.status == "draft"
    assert "Dry run" in result.message
    assert len(buffer_client.created) == 0
    assert len(posts) == 1
    assert posts[0].status == "draft"
    assert posts[0].image_path.endswith(".png")
    assert posts[0].video_path.endswith(".mp4")
