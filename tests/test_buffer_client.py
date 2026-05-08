from __future__ import annotations

from datetime import datetime, timezone

from askbot.services.buffer_client import BufferClient


class CapturingBufferClient(BufferClient):
    def __init__(self, settings):
        super().__init__(settings, api_key="test")
        self.variables = {}

    def graphql(self, query, variables=None):
        self.variables = variables or {}
        return {"createPost": {"post": {"id": "post-1", "status": "scheduled"}}}


def test_create_post_uses_facebook_metadata(test_settings):
    client = CapturingBufferClient(test_settings)

    client.create_post(
        channel_id="facebook-channel",
        text="hello",
        due_at=datetime.now(timezone.utc),
        service="facebook",
    )

    assert client.variables["input"]["metadata"] == {"facebook": {"type": "post"}}


def test_create_post_uses_instagram_metadata(test_settings):
    client = CapturingBufferClient(test_settings)

    client.create_post(
        channel_id="instagram-channel",
        text="hello",
        due_at=datetime.now(timezone.utc),
        service="instagram",
    )

    assert client.variables["input"]["metadata"] == {
        "instagram": {"type": "post", "shouldShareToFeed": True}
    }
