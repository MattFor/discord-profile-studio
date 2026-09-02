from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from discord_profile_studio.auth import oauth
from discord_profile_studio.auth.oauth import (
    AUTHORIZE_URL,
    REVOKE_URL,
    TOKEN_URL,
    OAuthFlow,
    extract_code,
    new_state,
)
from discord_profile_studio.auth.token import Token, TokenKind
from discord_profile_studio.core.exceptions import AuthError

CLIENT_ID = "123456789012345678"
CLIENT_SECRET = "vErYs3cr3tCl13ntS3cr3t"
REDIRECT_URI = "http://127.0.0.1:6420/callback"
CODE = "n0tAr3alC0de"
ACCESS = "aBcDeFgHiJkLmNoPqRsTuVwXyZ012345"
REFRESH = "0123456789abcdefghijklmnopqrstuv"

PAYLOAD = {
    "access_token": ACCESS,
    "refresh_token": REFRESH,
    "expires_in": 604800,
    "scope": "identify rpc",
    "token_type": "Bearer",
}


class Recorder:
    def __init__(self, status=200, payload=None, text=None):
        self.status = status
        self.payload = payload if payload is not None else PAYLOAD
        self.text = text
        self.calls = []

    def __call__(self, url, **kwargs):
        self.calls.append((url, kwargs))
        request = httpx.Request("POST", url)

        if self.text is not None:
            return httpx.Response(self.status, text=self.text, request=request)

        return httpx.Response(self.status, json=self.payload, request=request)

    @property
    def data(self):
        return self.calls[-1][1]["data"]


@pytest.fixture
def flow():
    return OAuthFlow(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)


@pytest.fixture
def post(monkeypatch):
    recorder = Recorder()
    monkeypatch.setattr(oauth.httpx, "post", recorder)

    return recorder


def query_of(url):
    return parse_qs(urlparse(url).query)


def test_authorize_url_points_at_discord(flow):
    assert flow.authorize_url().startswith(AUTHORIZE_URL)


def test_authorize_url_carries_the_client_and_redirect(flow):
    query = query_of(flow.authorize_url())

    assert query["client_id"] == [CLIENT_ID]
    assert query["redirect_uri"] == [REDIRECT_URI]
    assert query["response_type"] == ["code"]


def test_authorize_url_joins_the_scopes(flow):
    assert query_of(flow.authorize_url(("identify", "rpc")))["scope"] == ["identify rpc"]


def test_authorize_url_falls_back_to_the_default_scopes(flow):
    assert query_of(flow.authorize_url(()))["scope"] == ["identify rpc"]


def test_authorize_url_includes_the_state(flow):
    assert query_of(flow.authorize_url(state="xyz"))["state"] == ["xyz"]


def test_authorize_url_omits_an_empty_state(flow):
    assert "state" not in query_of(flow.authorize_url())


def test_authorize_url_needs_a_client_id():
    with pytest.raises(AuthError):
        OAuthFlow("", CLIENT_SECRET, REDIRECT_URI).authorize_url()


def test_new_state_is_random():
    assert new_state() != new_state()


def test_extract_code_accepts_a_bare_code():
    assert extract_code(f"  {CODE}  ") == CODE


def test_extract_code_reads_a_redirect_url():
    assert extract_code(f"{REDIRECT_URI}?code={CODE}&state=xyz", "xyz") == CODE


def test_extract_code_reads_a_query_fragment():
    assert extract_code(f"?code={CODE}") == CODE


def test_extract_code_rejects_a_mismatched_state():
    with pytest.raises(AuthError):
        extract_code(f"{REDIRECT_URI}?code={CODE}&state=other", "xyz")


def test_extract_code_reports_a_refusal():
    with pytest.raises(AuthError):
        extract_code(f"{REDIRECT_URI}?error=access_denied&error_description=nope")


def test_extract_code_rejects_a_url_without_a_code():
    with pytest.raises(AuthError):
        extract_code(f"{REDIRECT_URI}?state=xyz")


@pytest.mark.parametrize("answer", ["", "   "])
def test_extract_code_rejects_nothing(answer):
    with pytest.raises(AuthError):
        extract_code(answer)


def test_exchange_posts_to_the_token_endpoint(flow, post):
    flow.exchange(CODE)

    assert post.calls[-1][0] == TOKEN_URL
    assert post.data["grant_type"] == "authorization_code"
    assert post.data["code"] == CODE
    assert post.data["redirect_uri"] == REDIRECT_URI
    assert post.data["client_id"] == CLIENT_ID
    assert post.data["client_secret"] == CLIENT_SECRET


@pytest.mark.usefixtures("post")
def test_exchange_returns_a_token(flow):
    token = flow.exchange(CODE)

    assert token.kind is TokenKind.OAUTH
    assert token.access_token == ACCESS
    assert token.refresh_token == REFRESH
    assert token.scopes == ["identify", "rpc"]
    assert token.expires_at is not None


@pytest.mark.usefixtures("post")
def test_exchange_needs_a_client_secret():
    with pytest.raises(AuthError):
        OAuthFlow(CLIENT_ID, "", REDIRECT_URI).exchange(CODE)


def test_refresh_posts_the_refresh_token(flow, post):
    flow.refresh(Token(refresh_token=REFRESH))

    assert post.data["grant_type"] == "refresh_token"
    assert post.data["refresh_token"] == REFRESH


@pytest.mark.usefixtures("post")
def test_refresh_needs_a_refresh_token(flow):
    with pytest.raises(AuthError):
        flow.refresh(Token(access_token=ACCESS))


def test_refresh_keeps_the_old_refresh_token(flow, monkeypatch):
    monkeypatch.setattr(oauth.httpx, "post", Recorder(payload={"access_token": ACCESS}))

    refreshed = flow.refresh(Token(refresh_token=REFRESH, scopes=["identify"]))

    assert refreshed.refresh_token == REFRESH
    assert refreshed.scopes == ["identify"]


def test_revoke_posts_the_access_token(flow, post):
    flow.revoke(Token(access_token=ACCESS))

    assert post.calls[-1][0] == REVOKE_URL
    assert post.data["token"] == ACCESS


def test_revoke_ignores_an_empty_token(flow, post):
    flow.revoke(Token())

    assert post.calls == []


def test_a_rejected_request_becomes_an_auth_error(flow, monkeypatch):
    rejection = Recorder(status=400, payload={"error": "invalid_grant"})
    monkeypatch.setattr(oauth.httpx, "post", rejection)

    with pytest.raises(AuthError, match="400"):
        flow.exchange(CODE)


def test_a_rejected_request_does_not_leak_the_code(flow, monkeypatch):
    body = f'{{"error": "invalid_grant", "code": "{CODE}"}}'
    monkeypatch.setattr(oauth.httpx, "post", Recorder(status=400, text=body))

    with pytest.raises(AuthError) as caught:
        flow.exchange(CODE)

    assert CODE not in str(caught.value)


def test_a_network_failure_becomes_an_auth_error(flow, monkeypatch):
    def explode(_url, **_kwargs):
        message = "connection refused"

        raise httpx.ConnectError(message)

    monkeypatch.setattr(oauth.httpx, "post", explode)

    with pytest.raises(AuthError, match="Could not reach Discord"):
        flow.exchange(CODE)


def test_a_non_json_response_becomes_an_auth_error(flow, monkeypatch):
    monkeypatch.setattr(oauth.httpx, "post", Recorder(text="<html>nope</html>"))

    with pytest.raises(AuthError):
        flow.exchange(CODE)


@pytest.mark.usefixtures("post")
def test_an_expiring_token_knows_when_it_expires(flow):
    before = datetime.now(UTC)
    token = flow.exchange(CODE)

    assert token.expires_at is not None
    assert token.expires_at >= before + timedelta(days=7) - timedelta(seconds=5)
