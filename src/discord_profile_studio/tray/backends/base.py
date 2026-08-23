from abc import ABC, abstractmethod
from pathlib import Path

from discord_profile_studio.tray.menu import TrayMenu


class TrayBackend(ABC):
    name: str

    @abstractmethod
    def available(self) -> bool: ...

    @abstractmethod
    def run(self, menu: TrayMenu, icon_path: Path, tooltip: str) -> None: ...

    @abstractmethod
    def update(self, menu: TrayMenu, icon_path: Path, tooltip: str) -> None: ...

    @abstractmethod
    def stop(self) -> None: ...


def select() -> TrayBackend:
    raise NotImplementedError
