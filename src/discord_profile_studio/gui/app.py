import tkinter as tk
from tkinter import simpledialog, ttk

from discord_profile_studio.core.exceptions import StudioError
from discord_profile_studio.core.paths import favourites_file
from discord_profile_studio.gui.editor.panel import EditorPanel
from discord_profile_studio.gui.favourites.panel import FavouritesPanel
from discord_profile_studio.gui.preview.panel import PreviewPanel
from discord_profile_studio.gui.state import AppState
from discord_profile_studio.storage.repository import FavouriteRepository

TITLE = "Discord Profile Studio"


class Application(tk.Tk):
    paned: ttk.PanedWindow
    favourites: FavouritesPanel
    editor: EditorPanel
    preview: PreviewPanel

    def __init__(self, state: AppState | None = None) -> None:
        super().__init__()
        self.state_store = state or AppState()
        self.message = tk.StringVar()

    def build(self) -> None:
        self.title(TITLE)
        self.geometry("760x560")
        self.minsize(520, 360)

        # ponytail: the favourites list and the preview join the editor here once they are built
        self.editor = EditorPanel(self, self.state_store)
        self.editor.build()
        self.editor.pack(fill="both", expand=True, padx=12, pady=(12, 0))

        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=12, pady=12)

        ttk.Button(bar, text="Save", command=self.save).pack(side="right")
        ttk.Label(bar, textvariable=self.message).pack(side="left")

    def save(self) -> None:
        self.editor.write()
        favourite = self.state_store.current
        # A favourite loaded by name is updated, a new one must not overwrite an existing one
        loaded = bool(favourite.name.strip())

        if not loaded:
            name = simpledialog.askstring("Save favourite", "Name of the favourite", parent=self)

            if not name or not name.strip():
                return

            favourite.name = name.strip()

        repository = FavouriteRepository(favourites_file())

        try:
            if loaded:
                repository.update(favourite)
            else:
                repository.add(favourite)
        except StudioError as e:
            if not loaded:
                favourite.name = ""

            self.message.set(str(e))
            return

        self.state_store.dirty = False
        self.message.set(f"Saved {favourite.name}")


def run(state: AppState | None = None) -> None:
    app = Application(state)
    app.build()
    app.mainloop()
