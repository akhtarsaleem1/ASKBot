from __future__ import annotations

from askbot.services.play_store import normalize_app_link, package_from_link


def test_package_from_play_store_link():
    link = "https://play.google.com/store/apps/details?id=com.example.app&hl=en_US"

    assert package_from_link(link) == "com.example.app"
    assert normalize_app_link("com.example.app") == "https://play.google.com/store/apps/details?id=com.example.app"

