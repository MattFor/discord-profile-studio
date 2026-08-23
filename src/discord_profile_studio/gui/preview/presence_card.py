import tkinter as tk

from discord_profile_studio.models.presence import Presence


class PresenceCard:
    def __init__(self, canvas: tk.Canvas) -> None:
        self.canvas = canvas

    def draw(self, presence: Presence, x: int, y: int) -> int:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError
