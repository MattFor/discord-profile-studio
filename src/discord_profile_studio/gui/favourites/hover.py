import tkinter as tk

from discord_profile_studio.gui.state import AppState
from discord_profile_studio.models.favourite import Favourite


class HoverPreview:
    def __init__(self, state: AppState, delay_ms: int = 120) -> None:
        self.state_store = state
        self.delay_ms = delay_ms
        self.pending: str | None = None

    def bind(self, widget: tk.Misc, favourite: Favourite) -> None:
        raise NotImplementedError

    def enter(self, favourite: Favourite) -> None:
        raise NotImplementedError

    def leave(self) -> None:
        raise NotImplementedError

    def cancel(self) -> None:
        raise NotImplementedError
