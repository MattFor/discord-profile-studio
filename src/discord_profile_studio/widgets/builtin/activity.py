from discord_profile_studio.models.widget import Widget, WidgetKind
from discord_profile_studio.widgets.base import WidgetRenderer


class ActivityWidget(WidgetRenderer):
    kind = WidgetKind.ACTIVITY

    def render(self, widget: Widget) -> dict[str, str]:
        raise NotImplementedError

    def validate(self, widget: Widget) -> list[str]:
        raise NotImplementedError
