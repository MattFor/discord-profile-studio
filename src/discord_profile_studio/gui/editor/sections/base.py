import tkinter as tk
from abc import abstractmethod
from tkinter import ttk

from discord_profile_studio.gui.sections import Section
from discord_profile_studio.gui.state import AppState


class EditorSection(ttk.Frame):
    section: Section

    def __init__(self, master: tk.Misc, state: AppState) -> None:
        super().__init__(master)
        self.state_store = state

    @abstractmethod
    def build(self) -> None: ...

    @abstractmethod
    def read(self) -> None: ...

    @abstractmethod
    def write(self) -> None: ...
