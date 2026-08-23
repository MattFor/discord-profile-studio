from typing import Any

from discord_profile_studio.models.presence import Presence


def to_payload(presence: Presence) -> dict[str, Any]:
    raise NotImplementedError


def from_payload(payload: dict[str, Any]) -> Presence:
    raise NotImplementedError
