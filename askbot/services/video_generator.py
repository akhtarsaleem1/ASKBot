"""Video generation service stub - disabled by default."""
from __future__ import annotations

import logging
from pathlib import Path

from askbot.config import Settings, get_settings
from askbot.models import AppRecord
from askbot.services.content import GeneratedContent


class PromoVideoGenerator:
    """Video generation service - currently disabled as no free APIs work reliably."""
    
    def __init__(self, output_dir: Path | None = None, settings: Settings | None = None) -> None:
        self.output_dir = output_dir or Path("data/assets")
        self.settings = settings or get_settings()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create(self, app: AppRecord, content: GeneratedContent, run_key: str, selected_feature: str = "", image_url: str = "") -> Path | None:
        """Video generation is disabled by default."""
        logging.info(f"Video generation disabled for {app.title}")
        return None
