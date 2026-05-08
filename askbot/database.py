from __future__ import annotations

from pathlib import Path
from typing import Iterator

from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine

from askbot.config import PROJECT_ROOT, Settings, get_settings


def normalize_sqlite_url(database_url: str) -> str:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return database_url
    raw_path = database_url.removeprefix(prefix)
    db_path = Path(raw_path)
    if not db_path.is_absolute():
        db_path = PROJECT_ROOT / db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path.as_posix()}"


settings = get_settings()
engine = create_engine(
    normalize_sqlite_url(settings.database_url),
    connect_args={"check_same_thread": False},
)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    ensure_sqlite_schema(engine)


def ensure_sqlite_schema(active_engine) -> None:
    inspector = inspect(active_engine)
    table_names = set(inspector.get_table_names())
    with active_engine.begin() as connection:
        if "bufferchannel" in table_names:
            columns = {column["name"] for column in inspector.get_columns("bufferchannel")}
            if "buffer_account_label" not in columns:
                connection.execute(
                    text("ALTER TABLE bufferchannel ADD COLUMN buffer_account_label VARCHAR NOT NULL DEFAULT 'primary'")
                )
        if "generatedpost" in table_names:
            columns = {column["name"] for column in inspector.get_columns("generatedpost")}
            if "buffer_account_label" not in columns:
                connection.execute(
                    text("ALTER TABLE generatedpost ADD COLUMN buffer_account_label VARCHAR NOT NULL DEFAULT ''")
                )
            if "video_path" not in columns:
                connection.execute(text("ALTER TABLE generatedpost ADD COLUMN video_path VARCHAR NOT NULL DEFAULT ''"))
            if "video_url" not in columns:
                connection.execute(text("ALTER TABLE generatedpost ADD COLUMN video_url VARCHAR NOT NULL DEFAULT ''"))


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


def create_session(custom_settings: Settings | None = None) -> Session:
    if custom_settings is None:
        return Session(engine)
    custom_engine = create_engine(
        normalize_sqlite_url(custom_settings.database_url),
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(custom_engine)
    ensure_sqlite_schema(custom_engine)
    return Session(custom_engine)
