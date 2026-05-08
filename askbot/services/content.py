from __future__ import annotations

import json
from dataclasses import dataclass

from askbot.config import Settings
from askbot.models import AppRecord
from askbot.services.qc import PLATFORM_LIMITS


PLATFORM_BY_SERVICE = {
    "twitter": "twitter",
    "x": "twitter",
    "linkedin": "linkedin",
    "facebook": "facebook",
    "instagram": "instagram",
    "threads": "threads",
    "mastodon": "mastodon",
    "bluesky": "bluesky",
    "youtube": "generic",
    "pinterest": "generic",
    "tiktok": "generic",
    "googlebusiness": "generic",
}


@dataclass
class GeneratedContent:
    posts: dict[str, str]
    headline: str
    subheadline: str
    cta: str
    selected_feature: str = ""
    hashtags: str = ""


class ContentGenerator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate(self, app: AppRecord, plan: dict[str, Any]) -> GeneratedContent:
        if self.settings.groq_api_key:
            try:
                generated = self._generate_with_groq(app, plan)
                if generated:
                    return generated
            except Exception as e:
                import logging
                logging.error(f"Content generation failed: {e}")
        return self._fallback(app, plan)

    def _generate_with_groq(self, app: AppRecord, plan: dict[str, Any]) -> GeneratedContent | None:
        from groq import Groq

        client = Groq(api_key=self.settings.groq_api_key, timeout=30.0)
        prompt = {
            "task": "Create daily social media promotion content for an Android app based on the provided marketing plan.",
            "rules": [
                "Use English.",
                "Do not invent rankings, awards, downloads, or ratings.",
                "Every post must include the exact Play Store link.",
                "Keep the tone clear, useful, and non-spammy.",
                "Align with the campaign_theme.",
                "Return JSON only.",
            ],
            "app": {
                "title": app.title,
                "short_description": app.short_description,
                "full_description": app.long_description or app.short_description,
                "rating": app.rating,
                "installs": app.installs,
                "play_store_link": app.app_link,
            },
            "marketing_plan": plan,
            "schema": {
                "headline": "short image headline (max 5 words, engaging)",
                "subheadline": "short benefit line (max 10 words)",
                "cta": "short call to action (max 4 words)",
                "hashtags": "Space-separated hashtags for generic use (e.g. '#App #Tech')",
                "posts": {
                    "linkedin": "professional post focusing on value/productivity",
                    "twitter": "short punchy post, 1-2 emojis, include relevant hashtags",
                    "facebook": "conversational post, engaging question",
                    "threads": "casual, relatable post",
                    "instagram": "visual-focused caption, high emoji use, 10-15 hashtags at end",
                    "generic": "standard promotional text",
                },
            },
        }

        response = client.chat.completions.create(
            model=self.settings.groq_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert social media copywriter. You generate concise promotional copy that exactly matches the provided marketing plan. Return valid JSON.",
                },
                {"role": "user", "content": json.dumps(prompt)},
            ],
            response_format={"type": "json_object"},
            temperature=0.8,
            max_tokens=2000,
        )
        raw = response.choices[0].message.content or "{}"
        parsed = json.loads(raw)
        posts = parsed.get("posts", {})
        if not isinstance(posts, dict):
            return None

        sanitized = {
            platform: self._ensure_link_and_limit(str(text), app.app_link, platform)
            for platform, text in posts.items()
        }
        for platform in ("linkedin", "twitter", "facebook", "threads", "instagram", "generic"):
            sanitized.setdefault(platform, self._fallback_post(app, platform))

        suggested_hashtags = " ".join(plan.get("suggested_hashtags", []))
        return GeneratedContent(
            posts=sanitized,
            headline=str(parsed.get("headline") or plan.get("campaign_theme") or app.title)[:80],
            subheadline=str(parsed.get("subheadline") or app.short_description or "Try it on Google Play")[:120],
            cta=str(parsed.get("cta") or "Download on Google Play")[:40],
            selected_feature=str(plan.get("selected_feature") or app.short_description or "Key Feature")[:60],
            hashtags=str(parsed.get("hashtags") or suggested_hashtags)[:200],
        )

    def _fallback(self, app: AppRecord, plan: dict[str, Any]) -> GeneratedContent:
        suggested_hashtags = " ".join(plan.get("suggested_hashtags", []))
        return GeneratedContent(
            posts={
                platform: self._fallback_post(app, platform)
                for platform in ("linkedin", "twitter", "facebook", "threads", "instagram", "generic")
            },
            headline=app.title[:80],
            subheadline=(app.short_description or "A useful Android app available on Google Play")[:120],
            cta="Get it on Google Play",
            selected_feature=(app.short_description or "Key Feature")[:60],
            hashtags=suggested_hashtags,
        )

    def _fallback_post(self, app: AppRecord, platform: str) -> str:
        benefit = app.short_description.strip() or "Try this Android app from my Play Store portfolio."
        if platform == "twitter":
            text = f"Today I am featuring {app.title}: {benefit}\n\nGet it on Google Play: {app.app_link}"
        elif platform == "linkedin":
            text = (
                f"App spotlight: {app.title}\n\n"
                f"{benefit}\n\n"
                f"If it looks useful for your workflow, you can check it out on Google Play:\n{app.app_link}"
            )
        else:
            text = f"Today's app spotlight is {app.title}.\n\n{benefit}\n\nDownload it on Google Play: {app.app_link}"
        return self._ensure_link_and_limit(text, app.app_link, platform)

    @staticmethod
    def _ensure_link_and_limit(text: str, app_link: str, platform: str) -> str:
        if app_link not in text:
            text = f"{text.rstrip()}\n\n{app_link}"

        limit = PLATFORM_LIMITS.get(platform, PLATFORM_LIMITS["generic"])
        if len(text) <= limit:
            return text

        link_suffix = f"\n\n{app_link}"
        available = max(30, limit - len(link_suffix))
        trimmed = text.replace(app_link, "").strip()[: available - 3].rstrip()
        return f"{trimmed}...{link_suffix}"

