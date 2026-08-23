from discord_profile_studio.models.widget import WidgetKind
from discord_profile_studio.widgets.base import WidgetRenderer

_RENDERERS: dict[WidgetKind, WidgetRenderer] = {}


def register(renderer: WidgetRenderer) -> None:
    raise NotImplementedError


def get(kind: WidgetKind) -> WidgetRenderer:
    raise NotImplementedError


def available() -> list[WidgetKind]:
    raise NotImplementedError
