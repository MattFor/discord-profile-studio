import tkinter as tk
from tkinter import ttk


class LabelledEntry(ttk.Frame):
    def __init__(self, master: tk.Misc, label: str, limit: int = 128) -> None:
        super().__init__(master)
        self.label = label
        self.limit = limit
        self.variable = tk.StringVar()

    def build(self) -> None:
        raise NotImplementedError


class LabelledCombo(ttk.Frame):
    def __init__(self, master: tk.Misc, label: str, values: list[str]) -> None:
        super().__init__(master)
        self.label = label
        self.values = values
        self.variable = tk.StringVar()

    def build(self) -> None:
        raise NotImplementedError


class ButtonRow(ttk.Frame):
    def __init__(self, master: tk.Misc, index: int) -> None:
        super().__init__(master)
        self.index = index
        self.label = tk.StringVar()
        self.url = tk.StringVar()

    def build(self) -> None:
        raise NotImplementedError
