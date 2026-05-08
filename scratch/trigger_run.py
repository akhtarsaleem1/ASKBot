import os
import logging
from datetime import date
from askbot.config import get_settings
from askbot.database import init_db, create_session
from askbot.services.promotion import PromotionService

logging.basicConfig(level=logging.INFO)
init_db()
settings = get_settings()
service = PromotionService(settings)

print("=== Testing NEW image generator with LLM prompts + 5 layouts ===")
with create_session(settings) as session:
    test_date = date(2026, 5, 24)
    result = service.run_daily(session, target_date=test_date, media_focus="image", dry_run=False)
    print(f"\nResult: [{result.status}] {result.message}")
