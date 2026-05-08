from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Session, select

from askbot.models import AppRecord, PromotionRun


def select_next_apps(session: Session, run_key: str, limit: int = 1) -> list[AppRecord]:
    existing_run = session.exec(
        select(PromotionRun).where(PromotionRun.run_key == run_key)
    ).first()
    if existing_run and existing_run.status in {"queued", "completed", "blocked"}:
        return []

    apps = session.exec(select(AppRecord).where(AppRecord.enabled == True)).all()  # noqa: E712
    if not apps:
        return []

    def sort_key(app: AppRecord) -> tuple[datetime, int]:
        promoted_at = app.last_promoted_at or datetime(1970, 1, 1, tzinfo=timezone.utc)
        if promoted_at.tzinfo is None:
            promoted_at = promoted_at.replace(tzinfo=timezone.utc)
        return promoted_at, app.id or 0

    return sorted(apps, key=sort_key)[:limit]
