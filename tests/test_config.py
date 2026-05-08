from __future__ import annotations

from askbot.config import parse_buffer_api_keys


def test_parse_buffer_api_keys_supports_primary_second_and_named(monkeypatch):
    monkeypatch.setenv("BUFFER_API_KEY", "first")
    monkeypatch.setenv("BUFFER_API_KEY_2", "second")
    monkeypatch.setenv("BUFFER_API_KEYS", "main:third,extra:fourth")

    keys = parse_buffer_api_keys()

    assert keys == {
        "primary": "first",
        "main": "third",
        "extra": "fourth",
        "account2": "second",
    }
