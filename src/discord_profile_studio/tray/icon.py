import threading
from collections.abc import Callable

from discord_profile_studio.assets import tray_icon
from discord_profile_studio.core.paths import APP_NAME
from discord_profile_studio.tray.backends.base import TrayBackend
from discord_profile_studio.tray.backends.factory import select
from discord_profile_studio.tray.menu import TrayMenu, TrayMenuItem

STOP_TIMEOUT = 5.0


class TrayIcon:
    def __init__(self, menu: TrayMenu, backend: TrayBackend | None = None) -> None:
        self.menu = menu
        self.backend = backend
        self.running = False

        self._thread: threading.Thread | None = None

        self._tooltip = APP_NAME
        self._connected = False
        self._activate: Callable[[], None] | None = None

    def start(self) -> None:
        if self.running:
            return

        if self.backend is None:
            self.backend = select()

        backend = self.backend

        self.running = True

        self._thread = threading.Thread(
            target=self._run,
            args=(backend,),
            name="tray_icon",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        if not self.running:
            return

        self.running = False

        if self.backend is not None:
            self.backend.stop()

        thread = self._thread
        self._thread = None

        if thread is not None:
            thread.join(timeout=STOP_TIMEOUT)

    def set_tooltip(self, text: str) -> None:
        if text == self._tooltip:
            return

        self._tooltip = text
        self._refresh()

    def set_state(self, *, connected: bool) -> None:
        if connected == self._connected:
            return

        self._connected = connected
        self._refresh()

    def on_activate(self, callback: Callable[[], None]) -> None:
        self._activate = callback
        self._refresh()

    def _run(self, backend: TrayBackend) -> None:
        try:
            backend.run(self._compose(), tray_icon(connected=self._connected), self._tooltip)
        finally:
            self.running = False

    def _refresh(self) -> None:
        backend = self.backend
        if backend is None or not self.running:
            return

        backend.update(self._compose(), tray_icon(connected=self._connected), self._tooltip)

    def _compose(self) -> TrayMenu:
        if self._activate is None:
            return self.menu

        entry = TrayMenuItem(
            label=APP_NAME,
            action=self._activate,
            default=True,
            visible=False,
        )

        return TrayMenu(items=[entry, *self.menu.items])
