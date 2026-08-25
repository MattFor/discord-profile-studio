from dataclasses import dataclass, field
from enum import StrEnum


class WidgetKind(StrEnum):
    STATUS = "status"
    MEDIA = "media"
    ACTIVITY = "activity"
    LINK = "link"
    CUSTOM = "custom"


@dataclass(slots=True)
class Widget:
    kind: WidgetKind = WidgetKind.CUSTOM
    title: str = ""
    body: str = ""
    icon: str = ""
    accent: str = "#5865f2"
    enabled: bool = True
    options: dict[str, str] = field(default_factory=dict)
