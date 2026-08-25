import tkinter as tk
from tkinter import ttk


class ColorPicker(ttk.Frame):
    def __init__(self, master: tk.Misc, initial: str = "#5865F2") -> None:
        super().__init__(master)
        self.value = tk.StringVar(value=initial)

    def build(self) -> None:
        raise NotImplementedError

    def choose(self) -> None:
        raise NotImplementedError
