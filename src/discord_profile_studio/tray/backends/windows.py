from pathlib import Path

from discord_profile_studio.tray.backends.base import TrayBackend
from discord_profile_studio.tray.menu import TrayMenu


class WindowsTray(TrayBackend):
    name = "windows"

    def available(self) -> bool:
        raise NotImplementedError

    def run(self, menu: TrayMenu, icon_path: Path, tooltip: str) -> None:
        raise NotImplementedError

    def update(self, menu: TrayMenu, icon_path: Path, tooltip: str) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        raise NotImplementedError
