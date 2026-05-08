import logging
import random
from datetime import datetime, timezone
from sqlmodel import Session, select
from askbot.models import GeneratedPost, PostMetrics

logger = logging.getLogger("askbot.analytics")

class AnalyticsFetcher:
    def sync_metrics(self, session: Session) -> None:
        """
        Simulate fetching analytics from Buffer API.
        We will assign mock metrics to any queued/sent post that doesn't have metrics yet.
        """
        logger.info("Starting analytics sync...")
        
        # In a real scenario we might query Buffer API for posts created in the last N days.
        # Here we just look for any 'queued' or 'ready' post without a PostMetrics entry.
        posts = session.exec(
            select(GeneratedPost)
            .where(GeneratedPost.status.in_(["queued", "ready"]))
        ).all()
        
        count = 0
        now = datetime.now(timezone.utc)
        
        for post in posts:
            existing = session.exec(
                select(PostMetrics).where(PostMetrics.post_id == post.id)
            ).first()
            
            if not existing:
                # Generate realistic mock metrics based on platform and layout
                base_impressions = random.randint(100, 500)
                
                # Cinematic/Bold Split layouts typically perform better visually
                if "cinematic" in (post.layout_used or "") or "bold_split" in (post.layout_used or ""):
                    base_impressions = int(base_impressions * 1.5)
                
                if post.platform == "twitter":
                    impressions = base_impressions * random.randint(1, 10)
                    clicks = int(impressions * random.uniform(0.01, 0.05))
                    likes = int(impressions * random.uniform(0.02, 0.08))
                    comments = int(likes * random.uniform(0.05, 0.2))
                    shares = int(likes * random.uniform(0.1, 0.3))
                elif post.platform == "linkedin":
                    impressions = base_impressions * random.randint(2, 5)
                    clicks = int(impressions * random.uniform(0.03, 0.08))
                    likes = int(impressions * random.uniform(0.01, 0.05))
                    comments = int(likes * random.uniform(0.1, 0.4))
                    shares = int(likes * random.uniform(0.05, 0.15))
                else: # instagram, facebook, etc
                    impressions = base_impressions * random.randint(5, 15)
                    clicks = int(impressions * random.uniform(0.005, 0.02))
                    likes = int(impressions * random.uniform(0.05, 0.15))
                    comments = int(likes * random.uniform(0.02, 0.1))
                    shares = int(likes * random.uniform(0.01, 0.05))
                
                engagement_rate = (clicks / impressions) if impressions > 0 else 0.0
                metrics = PostMetrics(
                    post_id=post.id,
                    impressions=impressions,
                    clicks=clicks,
                    engagement_rate=engagement_rate,
                    fetched_at=now
                )
                session.add(metrics)
                count += 1
                
        session.commit()
        logger.info(f"Analytics sync complete. Generated mock metrics for {count} posts.")
