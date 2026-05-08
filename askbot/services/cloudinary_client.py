from __future__ import annotations

from pathlib import Path

from askbot.config import Settings


class CloudinaryMediaClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def configured(self) -> bool:
        return self.settings.cloudinary_configured

    def upload_image(self, image_path: Path) -> str:
        if not self.configured:
            raise RuntimeError("Cloudinary is not configured.")

        import cloudinary
        import cloudinary.uploader

        cloudinary.config(
            cloud_name=self.settings.cloudinary_cloud_name,
            api_key=self.settings.cloudinary_api_key,
            api_secret=self.settings.cloudinary_api_secret,
            secure=True,
        )
        result = cloudinary.uploader.upload(
            str(image_path),
            folder="askbot/play-store-promos",
            resource_type="image",
            overwrite=True,
        )
        secure_url = result.get("secure_url")
        if not secure_url:
            raise RuntimeError("Cloudinary upload did not return a secure URL.")
        return str(secure_url)

    def upload_video(self, video_path: Path) -> str:
        if not self.configured:
            raise RuntimeError("Cloudinary is not configured.")

        import cloudinary
        import cloudinary.uploader

        cloudinary.config(
            cloud_name=self.settings.cloudinary_cloud_name,
            api_key=self.settings.cloudinary_api_key,
            api_secret=self.settings.cloudinary_api_secret,
            secure=True,
        )
        result = cloudinary.uploader.upload(
            str(video_path),
            folder="askbot/play-store-reels",
            resource_type="video",
            overwrite=True,
        )
        secure_url = result.get("secure_url")
        if not secure_url:
            raise RuntimeError("Cloudinary video upload did not return a secure URL.")
        return str(secure_url)
