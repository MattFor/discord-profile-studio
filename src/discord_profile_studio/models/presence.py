from dataclasses import dataclass, field
from enum import IntEnum, StrEnum


class ActivityType(IntEnum):
    PLAYING = 0
    LISTENING = 2
    WATCHING = 3
    COMPETING = 5


class TimestampMode(StrEnum):
    NONE = "none"
    SINCE_START = "since_start"
    LOCAL_TIME = "local_time"
    CUSTOM = "custom"


@dataclass(slots=True)
class Asset:
    key: str = ""
    text: str = ""


@dataclass(slots=True)
class Button:
    label: str = ""
    url: str = ""


@dataclass(slots=True)
class Party:
    size: int = 0
    maximum: int = 0


@dataclass(slots=True)
class Timestamps:
    mode: TimestampMode = TimestampMode.NONE
    start: int | None = None
    end: int | None = None


@dataclass(slots=True)
class Presence:
    client_id: str = ""
    activity_type: ActivityType = ActivityType.PLAYING
    details: str = ""
    state: str = ""
    large_image: Asset = field(default_factory=Asset)
    small_image: Asset = field(default_factory=Asset)
    party: Party = field(default_factory=Party)
    timestamps: Timestamps = field(default_factory=Timestamps)
    buttons: list[Button] = field(default_factory=list)
