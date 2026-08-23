from abc import ABC, abstractmethod

from discord_profile_studio.models.widget import Widget, WidgetKind


class WidgetRenderer(ABC):
    kind: WidgetKind

    @abstractmethod
    def render(self, widget: Widget) -> dict[str, str]: ...

    @abstractmethod
    def validate(self, widget: Widget) -> list[str]: ...
