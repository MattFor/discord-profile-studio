from abc import ABC, abstractmethod
from pathlib import Path

from discord_profile_studio.models.favourite import Favourite


class Importer(ABC):
    name: str

    @abstractmethod
    def detect(self, path: Path) -> bool: ...

    @abstractmethod
    def load(self, path: Path) -> list[Favourite]: ...
