from datetime import UTC, datetime, timedelta

import pytest

from discord_profile_studio.auth.token import REFRESH_LEEWAY, Token, TokenKind
from discord_profile_studio.core.exceptions import AuthError

ACCESS = "aBcDeFgHiJkLmNoPqRsTuVwXyZ012345"
REFRESH = "0123456789abcdefghijklmnopqrstuv"
NOW = datetime(1970, 1, 1, 0, 0, tzinfo=UTC)


def make_token(**overrides):
    values = {
        "kind": TokenKind.OAUTH,
        "access_token": ACCESS,
        "refresh_token": REFRESH,
        "scopes": ["identify", "rpc"],
        "expires_at": datetime.now(UTC) + timedelta(hours=1),
    }

    return Token(**{**values, **overrides})


def test_a_token_without_an_expiry_never_expires():
    assert not make_token(expires_at=None).expired
    assert not make_token(expires_at=None).needs_refresh


def test_a_future_token_is_not_expired():
    assert not make_token().expired


def test_a_past_token_is_expired():
    assert make_token(expires_at=datetime.now(UTC) - timedelta(seconds=1)).expired


def test_a_token_close_to_expiry_needs_a_refresh():
    soon = datetime.now(UTC) + REFRESH_LEEWAY - timedelta(seconds=30)

    assert make_token(expires_at=soon).needs_refresh
    assert not make_token(expires_at=soon).expired


def test_an_empty_token_is_empty():
    assert Token().empty
    assert not make_token().empty


@pytest.mark.parametrize(
    ("kind", "expected"),
    [(TokenKind.BOT, f"Bot {ACCESS}"), (TokenKind.OAUTH, f"Bearer {ACCESS}")],
)
def test_header_uses_the_right_prefix(kind, expected):
    assert make_token(kind=kind).header == expected


def test_dict_roundtrip():
    token = make_token(expires_at=NOW)

    assert Token.from_dict(token.to_dict()) == token


@pytest.mark.parametrize("scopes", [None, [], ["identify"], ["identify", "rpc"]])
def test_dict_roundtrip_keeps_the_scopes(scopes):
    token = make_token(scopes=scopes, expires_at=NOW)

    assert Token.from_dict(token.to_dict()).scopes == scopes


def test_to_dict_is_json_friendly():
    data = make_token(expires_at=NOW).to_dict()

    assert data["kind"] == "oauth"
    assert data["scopes"] == ["identify", "rpc"]
    assert data["expires_at"] == NOW.isoformat()


def test_from_dict_fills_in_defaults():
    token = Token.from_dict({"access_token": ACCESS})

    assert token.kind is TokenKind.OAUTH
    assert token.refresh_token == ""
    assert token.scopes is None
    assert token.expires_at is None


def test_from_dict_accepts_an_epoch_expiry():
    token = Token.from_dict({"access_token": ACCESS, "expires_at": NOW.timestamp()})

    assert token.expires_at == NOW


def test_from_dict_treats_a_naive_expiry_as_utc():
    token = Token.from_dict({"access_token": ACCESS, "expires_at": "2026-08-31T12:00:00"})

    assert token.expires_at == NOW


@pytest.mark.parametrize("data", [[], "token", 1, None])
def test_from_dict_rejects_a_non_record(data):
    with pytest.raises(AuthError):
        Token.from_dict(data)


def test_from_dict_rejects_an_unknown_kind():
    with pytest.raises(AuthError):
        Token.from_dict({"access_token": ACCESS, "kind": "magic"})


def test_from_dict_rejects_a_broken_expiry():
    with pytest.raises(AuthError):
        Token.from_dict({"access_token": ACCESS, "expires_at": "tomorrow"})


def test_from_response_reads_a_discord_payload():
    token = Token.from_response(
        {
            "access_token": ACCESS,
            "refresh_token": REFRESH,
            "expires_in": 604800,
            "scope": "identify rpc",
            "token_type": "Bearer",
        },
        issued_at=NOW,
    )

    assert token.access_token == ACCESS
    assert token.refresh_token == REFRESH
    assert token.scopes == ["identify", "rpc"]
    assert token.expires_at == NOW + timedelta(days=7)


def test_from_response_without_an_expiry():
    token = Token.from_response({"access_token": ACCESS}, issued_at=NOW)

    assert token.expires_at is None
    assert token.scopes is None


def test_from_response_rejects_a_payload_without_a_token():
    with pytest.raises(AuthError):
        Token.from_response({"error": "invalid_grant"})


@pytest.mark.parametrize("data", [[], "token", None])
def test_from_response_rejects_a_non_record(data):
    with pytest.raises(AuthError):
        Token.from_response(data)


def test_repr_hides_the_secrets():
    text = repr(make_token())

    assert ACCESS not in text
    assert REFRESH not in text
    assert "oauth" in text


def test_repr_survives_an_empty_token():
    assert "Token(" in repr(Token())
