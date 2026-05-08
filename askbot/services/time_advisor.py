import json
import logging
from datetime import datetime, timezone, date, time
from typing import Any

from askbot.config import Settings
from askbot.models import AppRecord

class AITimeAdvisor:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def get_optimal_posting_times(self, app: AppRecord, plan: dict[str, Any], current_date: date) -> dict[str, datetime]:
        """
        Ask the AI for the optimal posting times for today for various platforms.
        Returns a dict mapping platform ('twitter', 'linkedin', 'instagram', 'facebook') to a datetime object.
        """
        if not self.settings.groq_api_key:
            return self._fallback_times(current_date)

        try:
            from groq import Groq
            client = Groq(api_key=self.settings.groq_api_key, timeout=30.0)

            system = (
                "You are an expert social media strategist. "
                "Your task is to determine the optimal posting times TODAY for a specific mobile app.\n\n"
                "RULES:\n"
                "- Consider the target audience and the day of the week.\n"
                "- Return ONLY a JSON object with keys: 'twitter', 'linkedin', 'instagram', 'facebook'.\n"
                "- The value for each key MUST be a string in 'HH:MM' 24-hour format (e.g., '14:30', '09:15').\n"
                "- Stagger the times so they don't all post at the exact same minute.\n"
                "- Keep the times within reasonable waking hours (08:00 to 22:00).\n"
            )

            user_msg = (
                f"App Title: {app.title}\n"
                f"Target Audience: {plan.get('target_audience', 'General users')}\n"
                f"Day of Week: {current_date.strftime('%A')}\n\n"
                "Determine the optimal posting time for each platform."
            )

            response = client.chat.completions.create(
                model=self.settings.groq_model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_msg},
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=200,
            )

            raw = response.choices[0].message.content or "{}"
            parsed = json.loads(raw)
            logging.info(f"AI suggested post times for {app.title}: {parsed}")
            
            return self._parse_ai_times(parsed, current_date)

        except Exception as e:
            logging.error(f"Time Advisor failed: {e}")
            return self._fallback_times(current_date)
            
    def _parse_ai_times(self, ai_times: dict[str, str], current_date: date) -> dict[str, datetime]:
        result = {}
        # Default fallback times
        defaults = {
            "twitter": "09:30",
            "linkedin": "10:15",
            "instagram": "17:45",
            "facebook": "13:00"
        }
        
        for platform in ["twitter", "linkedin", "instagram", "facebook"]:
            time_str = ai_times.get(platform, defaults[platform])
            try:
                hour, minute = map(int, time_str.split(':'))
            except (ValueError, TypeError):
                hour, minute = map(int, defaults[platform].split(':'))
                
            # Create a timezone-aware datetime for today
            # We assume the AI returns times in the local timezone configured in settings
            try:
                import zoneinfo
                tz = zoneinfo.ZoneInfo(self.settings.timezone)
            except Exception:
                tz = timezone.utc
                
            dt = datetime.combine(current_date, time(hour, minute), tzinfo=tz)
            
            # If the generated time is in the past (e.g. script runs at 10 AM, AI picks 9 AM)
            # just bump it to current time + some minutes, or tomorrow.
            # But since this is a daily planner, we'll assume it runs early enough.
            # If not, add a small buffer:
            now = datetime.now(tz)
            if dt < now:
                # If we missed the slot, schedule for 15 mins from now
                # Or we could schedule for tomorrow, but let's do today
                logging.warning(f"AI suggested {platform} time {time_str} is in the past. Scheduling for soon.")
                from datetime import timedelta
                dt = now + timedelta(minutes=15)
                
            result[platform] = dt
            
        return result

    def _fallback_times(self, current_date: date) -> dict[str, datetime]:
        return self._parse_ai_times({}, current_date)
