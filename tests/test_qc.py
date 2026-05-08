from __future__ import annotations

from askbot.models import AppRecord, GeneratedPost
from askbot.services.qc import QualityControl


def test_qc_requires_play_store_link(session):
    qc = QualityControl().check(
        session=session,
        run_key="2026-05-07",
        platform="twitter",
        text="Try my app today",
        app_link="https://play.google.com/store/apps/details?id=com.example.app",
        require_image=False,
    )

    assert not qc.approved
    assert "missing the Play Store app link" in qc.reasons[0]


def test_qc_rejects_over_platform_limit(session):
    link = "https://play.google.com/store/apps/details?id=com.example.app"
    text = f"{'x' * 300}\n{link}"

    qc = QualityControl().check(
        session=session,
        run_key="2026-05-07",
        platform="twitter",
        text=text,
        app_link=link,
        require_image=False,
    )

    assert not qc.approved
    assert any("above the 280 limit" in reason for reason in qc.reasons)


def test_qc_duplicate_check_ignores_same_run(session):
    app = AppRecord(
        package_name="com.example.app",
        title="Example",
        app_link="https://play.google.com/store/apps/details?id=com.example.app",
    )
    session.add(app)
    session.commit()
    session.refresh(app)
    link = app.app_link
    text = f"Try Example\n\n{link}"
    session.add(
        GeneratedPost(
            app_id=app.id,
            run_key="2026-05-07",
            platform="linkedin",
            text=text,
            status="queued",
        )
    )
    session.commit()

    qc = QualityControl().check(
        session=session,
        run_key="2026-05-07",
        platform="linkedin",
        text=text,
        app_link=link,
        require_image=False,
    )

    assert qc.approved

