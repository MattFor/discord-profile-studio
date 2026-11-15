import tkinter as tk
from tkinter import ttk

from discord_profile_studio.gui.editor.sections.base import EditorSection
from discord_profile_studio.gui.editor.sections.widgets import WidgetsSection
from discord_profile_studio.gui.sections import Section
from discord_profile_studio.gui.state import AppState

# ponytail: the RPC and account tabs join this tuple once their sections are built
SECTIONS: tuple[type[EditorSection], ...] = (WidgetsSection,)


class EditorPanel(ttk.Frame):
    notebook: ttk.Notebook

    def __init__(self, master: tk.Misc, state: AppState) -> None:
        super().__init__(master)
        self.state_store = state
        self.sections: dict[Section, EditorSection] = {}

    def build(self) -> None:
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        for kind in SECTIONS:
            section = kind(self.notebook, self.state_store)
            section.build()
            self.notebook.add(section, text=section.section.value.title(), padding=8)
            self.sections[section.section] = section

    def show(self, section: Section) -> None:
        self.notebook.select(self.sections[section])

    def read(self) -> None:
        for section in self.sections.values():
            section.read()

    def write(self) -> None:
        for section in self.sections.values():
            section.write()
