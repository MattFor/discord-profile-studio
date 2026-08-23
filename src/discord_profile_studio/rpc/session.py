from discord_profile_studio.models.presence import Presence
from discord_profile_studio.rpc.client import PresenceClient


class PresenceSession:
    def __init__(self, client: PresenceClient, interval: float = 15.0) -> None:
        self.client = client
        self.interval = interval
        self.current: Presence | None = None

    def start(self, presence: Presence) -> None:
        raise NotImplementedError

    def apply(self, presence: Presence) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        raise NotImplementedError
