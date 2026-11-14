from dataclasses import dataclass, field
from datetime import UTC, datetime

from discord_profile_studio.models.presence import Presence
from discord_profile_studio.models.widget import Widget


def _utc_now() -> datetime:
    return datetime.now(UTC)


_SAME_AS_CREATED = datetime.min.replace(tzinfo=UTC)


@dataclass(slots=True)
class Favourite:
    name: str = ""
    presence: Presence = field(default_factory=Presence)
    widgets: list[Widget] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = _SAME_AS_CREATED

    def __post_init__(self) -> None:
        if self.updated_at is _SAME_AS_CREATED:
            self.updated_at = self.created_at
