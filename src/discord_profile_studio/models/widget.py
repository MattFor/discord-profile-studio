from dataclasses import dataclass, field
from enum import IntEnum


# Discord's wire codes for a dynamic value's "type"
class FieldType(IntEnum):
    TEXT = 1
    NUMBER = 2
    IMAGE = 3


@dataclass(slots=True)
class WidgetField:
    name: str = ""
    kind: FieldType = FieldType.TEXT
    # Text, a number written out, or an image URL
    value: str = ""


# One Developer Portal application, its layout lives on Discord and only the values live here
@dataclass(slots=True)
class Widget:
    application_id: str = ""
    name: str = ""
    fields: list[WidgetField] = field(default_factory=list)
