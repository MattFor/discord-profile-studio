from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any, Self, cast

from discord_profile_studio.auth.redaction import mask
from discord_profile_studio.core.exceptions import AuthError

REFRESH_LEEWAY = timedelta(minutes=5)


class TokenKind(StrEnum):
    BOT = "bot"
    OAUTH = "oauth"


def _now() -> datetime:
    return datetime.now(UTC)


def _as_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)

    return value.astimezone(UTC)


def _parse_moment(value: object) -> datetime | None:
    if value is None or value == "":
        return None

    if isinstance(value, datetime):
        return _as_aware(value)

    if isinstance(value, int | float):
        return datetime.fromtimestamp(float(value), tz=UTC)

    if isinstance(value, str):
        try:
            return _as_aware(datetime.fromisoformat(value))
        except ValueError as e:
            msg = f"Invalid expiry timestamp: {value!r}"
            raise AuthError(msg) from e

    msg = f"Invalid expiry timestamp: {value!r}"
    raise AuthError(msg)


@dataclass(slots=True, repr=False)
class Token:
    kind: TokenKind = TokenKind.OAUTH
    access_token: str = ""
    refresh_token: str = ""
    scopes: list[str] | None = None
    expires_at: datetime | None = None

    @property
    def expired(self) -> bool:
        if self.expires_at is None:
            return False

        return _now() >= self.expires_at

    @property
    def needs_refresh(self) -> bool:
        if self.expires_at is None:
            return False

        return _now() + REFRESH_LEEWAY >= self.expires_at

    @property
    def empty(self) -> bool:
        return not self.access_token

    @property
    def header(self) -> str:
        prefix = "Bot" if self.kind is TokenKind.BOT else "Bearer"

        return f"{prefix} {self.access_token}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "scopes": list(self.scopes) if self.scopes is not None else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }

    @classmethod
    def from_dict(cls, data: object) -> Self:
        if not isinstance(data, dict):
            msg = "Malformed token record"
            raise AuthError(msg)

        record = cast("dict[str, Any]", data)
        raw_kind = str(record.get("kind", TokenKind.OAUTH.value))

        try:
            kind = TokenKind(raw_kind)
        except ValueError as e:
            msg = f"Unknown token kind: {raw_kind!r}"
            raise AuthError(msg) from e

        scopes: Any = record.get("scopes")

        return cls(
            kind=kind,
            access_token=str(record.get("access_token", "")),
            refresh_token=str(record.get("refresh_token", "")),
            scopes=[str(scope) for scope in cast("list[Any]", scopes)]
            if isinstance(scopes, list)
            else None,
            expires_at=_parse_moment(record.get("expires_at")),
        )

    @classmethod
    def from_response(
        cls,
        data: object,
        kind: TokenKind = TokenKind.OAUTH,
        issued_at: datetime | None = None,
    ) -> Self:
        if not isinstance(data, dict):
            msg = "Discord returned a response that is not a token"
            raise AuthError(msg)

        payload = cast("dict[str, Any]", data)
        access_token = str(payload.get("access_token", ""))

        if not access_token:
            msg = "Discord returned a response without an access token"
            raise AuthError(msg)

        expires_in = payload.get("expires_in")
        issued = issued_at or _now()
        scope = str(payload.get("scope", ""))

        return cls(
            kind=kind,
            access_token=access_token,
            refresh_token=str(payload.get("refresh_token", "")),
            scopes=scope.split() or None,
            expires_at=issued + timedelta(seconds=float(expires_in)) if expires_in else None,
        )

    def __repr__(self) -> str:
        return (
            f"Token(kind={self.kind.value}, access_token={mask(self.access_token)!r}, "
            f"refresh_token={mask(self.refresh_token)!r}, scopes={self.scopes!r}, "
            f"expires_at={self.expires_at!r})"
        )
