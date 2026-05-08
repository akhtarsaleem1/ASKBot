from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import Session

from askbot.config import Settings
from askbot.database import engine
from askbot.services.promotion import PromotionService
from askbot.services.settings_store import (
    SETTING_DAILY_POST_TIME,
    SETTING_TIMEZONE,
    runtime_config,
)


def _parse_time(time_str: str) -> tuple[int, int]:
    try:
        if not time_str or ":" not in time_str:
            return 7, 0 # Default to 7 AM
        hour, minute = [int(part) for part in time_str.split(":", 1)]
        return hour, minute
    except (ValueError, AttributeError):
        return 7, 0


def refresh_scheduler(scheduler: BackgroundScheduler, settings: Settings, session: Session) -> None:
    """Updates the scheduler jobs based on the latest database settings."""
    cfg = runtime_config(session, settings)
    image_time = str(cfg[SETTING_DAILY_POST_TIME])
    timezone = str(cfg[SETTING_TIMEZONE])

    image_hour, image_minute = _parse_time(image_time)
    
    # Update Daily Promotion Job with explicit timezone
    trigger = CronTrigger(
        hour=image_hour, 
        minute=image_minute, 
        timezone=timezone
    )
    
    scheduler.add_job(
        image_job_wrapper,
        trigger=trigger,
        id="daily_image_promotion",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        args=[settings]
    )
    
    import logging
    logging.info(f"Scheduler refreshed: Daily promotion set to {image_hour:02d}:{image_minute:02d} (Timezone: {timezone})")
    
    # Check when the next run is
    job = scheduler.get_job("daily_image_promotion")
    if job:
        logging.info(f"Next scheduled run for daily promotion: {job.next_run_time}")


def image_job_wrapper(settings: Settings) -> None:
    import logging
    logging.info("Scheduled daily promotion job starting...")
    with Session(engine) as session:
        PromotionService(settings).run_daily(session, media_focus="image")


def start_scheduler(settings: Settings) -> BackgroundScheduler:
    # Get initial settings
    with Session(engine) as session:
        cfg = runtime_config(session, settings)
        image_time = str(cfg[SETTING_DAILY_POST_TIME])
        timezone = str(cfg[SETTING_TIMEZONE])

    scheduler = BackgroundScheduler(timezone=timezone)

    image_hour, image_minute = _parse_time(image_time)
    
    # Initial job add
    trigger = CronTrigger(hour=image_hour, minute=image_minute, timezone=timezone)
    scheduler.add_job(
        image_job_wrapper,
        trigger=trigger,
        id="daily_image_promotion",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        args=[settings]
    )

    def analytics_job() -> None:
        from askbot.services.analytics import AnalyticsFetcher
        import logging
        logging.info("Scheduled analytics sync job starting...")
        with Session(engine) as session:
            AnalyticsFetcher().sync_metrics(session)

    scheduler.add_job(
        analytics_job,
        "cron",
        hour=23,
        minute=50,
        id="daily_analytics_sync",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    scheduler.start()
    return scheduler
