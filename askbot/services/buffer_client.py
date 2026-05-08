from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import requests

from askbot.config import Settings


BUFFER_ENDPOINT = "https://api.buffer.com"


@dataclass
class BufferPostResult:
    post_id: str
    status: str
    due_at: str = ""


@dataclass
class BufferChannelInfo:
    id: str
    name: str
    service: str
    account_label: str = "primary"


class BufferClient:
    def __init__(
        self,
        settings: Settings,
        timeout: int = 30,
        api_key: str | None = None,
        account_label: str = "primary",
    ) -> None:
        self.settings = settings
        self.timeout = timeout
        self.api_key = api_key if api_key is not None else settings.buffer_api_key
        self.account_label = account_label

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def graphql(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError(f"Buffer API key is not configured for account '{self.account_label}'.")
        response = requests.post(
            BUFFER_ENDPOINT,
            json={"query": query, "variables": variables or {}},
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=self.timeout,
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            detail = response.text[:500]
            raise RuntimeError(f"Buffer HTTP {response.status_code}: {detail}") from exc
        payload = response.json()
        if payload.get("errors"):
            raise RuntimeError(str(payload["errors"]))
        return payload.get("data", {})

    def list_channels(self) -> list[BufferChannelInfo]:
        org_query = """
        query GetOrganizations {
          account {
            organizations {
              id
              name
            }
          }
        }
        """
        org_data = self.graphql(org_query)
        organizations = org_data.get("account", {}).get("organizations", []) or []
        channels: list[BufferChannelInfo] = []

        channel_query = """
        query GetChannels($organizationId: OrganizationId!) {
          channels(input: { organizationId: $organizationId }) {
            id
            name
            service
          }
        }
        """
        for org in organizations:
            org_id = org.get("id")
            if not org_id:
                continue
            data = self.graphql(channel_query, {"organizationId": org_id})
            for channel in data.get("channels", []) or []:
                channels.append(
                    BufferChannelInfo(
                        id=str(channel.get("id", "")),
                        name=str(channel.get("name") or channel.get("id") or "Buffer channel"),
                        service=str(channel.get("service") or "generic").lower(),
                        account_label=self.account_label,
                    )
                )
        return [channel for channel in channels if channel.id]

    def create_post(
        self,
        *,
        channel_id: str,
        text: str,
        due_at: datetime,
        image_url: str = "",
        video_url: str = "",
        video_title: str = "",
        mode: str = "customScheduled",
        service: str = "",
    ) -> BufferPostResult:
        mutation = """
        mutation CreatePost($input: CreatePostInput!) {
          createPost(input: $input) {
            ... on PostActionSuccess {
              post {
                id
                status
                dueAt
              }
            }
            ... on MutationError {
              message
            }
          }
        }
        """
        input_payload: dict[str, Any] = {
            "text": text,
            "channelId": channel_id,
            "schedulingType": "automatic",
            "mode": mode,
        }
        normalized_service = service.lower()
        if normalized_service == "facebook":
            input_payload["metadata"] = {"facebook": {"type": "post"}}
        elif normalized_service == "instagram":
            input_payload["metadata"] = {"instagram": {"type": "post", "shouldShareToFeed": True}}
        elif normalized_service == "youtube":
            input_payload["metadata"] = {
                "youtube": {
                    "title": (video_title or text.splitlines()[0] or "App spotlight")[:95],
                    "categoryId": "28",
                    "privacy": "public",
                    "notifySubscribers": False,
                    "embeddable": True,
                    "madeForKids": False,
                }
            }
        if mode == "customScheduled":
            input_payload["dueAt"] = due_at.astimezone().isoformat()
        if video_url:
            input_payload["assets"] = {"videos": [{"url": video_url, "metadata": {"title": video_title[:95] if video_title else ""}}]}
        elif image_url:
            input_payload["assets"] = {"images": [{"url": image_url}]}

        data = self.graphql(mutation, {"input": input_payload})
        result = data.get("createPost", {})
        if result.get("message"):
            raise RuntimeError(str(result["message"]))
        post = result.get("post") or {}
        post_id = str(post.get("id") or "")
        if not post_id:
            raise RuntimeError("Buffer createPost did not return a post id.")
        return BufferPostResult(
            post_id=post_id,
            status=str(post.get("status") or "scheduled"),
            due_at=str(post.get("dueAt") or ""),
        )


def configured_buffer_clients(settings: Settings) -> dict[str, BufferClient]:
    return {
        label: BufferClient(settings, api_key=api_key, account_label=label)
        for label, api_key in settings.buffer_api_keys.items()
        if api_key
    }
