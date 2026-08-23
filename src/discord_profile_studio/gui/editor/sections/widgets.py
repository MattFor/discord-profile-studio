from discord_profile_studio.gui.editor.sections.base import EditorSection
from discord_profile_studio.gui.sections import Section
from discord_profile_studio.models.widget import Widget


class WidgetsSection(EditorSection):
    section = Section.WIDGETS

    def build(self) -> None:
        raise NotImplementedError

    def read(self) -> None:
        raise NotImplementedError

    def write(self) -> None:
        raise NotImplementedError

    def to_model(self) -> list[Widget]:
        raise NotImplementedError

    def from_model(self, widgets: list[Widget]) -> None:
        raise NotImplementedError

    def add_widget(self, widget: Widget) -> None:
        raise NotImplementedError

    def remove_widget(self, index: int) -> None:
        raise NotImplementedError
