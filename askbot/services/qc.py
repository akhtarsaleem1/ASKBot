from __future__ import annotations

from dataclasses import dataclass

from sqlmodel import Session, select

from askbot.models import GeneratedPost


PLATFORM_LIMITS = {
    "twitter": 280,
    "x": 280,
    "threads": 500,
    "linkedin": 3000,
    "facebook": 63206,
    "instagram": 2200,
    "mastodon": 500,
    "bluesky": 300,
    "generic": 2200,
}


@dataclass
class QCResult:
    approved: bool
    score: int
    reasons: list[str]


class QualityControl:
    def check(
        self,
        *,
        session: Session,
        run_key: str,
        platform: str,
        text: str,
        app_link: str,
        require_image: bool,
        image_url: str = "",
    ) -> QCResult:
        reasons: list[str] = []
        normalized_platform = platform.lower()
        limit = PLATFORM_LIMITS.get(normalized_platform, PLATFORM_LIMITS["generic"])

        if app_link not in text:
            reasons.append("The post is missing the Play Store app link.")
        if len(text) > limit:
            reasons.append(f"The post is {len(text)} characters, above the {limit} limit.")
        if require_image and not image_url:
            reasons.append("The promo image is required but no public image URL is available.")
        if self._is_duplicate(session, run_key, platform, text):
            reasons.append("The post text duplicates an existing generated post.")
        if any(term in text.lower() for term in ["guaranteed downloads", "guaranteed income", "fake reviews"]):
            reasons.append("The copy contains a risky or unsupported claim.")

        score = max(0, 100 - len(reasons) * 25)
        return QCResult(approved=not reasons, score=score, reasons=reasons)

    @staticmethod
    def _is_duplicate(session: Session, run_key: str, platform: str, text: str) -> bool:
        existing = session.exec(
            select(GeneratedPost).where(
                GeneratedPost.platform == platform,
                GeneratedPost.run_key != run_key,
            )
        ).all()
        normalized = " ".join(text.lower().split())
        return any(" ".join(post.text.lower().split()) == normalized for post in existing)
