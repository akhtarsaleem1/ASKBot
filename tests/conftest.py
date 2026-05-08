from __future__ import annotations

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from askbot.config import Settings


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture()
def test_settings() -> Settings:
    return Settings(
        host="127.0.0.1",
        port=8788,
        database_url="sqlite:///data/test.db",
        developer_url="https://play.google.com/store/apps/dev?id=6396415332355171917",
        daily_post_time="00:00",
        daily_video_time="18:00",
        timezone="Asia/Karachi",
        auto_publish_after_qc=True,
        require_image_asset=True,
        groq_api_key=None,
        groq_model="llama-3.3-70b-versatile",
        buffer_api_key="buffer-test-key",
        buffer_api_keys={"primary": "buffer-test-key", "account2": "buffer-test-key-2"},
        buffer_default_mode="customScheduled",
        creative_image_provider="local",
        creative_video_provider="none",
        creative_image_daily_limit=3,
        creative_video_daily_limit=2,
        gemini_api_key=None,
        gemini_image_model="gemini-2.5-flash-image",
        huggingface_api_key=None,
        huggingface_api_keys=[],
        huggingface_image_model="",
        huggingface_video_model="",
        zsky_video_api_url="https://zsky.ai/api/v1/video/generate",
        pollinations_api_key=None,
        pollinations_video_model="seedance",
        cloudinary_cloud_name="demo",
        cloudinary_api_key="key",
        cloudinary_api_secret="secret",
    )
