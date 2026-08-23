from discord_profile_studio.gui.state import AppState
from discord_profile_studio.models.favourite import Favourite
from discord_profile_studio.rpc.session import PresenceSession
from discord_profile_studio.storage.repository import FavouriteRepository


class StudioController:
    def __init__(
        self,
        state: AppState,
        repository: FavouriteRepository,
        session: PresenceSession,
    ) -> None:
        self.state = state
        self.repository = repository
        self.session = session

    def load_favourites(self) -> list[Favourite]:
        raise NotImplementedError

    def select(self, name: str) -> None:
        raise NotImplementedError

    def save_current(self) -> None:
        raise NotImplementedError

    def apply_current(self) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        raise NotImplementedError
