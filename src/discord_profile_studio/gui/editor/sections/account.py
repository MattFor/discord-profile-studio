from discord_profile_studio.auth.store import TokenStore
from discord_profile_studio.gui.editor.sections.base import EditorSection
from discord_profile_studio.gui.sections import Section


class AccountSection(EditorSection):
    section = Section.ACCOUNT
    store: TokenStore

    def build(self) -> None:
        raise NotImplementedError

    def read(self) -> None:
        raise NotImplementedError

    def write(self) -> None:
        raise NotImplementedError

    def sign_in(self) -> None:
        raise NotImplementedError

    def sign_out(self) -> None:
        raise NotImplementedError
