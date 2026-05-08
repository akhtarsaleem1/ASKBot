from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Session, select

from askbot.config import Settings
from askbot.models import Setting


SETTING_DEVELOPER_URL = "developer_url"
SETTING_DAILY_POST_TIME = "daily_post_time"
SETTING_DAILY_VIDEO_TIME = "daily_video_time"
SETTING_TIMEZONE = "timezone"
SETTING_AUTO_PUBLISH = "auto_publish_after_qc"
SETTING_REQUIRE_IMAGE = "require_image_asset"
SETTING_POSTS_PER_DAY = "posts_per_day"
SETTING_IMAGE_PROVIDER = "creative_image_provider"
SETTING_GEMINI_MODEL = "gemini_image_model"
SETTING_GROQ_MODEL = "groq_model"


def get_setting(session: Session, key: str, default: str) -> str:
    row = session.exec(select(Setting).where(Setting.key == key)).first()
    return row.value if row else default


def set_setting(session: Session, key: str, value: str) -> None:
    row = session.exec(select(Setting).where(Setting.key == key)).first()
    if row:
        row.value = value
        row.updated_at = datetime.now(timezone.utc)
        session.add(row)
    else:
        session.add(Setting(key=key, value=value))
    session.commit()


def bool_from_setting(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def runtime_config(session: Session, settings: Settings) -> dict[str, str | bool]:
    return {
        SETTING_DEVELOPER_URL: get_setting(session, SETTING_DEVELOPER_URL, settings.developer_url),
        SETTING_DAILY_POST_TIME: get_setting(session, SETTING_DAILY_POST_TIME, settings.daily_post_time),
        SETTING_DAILY_VIDEO_TIME: get_setting(session, SETTING_DAILY_VIDEO_TIME, settings.daily_video_time),
        SETTING_TIMEZONE: get_setting(session, SETTING_TIMEZONE, settings.timezone),
        SETTING_AUTO_PUBLISH: bool_from_setting(
            get_setting(session, SETTING_AUTO_PUBLISH, str(settings.auto_publish_after_qc))
        ),
        SETTING_REQUIRE_IMAGE: bool_from_setting(
            get_setting(session, SETTING_REQUIRE_IMAGE, str(settings.require_image_asset))
        ),
        SETTING_POSTS_PER_DAY: get_setting(session, SETTING_POSTS_PER_DAY, "3"),
        SETTING_IMAGE_PROVIDER: get_setting(session, SETTING_IMAGE_PROVIDER, settings.creative_image_provider),
        SETTING_GEMINI_MODEL: get_setting(session, SETTING_GEMINI_MODEL, settings.gemini_image_model),
        SETTING_GROQ_MODEL: get_setting(session, SETTING_GROQ_MODEL, settings.groq_model),
    }
