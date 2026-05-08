from __future__ import annotations

from datetime import datetime, timedelta, timezone

from askbot.models import AppRecord
from askbot.services.rotation import select_next_apps


def test_rotation_picks_never_promoted_app_first(session):
    old = AppRecord(
        package_name="com.example.old",
        title="Old App",
        app_link="https://play.google.com/store/apps/details?id=com.example.old",
        last_promoted_at=datetime.now(timezone.utc) - timedelta(days=3),
    )
    fresh = AppRecord(
        package_name="com.example.fresh",
        title="Fresh App",
        app_link="https://play.google.com/store/apps/details?id=com.example.fresh",
    )
    session.add(old)
    session.add(fresh)
    session.commit()

    selected = select_next_apps(session, "2026-05-07")

    assert selected is not None
    assert len(selected) == 1
    assert selected[0].package_name == "com.example.fresh"


def test_rotation_ignores_disabled_apps(session):
    disabled = AppRecord(
        package_name="com.example.disabled",
        title="Disabled App",
        app_link="https://play.google.com/store/apps/details?id=com.example.disabled",
        enabled=False,
    )
    enabled = AppRecord(
        package_name="com.example.enabled",
        title="Enabled App",
        app_link="https://play.google.com/store/apps/details?id=com.example.enabled",
    )
    session.add(disabled)
    session.add(enabled)
    session.commit()

    selected = select_next_apps(session, "2026-05-07")

    assert selected is not None
    assert len(selected) == 1
    assert selected[0].package_name == "com.example.enabled"

