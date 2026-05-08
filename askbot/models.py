from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Setting(SQLModel, table=True):
    key: str = Field(primary_key=True)
    value: str
    updated_at: datetime = Field(default_factory=utc_now)


class AppRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    package_name: str = Field(index=True, unique=True)
    title: str
    app_link: str
    short_description: str = ""
    long_description: str = ""
    icon_url: str = ""
    screenshots_json: str = "[]"
    rating: str = ""
    installs: str = ""
    enabled: bool = True
    last_promoted_at: Optional[datetime] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class BufferChannel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    buffer_channel_id: str = Field(index=True, unique=True)
    buffer_account_label: str = Field(default="primary", index=True)
    name: str
    service: str
    enabled: bool = True
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class GeneratedPost(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    app_id: int = Field(index=True, foreign_key="apprecord.id")
    run_key: str = Field(index=True)
    platform: str = Field(index=True)
    text: str
    hashtags: str = ""
    image_path: str = ""
    image_url: str = ""
    video_path: str = ""
    video_url: str = ""
    ai_prompt_used: str = ""
    layout_used: str = ""
    qc_score: int = 0
    status: str = Field(default="draft", index=True)
    buffer_account_label: str = ""
    buffer_post_id: str = ""
    error: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class PostMetrics(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    post_id: int = Field(index=True, foreign_key="generatedpost.id")
    impressions: int = 0
    clicks: int = 0
    engagement_rate: float = 0.0
    fetched_at: datetime = Field(default_factory=utc_now)


class PromotionRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    run_key: str = Field(index=True, unique=True)
    app_id: Optional[int] = Field(default=None, foreign_key="apprecord.id")
    status: str = Field(default="started", index=True)
    message: str = ""
    started_at: datetime = Field(default_factory=utc_now)
    finished_at: Optional[datetime] = None


class RunLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    level: str = "info"
    message: str
    context: str = ""
    created_at: datetime = Field(default_factory=utc_now, index=True)
