import tkinter as tk

from discord_profile_studio.gui.controller import StudioController
from discord_profile_studio.tray.icon import TrayIcon


class TrayBridge:
    def __init__(self, root: tk.Tk, controller: StudioController, tray: TrayIcon) -> None:
        self.root = root
        self.controller = controller
        self.tray = tray

    def install(self) -> None:
        raise NotImplementedError

    def hide_to_tray(self) -> None:
        raise NotImplementedError

    def restore(self) -> None:
        raise NotImplementedError

    def on_close(self) -> None:
        raise NotImplementedError
