from collections.abc import Callable

from discord_profile_studio.models.favourite import Favourite

Listener = Callable[[Favourite], None]


class AppState:
    def __init__(self) -> None:
        self.current: Favourite
        self.hovered: Favourite | None
        self.dirty: bool
        self._listeners: list[Listener]

    @property
    def previewed(self) -> Favourite:
        raise NotImplementedError

    def subscribe(self, listener: Listener) -> Callable[[], None]:
        raise NotImplementedError

    def notify(self) -> None:
        raise NotImplementedError

    def set_current(self, favourite: Favourite) -> None:
        raise NotImplementedError

    def set_hovered(self, favourite: Favourite | None) -> None:
        raise NotImplementedError
