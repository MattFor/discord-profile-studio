import secrets
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

from discord_profile_studio.auth.redaction import scrub
from discord_profile_studio.auth.token import Token, TokenKind
from discord_profile_studio.core.exceptions import AuthError
from discord_profile_studio.core.logging import get

DEFAULT_SCOPES = ("identify", "rpc")
TOKEN_URL = "https://discord.com/api/oauth2/token"
AUTHORIZE_URL = "https://discord.com/oauth2/authorize"
REVOKE_URL = "https://discord.com/api/oauth2/token/revoke"
DEFAULT_REDIRECT_URI = "http://127.0.0.1:6420/callback"
TIMEOUT = 15.0
STATE_BYTES = 16

log = get(__name__)


def new_state() -> str:
    return secrets.token_urlsafe(STATE_BYTES)


def extract_code(response: str, state: str | None = None) -> str:
    '''
    Prase the url and get the correct extraction code

    f.e discord redirects to local callback : http://127.0.0.1:6420/callback?code=ABC123&state=XYZ789

    then query = parse_qs(urlparse(value).query or value.lstrip("?"))
    turns that into

    {
        "code": ["ABC123"],
        "state": ["XYZ789"],
    }

    from which code = query.get("code", [""])[0]
    gets

    ABC123

    Also protects against CSRF
    '''

    value = response.strip()

    if not value:
        msg = "No authorisation code was given"
        raise AuthError(msg)

    if "?" not in value and "&" not in value:
        return value

    query = parse_qs(urlparse(value).query or value.lstrip("?"))
    error = query.get("error", [""])[0]

    if error:
        description = query.get("error_description", [""])[0]
        msg = f"Discord refused the authorisation: {error} {description}".strip(
        )
        raise AuthError(msg)

    code = query.get("code", [""])[0]

    if not code:
        msg = "The redirect URL does not contain an authorisation code"
        raise AuthError(msg)

    if state is not None and query.get("state", [""])[0] != state:
        msg = "The redirect URL carries a different state, start the sign in again"
        raise AuthError(msg)

    return code


class OAuthFlow:

    def __init__(self, client_id: str, client_secret: str,
                 redirect_uri: str) -> None:
        self.client_id: str = client_id
        self.client_secret: str = client_secret
        self.redirect_uri: str = redirect_uri

    def authorize_url(
        self,
        scopes: tuple[str, ...] = DEFAULT_SCOPES,
        state: str | None = None,
    ) -> str:
        if not self.client_id:
            msg = "A client id is required to build the authorisation URL"
            raise AuthError(msg)

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes or DEFAULT_SCOPES),
        }

        if state:
            params["state"] = state

        return f"{AUTHORIZE_URL}?{urlencode(params)}"

    def _post(self, url: str, data: dict[str, str]) -> httpx.Response:
        if not self.client_id or not self.client_secret:
            msg = "Both a client id and a client secret are required to talk to Discord"
            raise AuthError(msg)

        payload = {
            **data,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        try:
            response = httpx.post(
                url,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=TIMEOUT,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            msg = f"Discord rejected the request: {e.response.status_code} {scrub(e.response.text)}"
            raise AuthError(msg) from e
        except httpx.HTTPError as e:
            msg = f"Could not reach Discord: {scrub(str(e))}"
            raise AuthError(msg) from e

        return response

    def _token(self, data: dict[str, str]) -> Token:
        response = self._post(TOKEN_URL, data)

        try:
            payload: Any = response.json()
        except ValueError as e:
            msg = "Discord returned a response that is not valid JSON"
            raise AuthError(msg) from e

        return Token.from_response(payload, kind=TokenKind.OAUTH)

    def exchange(self, code: str) -> Token:
        log.info("exchanging the authorisation code for a token")

        return self._token({
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        })

    def refresh(self, token: Token) -> Token:
        if not token.refresh_token:
            msg = "The stored token cannot be refreshed, sign in again"
            raise AuthError(msg)

        log.info("refreshing the access token")

        refreshed = self._token({
            "grant_type": "refresh_token",
            "refresh_token": token.refresh_token,
        })

        if not refreshed.refresh_token:
            refreshed.refresh_token = token.refresh_token

        if not refreshed.scopes:
            refreshed.scopes = token.scopes

        return refreshed

    def revoke(self, token: Token) -> None:
        if not token.access_token:
            return

        log.info("revoking the access token")

        self._post(REVOKE_URL, {
            "token": token.access_token,
            "token_type_hint": "access_token"
        })
