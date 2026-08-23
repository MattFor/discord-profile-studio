import tkinter as tk
from tkinter import ttk

from discord_profile_studio.gui.sections import Section
from discord_profile_studio.gui.state import AppState
from discord_profile_studio.models.favourite import Favourite


class PreviewPanel(ttk.Frame):
    canvas: tk.Canvas

    def __init__(self, master: tk.Misc, state: AppState) -> None:
        super().__init__(master)
        self.state_store = state

    def build(self) -> None:
        raise NotImplementedError

    def show(self, section: Section) -> None:
        raise NotImplementedError

    def refresh(self, favourite: Favourite) -> None:
        raise NotImplementedError
