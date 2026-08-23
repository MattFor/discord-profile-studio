from collections.abc import Callable

from discord_profile_studio.tray.backends.base import TrayBackend
from discord_profile_studio.tray.menu import TrayMenu


class TrayIcon:
    def __init__(self, menu: TrayMenu, backend: TrayBackend | None = None) -> None:
        self.menu = menu
        self.backend = backend
        self.running = False

    def start(self) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        raise NotImplementedError

    def set_tooltip(self, text: str) -> None:
        raise NotImplementedError

    def set_state(self, *, connected: bool) -> None:
        raise NotImplementedError

    def on_activate(self, callback: Callable[[], None]) -> None:
        raise NotImplementedError
