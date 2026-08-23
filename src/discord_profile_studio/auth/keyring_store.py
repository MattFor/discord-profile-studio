from discord_profile_studio.auth.token import Token

SERVICE = "discord-profile-studio"


class KeyringStore:
    name = "keyring"

    def available(self) -> bool:
        raise NotImplementedError

    def get(self, account: str) -> Token:
        raise NotImplementedError

    def set(self, account: str, token: Token) -> None:
        raise NotImplementedError

    def delete(self, account: str) -> None:
        raise NotImplementedError

    def accounts(self) -> list[str]:
        raise NotImplementedError
