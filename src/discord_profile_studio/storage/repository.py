from pathlib import Path

from discord_profile_studio.models.favourite import Favourite


class FavouriteRepository:
    def __init__(self, path: Path) -> None:
        self.path = path

    def all(self) -> list[Favourite]:
        raise NotImplementedError

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
