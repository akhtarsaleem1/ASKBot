from __future__ import annotations

import json
import logging
from typing import Any

from groq import Groq
from sqlmodel import Session

from askbot.config import Settings
from askbot.models import AppRecord

class MarketingPlanner:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = Groq(api_key=settings.groq_api_key, timeout=30.0) if settings.groq_api_key else None

    def create_campaign_plan(self, app: AppRecord) -> dict[str, Any]:
        """
        Uses LLM to act as a Marketing Director and plan the entire campaign for the app.
        Returns a JSON object with the plan.
        """
        if not self.client:
            logging.warning("Groq API key not configured, returning fallback marketing plan.")
            return self._fallback_plan(app)

        system_prompt = (
            "You are a world-class Marketing Director at a top mobile app agency. "
            "Your job is to deeply analyze an app's full description, identify ONE standout feature or benefit, "
            "and create a razor-sharp daily marketing campaign plan around it. "
            "Think deeply about the target audience, the core benefit, and how to visually represent it. "
            "Output MUST be raw JSON with the following schema, no markdown blocks, no other text:\n"
            "{\n"
            '  "campaign_theme": "A short, catchy theme for this post",\n'
            '  "selected_feature": "The single most compelling feature or benefit to highlight today — be specific and concrete",\n'
            '  "target_audience": "Who this post is aimed at — be specific (e.g. content creators, students, professionals)",\n'
            '  "visual_concept": "A detailed, creative description of the hero image (no text in image, no phones, abstract/metaphorical)",\n'
            '  "color_palette_recommendation": "Suggest 2-3 hex colors that fit the theme",\n'
            '  "suggested_hashtags": ["#tag1", "#tag2", "#tag3"]\n'
            "}"
        )

        description = app.long_description or app.short_description
        user_prompt = (
            f"App Name: {app.title}\n"
            f"App Description (Full): {description[:1500]}\n"
            f"Installs: {app.installs}\n"
            f"Rating: {app.rating}\n\n"
            "Analyze the full description above. Pick ONE specific feature or benefit that stands out most. "
            "Create today's marketing plan focused exclusively on that feature. Make it completely different from generic ads. Be creative!"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.settings.groq_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.8,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if content:
                plan = json.loads(content)
                logging.info(f"Generated AI marketing plan for {app.title}: {plan.get('campaign_theme')}")
                return plan
        except Exception as e:
            logging.error(f"Failed to generate marketing plan: {e}")

        return self._fallback_plan(app)

    def _fallback_plan(self, app: AppRecord) -> dict[str, Any]:
        description = app.long_description or app.short_description
        # Extract a likely feature sentence from the description
        sentences = [s.strip() for s in (description or "").split(".") if len(s.strip()) > 10]
        selected_feature = sentences[0] if sentences else (app.short_description or "Amazing Features")
        return {
            "campaign_theme": f"Discover {app.title}",
            "selected_feature": selected_feature[:200],
            "target_audience": "Everyone",
            "visual_concept": "Abstract flowing shapes, clean minimal background",
            "color_palette_recommendation": ["#0f172a", "#14b8a6"],
            "suggested_hashtags": ["#MobileApp", "#Tech", "#Innovation"]
        }
