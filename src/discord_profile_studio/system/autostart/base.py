from abc import ABC, abstractmethod

APP_NAME = "DiscordProfileStudio"
START_MINIMIZED = "--start-minimized"


class AutostartBackend(ABC):
    @abstractmethod
    def enabled(self) -> bool: ...

    @abstractmethod
    def enable(self, *, minimized: bool = True) -> None: ...

    @abstractmethod
    def disable(self) -> None: ...


def backend() -> AutostartBackend:
    raise NotImplementedError
