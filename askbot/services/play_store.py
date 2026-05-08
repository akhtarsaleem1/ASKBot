from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup
from sqlmodel import Session, select

from askbot.models import AppRecord, RunLog


PLAY_BASE = "https://play.google.com"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


@dataclass
class PlayStoreApp:
    package_name: str
    title: str
    app_link: str
    short_description: str = ""
    long_description: str = ""
    icon_url: str = ""
    screenshots: list[str] | None = None
    rating: str = ""
    installs: str = ""


@dataclass
class CatalogRefreshResult:
    discovered: int
    updated: int
    warning: str = ""


def with_locale(url: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    query.setdefault("hl", ["en_US"])
    query.setdefault("gl", ["US"])
    return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))


def package_from_link(link: str) -> str | None:
    parsed = urlparse(link)
    query = parse_qs(parsed.query)
    package = query.get("id", [None])[0]
    if package and "." in package:
        return package
    return None


def normalize_app_link(package_name: str) -> str:
    return f"{PLAY_BASE}/store/apps/details?id={package_name}"


class PlayStoreScraper:
    def __init__(self, timeout: int = 20) -> None:
        self.timeout = timeout

    def fetch(self, url: str) -> str:
        response = requests.get(
            with_locale(url),
            timeout=self.timeout,
            headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"},
        )
        response.raise_for_status()
        return response.text

    def discover_app_links(self, developer_url: str) -> list[str]:
        html_text = self.fetch(developer_url)
        links: set[str] = set()

        for match in re.finditer(r"/store/apps/details\?id=([A-Za-z0-9._]+)", html_text):
            package = html.unescape(match.group(1))
            links.add(normalize_app_link(package))

        soup = BeautifulSoup(html_text, "html.parser")
        for anchor in soup.select("a[href*='/store/apps/details?id=']"):
            href = anchor.get("href") or ""
            if href.startswith("/"):
                href = f"{PLAY_BASE}{href}"
            package = package_from_link(href)
            if package:
                links.add(normalize_app_link(package))

        return sorted(links)

    def fetch_app(self, app_link: str) -> PlayStoreApp:
        package = package_from_link(app_link)
        if not package:
            raise ValueError(f"Could not find package id in app link: {app_link}")

        html_text = self.fetch(app_link)
        soup = BeautifulSoup(html_text, "html.parser")

        title = self._meta(soup, "og:title") or soup.title.string if soup.title else package
        title = self._clean_title(title or package)
        description = self._meta(soup, "og:description") or ""
        long_description = self._extract_long_description(soup) or html.unescape(description).strip()
        icon_url = self._meta(soup, "og:image") or ""
        screenshots = self._extract_screenshots(html_text, icon_url)
        rating = self._extract_first(html_text, r'"([0-5](?:\.[0-9])?) star"') or ""
        installs = self._extract_first(html_text, r'"([0-9,.]+\+?) downloads"') or ""

        return PlayStoreApp(
            package_name=package,
            title=title,
            app_link=normalize_app_link(package),
            short_description=html.unescape(description).strip(),
            long_description=long_description,
            icon_url=icon_url,
            screenshots=screenshots,
            rating=rating,
            installs=installs,
        )

    def fetch_developer_apps(self, developer_url: str) -> list[PlayStoreApp]:
        app_links = self.discover_app_links(developer_url)
        apps: list[PlayStoreApp] = []
        for link in app_links:
            try:
                apps.append(self.fetch_app(link))
            except Exception:
                package = package_from_link(link)
                if package:
                    apps.append(
                        PlayStoreApp(
                            package_name=package,
                            title=package,
                            app_link=normalize_app_link(package),
                        )
                    )
        return apps

    @staticmethod
    def _meta(soup: BeautifulSoup, prop: str) -> str:
        tag = soup.find("meta", attrs={"property": prop})
        if not tag:
            tag = soup.find("meta", attrs={"name": prop})
        return str(tag.get("content", "")).strip() if tag else ""

    @staticmethod
    def _clean_title(title: str) -> str:
        title = html.unescape(title).strip()
        for suffix in (" - Apps on Google Play", " - Google Play"):
            if title.endswith(suffix):
                return title[: -len(suffix)].strip()
        return title

    @staticmethod
    def _extract_first(text: str, pattern: str) -> str | None:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        return html.unescape(match.group(1)) if match else None

    @staticmethod
    def _extract_long_description(soup: BeautifulSoup) -> str:
        """Extract full app description from JSON-LD structured data in the page."""
        for script in soup.find_all("script", {"type": "application/ld+json"}):
            try:
                data = json.loads(script.string or "")
                if isinstance(data, dict) and data.get("@type") == "SoftwareApplication":
                    desc = data.get("description", "")
                    if desc and len(desc) > 20:
                        return html.unescape(desc).strip()
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get("@type") == "SoftwareApplication":
                            desc = item.get("description", "")
                            if desc and len(desc) > 20:
                                return html.unescape(desc).strip()
            except (json.JSONDecodeError, Exception):
                continue
        return ""

    @staticmethod
    def _extract_screenshots(html_text: str, icon_url: str) -> list[str]:
        image_urls = []
        for match in re.finditer(r'https://play-lh\.googleusercontent\.com/[A-Za-z0-9_\-=./]+', html_text):
            url = html.unescape(match.group(0))
            if url and url != icon_url and url not in image_urls:
                image_urls.append(url)
            if len(image_urls) >= 6:
                break
        return image_urls


def upsert_apps(session: Session, apps: Iterable[PlayStoreApp]) -> int:
    updated = 0
    now = datetime.now(timezone.utc)
    for app in apps:
        existing = session.exec(
            select(AppRecord).where(AppRecord.package_name == app.package_name)
        ).first()
        screenshots_json = json.dumps(app.screenshots or [])
        if existing:
            existing.title = app.title
            existing.app_link = app.app_link
            existing.short_description = app.short_description
            existing.long_description = app.long_description
            existing.icon_url = app.icon_url
            existing.screenshots_json = screenshots_json
            existing.rating = app.rating
            existing.installs = app.installs
            existing.updated_at = now
            session.add(existing)
        else:
            session.add(
                AppRecord(
                    package_name=app.package_name,
                    title=app.title,
                    app_link=app.app_link,
                    short_description=app.short_description,
                    long_description=app.long_description,
                    icon_url=app.icon_url,
                    screenshots_json=screenshots_json,
                    rating=app.rating,
                    installs=app.installs,
                )
            )
        updated += 1
    session.commit()
    return updated


def refresh_catalog(session: Session, developer_url: str, scraper: PlayStoreScraper | None = None) -> CatalogRefreshResult:
    scraper = scraper or PlayStoreScraper()
    try:
        apps = scraper.fetch_developer_apps(developer_url)
        if not apps:
            warning = "No apps were discovered from the Play Store developer page."
            session.add(RunLog(level="warning", message=warning))
            session.commit()
            return CatalogRefreshResult(discovered=0, updated=0, warning=warning)

        updated = upsert_apps(session, apps)
        return CatalogRefreshResult(discovered=len(apps), updated=updated)
    except Exception as exc:
        warning = f"Play Store refresh failed; keeping the last saved catalog. {exc}"
        session.add(RunLog(level="error", message=warning))
        session.commit()
        return CatalogRefreshResult(discovered=0, updated=0, warning=warning)

