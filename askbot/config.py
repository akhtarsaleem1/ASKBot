from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ASSET_DIR = DATA_DIR / "assets"


def load_dotenv(path: Path | None = None) -> None:
    env_path = path or PROJECT_ROOT / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def parse_buffer_api_keys() -> dict[str, str]:
    keys: dict[str, str] = {}

    primary = os.getenv("BUFFER_API_KEY")
    if primary:
        keys["primary"] = primary.strip()

    combined = os.getenv("BUFFER_API_KEYS", "")
    for index, part in enumerate(combined.split(","), start=1):
        item = part.strip()
        if not item:
            continue
        if ":" in item:
            label, key = item.split(":", 1)
            label = label.strip() or f"account{index}"
            key = key.strip()
        else:
            label = f"account{index}"
            key = item
        if key:
            keys[label] = key

    for index in range(2, 11):
        key = os.getenv(f"BUFFER_API_KEY_{index}")
        if key:
            keys[f"account{index}"] = key.strip()

    return keys


def parse_huggingface_api_keys() -> list[str]:
    keys: list[str] = []
    primary = os.getenv("HUGGINGFACE_API_KEY")
    if primary:
        keys.append(primary.strip())

    for index in range(2, 6):
        key = os.getenv(f"HUGGINGFACE_API_KEY_{index}")
        if key:
            keys.append(key.strip())
    return keys


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    database_url: str
    developer_url: str
    daily_post_time: str
    daily_video_time: str
    timezone: str
    auto_publish_after_qc: bool
    require_image_asset: bool
    groq_api_key: str | None
    groq_model: str
    buffer_api_key: str | None
    buffer_api_keys: dict[str, str]
    buffer_default_mode: str
    creative_image_provider: str
    creative_video_provider: str
    creative_image_daily_limit: int
    creative_video_daily_limit: int
    gemini_api_key: str | None
    gemini_image_model: str
    huggingface_api_key: str | None
    huggingface_api_keys: list[str]
    huggingface_image_model: str
    huggingface_video_model: str
    zsky_video_api_url: str
    pollinations_api_key: str | None
    pollinations_video_model: str
    cloudinary_cloud_name: str | None
    cloudinary_api_key: str | None
    cloudinary_api_secret: str | None

    @property
    def buffer_configured(self) -> bool:
        return bool(self.buffer_api_keys)

    @property
    def cloudinary_configured(self) -> bool:
        return bool(
            self.cloudinary_cloud_name
            and self.cloudinary_api_key
            and self.cloudinary_api_secret
        )


def get_settings() -> Settings:
    load_dotenv()
    DATA_DIR.mkdir(exist_ok=True)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)

    return Settings(
        host=os.getenv("APP_HOST", "127.0.0.1"),
        port=int(os.getenv("APP_PORT", "8788")),
        database_url=os.getenv("DATABASE_URL", "sqlite:///data/askbot.db"),
        developer_url=os.getenv(
            "PLAY_DEVELOPER_URL",
            "https://play.google.com/store/apps/dev?id=6396415332355171917",
        ),
        daily_post_time=os.getenv("DAILY_POST_TIME", "00:00"),
        daily_video_time=os.getenv("DAILY_VIDEO_TIME", "18:00"),
        timezone=os.getenv("APP_TIMEZONE", "Asia/Karachi"),
        auto_publish_after_qc=env_bool("AUTO_PUBLISH_AFTER_QC", True),
        require_image_asset=env_bool("REQUIRE_IMAGE_ASSET", True),
        groq_api_key=os.getenv("GROQ_API_KEY") or None,
        groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        buffer_api_key=os.getenv("BUFFER_API_KEY") or None,
        buffer_api_keys=parse_buffer_api_keys(),
        buffer_default_mode=os.getenv("BUFFER_DEFAULT_MODE", "customScheduled"),
        creative_image_provider=os.getenv("CREATIVE_IMAGE_PROVIDER", "gemini"),
        creative_video_provider=os.getenv("CREATIVE_VIDEO_PROVIDER", "none"),
        creative_image_daily_limit=int(os.getenv("CREATIVE_IMAGE_DAILY_LIMIT", "3")),
        creative_video_daily_limit=int(os.getenv("CREATIVE_VIDEO_DAILY_LIMIT", "2")),
        gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
        gemini_image_model=os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image"),
        huggingface_api_key=os.getenv("HUGGINGFACE_API_KEY") or None,
        huggingface_api_keys=parse_huggingface_api_keys(),
        huggingface_image_model=os.getenv("HUGGINGFACE_IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell"),
        huggingface_video_model=os.getenv("HUGGINGFACE_VIDEO_MODEL", "THUDM/CogVideoX-5b"),
        zsky_video_api_url=os.getenv("ZSKY_VIDEO_API_URL", "https://zsky.ai/api/v1/video/generate"),
        pollinations_api_key=os.getenv("POLLINATIONS_API_KEY") or None,
        pollinations_video_model=os.getenv("POLLINATIONS_VIDEO_MODEL", "seedance"),
        cloudinary_cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME") or None,
        cloudinary_api_key=os.getenv("CLOUDINARY_API_KEY") or None,
        cloudinary_api_secret=os.getenv("CLOUDINARY_API_SECRET") or None,
    )
