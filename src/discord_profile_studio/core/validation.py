from discord_profile_studio.models.presence import Presence


def validate_presence(presence: Presence) -> list[str]:
    raise NotImplementedError


def validate_client_id(client_id: str) -> bool:
    raise NotImplementedError
