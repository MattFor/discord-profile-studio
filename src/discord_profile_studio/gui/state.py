from collections.abc import Callable

from discord_profile_studio.models.favourite import Favourite

Listener = Callable[[Favourite], None]


class AppState:
    def __init__(self) -> None:
        self.current: Favourite = Favourite()
        self.hovered: Favourite | None = None
        self.dirty: bool = False
        self._listeners: list[Listener] = []

    @property
    def previewed(self) -> Favourite:
        return self.current if self.hovered is None else self.hovered

    def subscribe(self, listener: Listener) -> Callable[[], None]:
        self._listeners.append(listener)

        return lambda: self._listeners.remove(listener)

    def notify(self) -> None:
        # A copy, so a listener may unsubscribe while being called
        for listener in list(self._listeners):
            listener(self.previewed)

    def set_current(self, favourite: Favourite) -> None:
        self.current = favourite
        self.dirty = False
        self.notify()

    def set_hovered(self, favourite: Favourite | None) -> None:
        self.hovered = favourite
        self.notify()
