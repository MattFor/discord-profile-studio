from types import TracebackType

from discord_profile_studio.models.presence import Presence


class PresenceClient:
    def __init__(self, client_id: str) -> None:
        self.client_id = client_id
        self.connected = False

    def connect(self) -> None:
        raise NotImplementedError

    def update(self, presence: Presence) -> None:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError

    def __enter__(self) -> "PresenceClient":
        raise NotImplementedError

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        raise NotImplementedError
