from discord_profile_studio.models.widget import Widget, WidgetKind
from discord_profile_studio.widgets.base import WidgetRenderer


class StatusWidget(WidgetRenderer):
    kind = WidgetKind.STATUS

    def render(self, widget: Widget) -> dict[str, str]:
        raise NotImplementedError

    def validate(self, widget: Widget) -> list[str]:
        raise NotImplementedError
