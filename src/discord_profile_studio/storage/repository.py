from pathlib import Path

from discord_profile_studio.core.exceptions import StorageError
from discord_profile_studio.models.favourite import Favourite
from discord_profile_studio.storage.document import from_text


class FavouriteRepository:
    def __init__(self, path: Path) -> None:
        self.path = path

    def all(self) -> list[Favourite]:
        return self._load()

    def get(self, name: str) -> Favourite:
        raise NotImplementedError

    def add(self, favourite: Favourite) -> None:
        raise NotImplementedError

    def update(self, favourite: Favourite) -> None:
        raise NotImplementedError

    def delete(self, name: str) -> None:
        raise NotImplementedError

    def rename(self, name: str, new_name: str) -> None:
        raise NotImplementedError

    def _load(self) -> list[Favourite]:
        try:
            text = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return []
        except (OSError, UnicodeDecodeError) as e:
            msg = f"cannot read {self.path}: {e}"
            raise StorageError(msg) from e
        return from_text(text)
