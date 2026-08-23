import tkinter as tk

from discord_profile_studio.models.widget import Widget


class WidgetCard:
    def __init__(self, canvas: tk.Canvas) -> None:
        self.canvas = canvas

    def draw(self, widget: Widget, x: int, y: int) -> int:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError
