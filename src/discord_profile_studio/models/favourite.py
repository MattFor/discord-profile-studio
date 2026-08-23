from dataclasses import dataclass, field
from datetime import datetime

from discord_profile_studio.models.presence import Presence
from discord_profile_studio.models.widget import Widget


@dataclass(slots=True)
class Favourite:
    name: str = ""
    presence: Presence = field(default_factory=Presence)
    widgets: list[Widget] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
