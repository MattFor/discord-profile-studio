from typing import Any

from discord_profile_studio.models.favourite import Favourite
from discord_profile_studio.models.presence import Presence
from discord_profile_studio.models.widget import Widget


def presence_to_dict(presence: Presence) -> dict[str, Any]:
    raise NotImplementedError


def presence_from_dict(data: dict[str, Any]) -> Presence:
    raise NotImplementedError


def widget_to_dict(widget: Widget) -> dict[str, Any]:
    raise NotImplementedError


def widget_from_dict(data: dict[str, Any]) -> Widget:
    raise NotImplementedError


def favourite_to_dict(favourite: Favourite) -> dict[str, Any]:
    raise NotImplementedError


def favourite_from_dict(data: dict[str, Any]) -> Favourite:
    raise NotImplementedError
