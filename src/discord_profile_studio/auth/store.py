from typing import Protocol, runtime_checkable

from discord_profile_studio.auth.token import Token


@runtime_checkable
class TokenStore(Protocol):
    name: str

    def available(self) -> bool: ...

    def get(self, account: str) -> Token: ...

    def set(self, account: str, token: Token) -> None: ...

    def delete(self, account: str) -> None: ...

    def accounts(self) -> list[str]: ...


def open_store(preferred: str | None = None) -> TokenStore:
    raise NotImplementedError
