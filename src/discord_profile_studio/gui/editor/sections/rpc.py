from discord_profile_studio.gui.editor.sections.base import EditorSection
from discord_profile_studio.gui.sections import Section
from discord_profile_studio.models.presence import Presence


class RpcSection(EditorSection):
    section = Section.RPC

    def build(self) -> None:
        raise NotImplementedError

    def read(self) -> None:
        raise NotImplementedError

    def write(self) -> None:
        raise NotImplementedError

    def to_model(self) -> Presence:
        raise NotImplementedError

    def from_model(self, presence: Presence) -> None:
        raise NotImplementedError
