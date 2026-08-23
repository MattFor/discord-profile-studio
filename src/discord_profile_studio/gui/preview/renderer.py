import tkinter as tk

from discord_profile_studio.models.favourite import Favourite


class PreviewRenderer:
    def __init__(self, canvas: tk.Canvas, theme: dict[str, str]) -> None:
        self.canvas = canvas
        self.theme = theme

    def render(self, favourite: Favourite) -> None:
        raise NotImplementedError

    def measure(self, favourite: Favourite) -> tuple[int, int]:
        raise NotImplementedError
