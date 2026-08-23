import tkinter as tk
from tkinter import ttk


class StatusBar(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.message = tk.StringVar()
        self.connected = tk.BooleanVar(value=False)

    def build(self) -> None:
        raise NotImplementedError

    def set_status(self, message: str, *, connected: bool) -> None:
        raise NotImplementedError
