import tkinter as tk


class Tooltip:
    def __init__(self, widget: tk.Misc, text: str, delay_ms: int = 400) -> None:
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self.window: tk.Toplevel | None = None

    def show(self) -> None:
        raise NotImplementedError

    def hide(self) -> None:
        raise NotImplementedError
