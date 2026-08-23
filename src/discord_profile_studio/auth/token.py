from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class TokenKind(StrEnum):
    BOT = "bot"
    OAUTH = "oauth"


@dataclass(slots=True)
class Token:
    kind: TokenKind = TokenKind.OAUTH
    access_token: str = ""
    refresh_token: str = ""
    scopes: list[str] | None = None
    expires_at: datetime | None = None

    @property
    def expired(self) -> bool:
        raise NotImplementedError
