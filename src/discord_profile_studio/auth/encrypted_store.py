from pathlib import Path

from discord_profile_studio.auth.token import Token

FILE_MODE = 0o600


class EncryptedFileStore:
    name = "encrypted-file"

    def __init__(self, path: Path, passphrase: str | None = None) -> None:
        self.path = path
        self.passphrase = passphrase

    def available(self) -> bool:
        raise NotImplementedError

    def unlock(self, passphrase: str) -> None:
        raise NotImplementedError

    def get(self, account: str) -> Token:
        raise NotImplementedError

    def set(self, account: str, token: Token) -> None:
        raise NotImplementedError

    def delete(self, account: str) -> None:
        raise NotImplementedError

    def accounts(self) -> list[str]:
        raise NotImplementedError
