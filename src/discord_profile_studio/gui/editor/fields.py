import tkinter as tk
from tkinter import ttk

LABEL_WIDTH = 20


class LabelledEntry(ttk.Frame):
    def __init__(self, master: tk.Misc, label: str, limit: int = 128) -> None:
        super().__init__(master)
        self.label = label
        self.limit = limit
        self.variable = tk.StringVar()

    def build(self) -> None:
        ttk.Label(self, text=self.label, width=LABEL_WIDTH).pack(side="left")
        self.entry = ttk.Entry(self, textvariable=self.variable)
        self.entry.pack(side="left", fill="x", expand=True)
        self.variable.trace_add("write", self._clip)

    def _clip(self, *_: object) -> None:
        value = self.variable.get()

        if len(value) > self.limit:
            self.variable.set(value[: self.limit])


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
