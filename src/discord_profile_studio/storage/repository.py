from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from discord_profile_studio.core.exceptions import FavouriteNotFoundError, StorageError
from discord_profile_studio.core.paths import write_private
from discord_profile_studio.models.favourite import Favourite
from discord_profile_studio.storage.document import from_text, to_text


def _utc_now() -> datetime:
    return datetime.now(UTC)


class FavouriteRepository:
    def __init__(self, path: Path, clock: Callable[[], datetime] = _utc_now) -> None:
        self.path = path
        self._clock: Callable[[], datetime] = clock

    def all(self) -> list[Favourite]:
        return self._load()

    def get(self, name: str) -> Favourite:
        favourites = self._load()
        return favourites[_index(favourites, name)]

    def add(self, favourite: Favourite) -> None:
        favourites = self._load()
        _ensure_free(favourites, favourite.name)
        self._save([*favourites, favourite])

    def update(self, favourite: Favourite) -> None:
        favourites = self._load()
        i = _index(favourites, favourite.name)
        favourites[i] = replace(
            favourite, created_at=favourites[i].created_at, updated_at=self._clock()
        )
        self._save(favourites)

    def delete(self, name: str) -> None:
        favourites = self._load()
        del favourites[_index(favourites, name)]
        self._save(favourites)

    def rename(self, name: str, new_name: str) -> None:
        favourites = self._load()
        i = _index(favourites, name)
        _ensure_free(favourites, new_name)
        favourites[i] = replace(favourites[i], name=new_name, updated_at=self._clock())
        self._save(favourites)

    def _load(self) -> list[Favourite]:
        try:
            text = self.path.read_text(encoding="utf-8-sig")
        except FileNotFoundError:
            return []
        except (OSError, UnicodeDecodeError) as e:
            msg = f"cannot read {self.path}: {e}"
            raise StorageError(msg) from e
        return from_text(text)

    def _save(self, favourites: list[Favourite]) -> None:
        text = to_text(favourites)
        try:
            write_private(self.path, text)
        except OSError as e:
            msg = f"cannot write {self.path}: {e}"
            raise StorageError(msg) from e


def _index(favourites: list[Favourite], name: str) -> int:
    for i, favourite in enumerate(favourites):
        if favourite.name == name:
            return i
    msg = f"no favourite named {name!r}"
    raise FavouriteNotFoundError(msg)


def _ensure_free(favourites: list[Favourite], name: str) -> None:
    if any(favourite.name == name for favourite in favourites):
        msg = f"a favourite named {name!r} already exists"
        raise StorageError(msg)
