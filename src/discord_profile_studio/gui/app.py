import tkinter as tk
from tkinter import ttk

from discord_profile_studio.gui.editor.panel import EditorPanel
from discord_profile_studio.gui.favourites.panel import FavouritesPanel
from discord_profile_studio.gui.preview.panel import PreviewPanel
from discord_profile_studio.gui.state import AppState


class Application(tk.Tk):
    paned: ttk.PanedWindow
    favourites: FavouritesPanel
    editor: EditorPanel
    preview: PreviewPanel

    def __init__(self, state: AppState | None = None) -> None:
        super().__init__()
        self.state_store = state or AppState()

    def build(self) -> None:
        raise NotImplementedError


def run(state: AppState | None = None) -> None:
    raise NotImplementedError
