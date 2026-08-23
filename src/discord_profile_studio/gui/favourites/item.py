import tkinter as tk
from tkinter import ttk

from discord_profile_studio.models.favourite import Favourite


class FavouriteItem(ttk.Frame):
    def __init__(self, master: tk.Misc, favourite: Favourite) -> None:
        super().__init__(master)
        self.favourite = favourite
        self.selected = False

    def build(self) -> None:
        raise NotImplementedError

    def set_selected(self, *, selected: bool) -> None:
        raise NotImplementedError
