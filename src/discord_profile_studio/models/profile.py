from dataclasses import dataclass, field

from discord_profile_studio.models.favourite import Favourite


@dataclass(slots=True)
class Profile:
    version: int = 1
    active: str = ""
    favourites: list[Favourite] = field(default_factory=list)
