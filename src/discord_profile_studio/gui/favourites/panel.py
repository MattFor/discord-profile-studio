import tkinter as tk
from tkinter import ttk

from discord_profile_studio.gui.state import AppState
from discord_profile_studio.models.favourite import Favourite


class FavouritesPanel(ttk.Frame):
    def __init__(self, master: tk.Misc, state: AppState) -> None:
        super().__init__(master)
        self.state_store = state
        self.items: list[Favourite] = []

    def build(self) -> None:
        raise NotImplementedError

    def populate(self, favourites: list[Favourite]) -> None:
        raise NotImplementedError

    def on_select(self, favourite: Favourite) -> None:
        raise NotImplementedError
