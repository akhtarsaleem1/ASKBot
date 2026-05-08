from __future__ import annotations

import base64
import hashlib
import json
import logging
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image
from huggingface_hub import InferenceClient

from askbot.config import ASSET_DIR, Settings, get_settings
from askbot.models import AppRecord
from askbot.services.content import GeneratedContent


class PromoImageGenerator:
    def __init__(self, output_dir: Path | None = None, settings: Settings | None = None) -> None:
        self.output_dir = output_dir or ASSET_DIR
        self.settings = settings or get_settings()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create(
        self, 
        app: AppRecord, 
        content: GeneratedContent, 
        run_key: str, 
        selected_feature: str = "",
        provider_override: str | None = None,
        model_override: str | None = None
    ) -> tuple[Path, str, str]:
        """Generate a professional promotional image for the app.

        Builds a feature-specific prompt from the app's Play Store data
        (title, description, icon URL, screenshots) and passes it to the
        configured AI image generator (Gemini, HuggingFace, etc.).
        Returns the raw generated image with no text overlays or layouts.
        """
        width = height = 1080

        # Build a feature-specific professional prompt from Play Store data
        prompt = self._build_prompt(app, selected_feature or content.selected_feature or app.short_description)
        logging.info(f"Image prompt for {app.title}: {prompt[:120]}...")

        # Generate the hero image
        hero = self._generate_image(prompt, width, height, provider_override, model_override)

        if hero is None:
            logging.error(f"Image generation failed for {app.title}")
            raise RuntimeError(f"AI image generation failed for {app.title}. Check logs for details.")

        # Overlay app icon if available
        icon = self._download_icon(app.icon_url)
        if icon:
            hero = self._overlay_icon(hero, icon)

        # Save raw image (no layouts, overlays, or branding)
        digest = hashlib.sha1(f"{run_key}:{app.package_name}".encode()).hexdigest()[:12]
        path = self.output_dir / f"{run_key}-{app.package_name}-{digest}.png"
        hero.save(path, format="PNG", optimize=True)
        logging.info(f"Saved image: {path}")

        provider = provider_override or self.settings.creative_image_provider
        return path, prompt, provider

    def _build_prompt(self, app: AppRecord, selected_feature: str) -> str:
        """Build a professional, feature-specific image generation prompt
        using the app's Play Store metadata (title, description, icon, screenshots).
        """
        title = app.title or "Mobile App"
        desc = app.short_description or "a useful mobile application"
        feature = selected_feature or desc

        # Pull visual references from Play Store assets
        icon_ref = f"Inspired by the app's icon style from {app.icon_url}" if app.icon_url else ""
        screenshots = []
        try:
            screenshots = json.loads(app.screenshots_json) if app.screenshots_json else []
        except Exception:
            pass
        screenshot_ref = f"Visual style references from {len(screenshots)} Play Store screenshots" if screenshots else ""

        parts = [
            f"Professional promotional image for the mobile app '{title}'.",
            f"Feature focus: {feature}.",
            f"App identity: {desc}.",
        ]
        if icon_ref:
            parts.append(icon_ref)
        if screenshot_ref:
            parts.append(screenshot_ref)
        parts.extend([
            "Visual style: High-end, premium 3D marketing render. Clean, minimalist aesthetic.",
            "CRITICAL: No text, no letters, no characters, no alphabet, no fake words.",
            "CRITICAL: Do not show a phone screen, do not show a user interface, no buttons.",
            "Instead, focus on a beautiful, artistic, and metaphorical representation of the feature.",
            "Vibrant professional lighting, depth of field, 8k resolution, cinematic composition.",
        ])
        return " ".join(parts)

    # ── Image Generation ────────────────────────────────────────────

    def _generate_image(self, prompt: str, width: int, height: int, provider_override: str | None = None, model_override: str | None = None) -> Image.Image | None:
        provider = (provider_override or self.settings.creative_image_provider).lower()

        if provider == "huggingface" or self.settings.huggingface_api_keys:
            image = self._hf_generate(prompt, width, height, model_override)
            if image:
                return image

        if self.settings.gemini_api_key:
            image = self._gemini_generate(prompt, width, height, model_override)
            if image:
                return image

        if self.settings.pollinations_api_key:
            image = self._pollinations_generate(prompt, width, height)
            if image:
                return image

        return None

    def _hf_generate(self, prompt: str, width: int, height: int, model_override: str | None = None) -> Image.Image | None:
        if not self.settings.huggingface_api_keys:
            return None

        model = model_override or self.settings.huggingface_image_model
        for i, key in enumerate(self.settings.huggingface_api_keys):
            try:
                logging.info(f"HF key {i+1}/{len(self.settings.huggingface_api_keys)}")
                client = InferenceClient(api_key=key)
                img = client.text_to_image(prompt, model=model)
                logging.info(f"Hugging Face image generated successfully using {model}")
                return self._cover(img.convert("RGB"), width, height)
            except Exception as e:
                logging.error(f"HF key {i+1} error: {e}")
                if "402" in str(e) or "429" in str(e):
                    continue
                return None
        return None

    def _gemini_generate(self, prompt: str, width: int, height: int, model_override: str | None = None) -> Image.Image | None:
        model = model_override or self.settings.gemini_image_model
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.settings.gemini_api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["IMAGE"], "temperature": 0.9},
        }
        try:
            resp = requests.post(url, json=payload, timeout=120, headers={"Content-Type": "application/json"})
            resp.raise_for_status()
            for part in resp.json().get("candidates", [{}])[0].get("content", {}).get("parts", []):
                data = part.get("inlineData", {})
                if data.get("data") and "image" in data.get("mimeType", ""):
                    logging.info(f"Gemini image generated successfully using {model}")
                    return self._cover(Image.open(BytesIO(base64.b64decode(data["data"]))).convert("RGB"), width, height)
        except Exception as e:
            logging.error(f"Gemini error: {e}")
        return None

    def _pollinations_generate(self, prompt: str, width: int, height: int) -> Image.Image | None:
        if not self.settings.pollinations_api_key:
            return None
        encoded_prompt = requests.utils.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&seed=42&nologo=true"
        try:
            logging.info(f"Pollinations image request: {url[:120]}...")
            resp = requests.get(url, timeout=120, headers={"Authorization": f"Bearer {self.settings.pollinations_api_key}"})
            resp.raise_for_status()
            image = Image.open(BytesIO(resp.content)).convert("RGB")
            logging.info("Pollinations image generated successfully")
            return self._cover(image, width, height)
        except Exception as e:
            logging.error(f"Pollinations error: {e}")
        return None

    # ── Utilities ───────────────────────────────────────────────────

    @staticmethod
    def _cover(image: Image.Image, width: int, height: int) -> Image.Image:
        scale = max(width / image.width, height / image.height)
        resized = image.resize((int(image.width * scale), int(image.height * scale)), Image.Resampling.LANCZOS)
        left = (resized.width - width) // 2
        top = (resized.height - height) // 2
        return resized.crop((left, top, left + width, top + height))

    def _overlay_icon(self, background: Image.Image, icon: Image.Image) -> Image.Image:
        """Overlay the app icon onto the background image with a professional shadow/border."""
        canvas = background.copy()
        
        # Calculate icon size (12% of background width)
        size = int(canvas.width * 0.12)
        icon = icon.resize((size, size), Image.Resampling.LANCZOS)
        
        # Padding from corner
        padding = 50
        
        # Position: Top Left (standard for branding)
        pos = (padding, padding)
        
        # Add a subtle background plate for the icon to make it pop if the hero image is busy
        from PIL import ImageDraw
        draw = ImageDraw.Draw(canvas, "RGBA")
        
        # Draw a rounded white background with transparency
        rect_padding = 10
        rect = [pos[0] - rect_padding, pos[1] - rect_padding, pos[0] + size + rect_padding, pos[1] + size + rect_padding]
        draw.rounded_rectangle(rect, radius=20, fill=(255, 255, 255, 180))
        
        if icon.mode == 'RGBA':
            canvas.paste(icon, pos, icon)
        else:
            canvas.paste(icon, pos)
            
        return canvas

    @staticmethod
    def _download_icon(icon_url: str) -> Image.Image | None:
        if not icon_url:
            return None
        try:
            resp = requests.get(icon_url, timeout=15, headers={"User-Agent": "ASKBot/0.1"})
            resp.raise_for_status()
            icon = Image.open(BytesIO(resp.content)).convert("RGBA")
            icon.thumbnail((160, 160))
            canvas = Image.new("RGBA", (160, 160), (255, 255, 255, 0))
            canvas.alpha_composite(icon, ((160 - icon.width) // 2, (160 - icon.height) // 2))
            return canvas
        except Exception:
            return None
