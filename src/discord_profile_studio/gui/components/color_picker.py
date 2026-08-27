import tkinter as tk
from tkinter import TclError, colorchooser, ttk

from discord_profile_studio.core.color import to_hex, to_int


class ColorPicker(ttk.Frame):
    def __init__(self, master: tk.Misc, initial: str = "#5865F2") -> None:
        super().__init__(master)
        self.value = tk.StringVar(value=initial)

    def build(self) -> None:
        self.swatch = tk.Label(self, bg=self.value.get(), width=3, relief="solid", borderwidth=1)
        self.swatch.pack(side="left")

        self.label = ttk.Label(self, textvariable=self.value)
        self.label.pack(side="left", padx=8)

        self.button = ttk.Button(self, text="Choose color", command=self.choose)
        self.button.pack(side="left")

        self.value.trace_add("write", self._on_value_changed)

    def _on_value_changed(self, *_: object) -> None:
        try:
            self.swatch.configure(bg=self.value.get())
        except TclError:
            return

    def choose(self) -> None:
        _, chosen = colorchooser.askcolor(
            color=self.value.get(),
            parent=self,
            title="Pick accent color",
        )
        if chosen is None:
            return
        self.value.set("#" + to_hex(to_int(chosen)))
