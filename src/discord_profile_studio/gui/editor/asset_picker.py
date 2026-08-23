import tkinter as tk
from tkinter import ttk


class AssetPicker(ttk.Frame):
    def __init__(self, master: tk.Misc, label: str) -> None:
        super().__init__(master)
        self.label = label
        self.key = tk.StringVar()
        self.text = tk.StringVar()

    def build(self) -> None:
        raise NotImplementedError

    def browse(self) -> None:
        raise NotImplementedError
