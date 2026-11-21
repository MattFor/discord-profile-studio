from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, cast
from urllib.parse import urlencode

import httpx

from discord_profile_studio import __version__
from discord_profile_studio.auth.redaction import scrub
from discord_profile_studio.auth.token import Token
from discord_profile_studio.core.exceptions import WidgetError
from discord_profile_studio.models.widget import Widget, WidgetField
from discord_profile_studio.widgets.spec import Spec, problems, spec, to_payload

API = "https://discord.com/api/v10"
# The identity endpoint has only been seen working on v9
IDENTITY_API = "https://discord.com/api/v9"
AUTHORIZE_URL = "https://discord.com/oauth2/authorize"
PORTAL_URL = "https://discord.com/developers/applications"
USER_AGENT = f"DiscordBot (https://github.com/MattFor/discord-profile-studio, {__version__})"
TIMEOUT = 15.0
IDENTITY_SCOPE = "sdk.social_layer_presence"
NOT_AUTHORIZED = 50025


def token_account(application_id: str) -> str:
    return f"widget:{application_id}"


def authorize_url(application_id: str) -> str:
    query = {"client_id": application_id, "response_type": "token", "scope": IDENTITY_SCOPE}

    return f"{AUTHORIZE_URL}?{urlencode(query)}"


@dataclass(slots=True, frozen=True)
class Application:
    id: str
    name: str
    # Whose profile the widget lands on, the team owner for team apps
    owner_id: str


@dataclass(slots=True, frozen=True)
class WidgetConfig:
    id: str
    status: str
    fields: Spec

    @property
    def draft(self) -> bool:
        return self.status == "draft"


class WidgetApi:
    def __init__(self, token: Token) -> None:
        self._headers = {"Authorization": token.header, "User-Agent": USER_AGENT}

    def application(self) -> Application:
        data = _object(self._request("GET", f"{API}/oauth2/applications/@me"), "application")
        team, owner = data.get("team"), data.get("owner")

        if type(team) is dict:
            owner_id = cast("dict[str, object]", team).get("owner_user_id")
        else:
            owner_id = cast("dict[str, object]", owner).get("id") if type(owner) is dict else None

        return Application(
            id=_text(data.get("id"), "application.id"),
            name=_text(data.get("name"), "application.name"),
            owner_id=_text(owner_id, "application owner id"),
        )

    def config(self, application_id: str) -> WidgetConfig:
        data = self._request("GET", f"{API}/applications/{application_id}/widget-configs")
        # ponytail: unknown whether this returns one config or a list; one app holds one widget
        configs = cast("list[object]", data) if type(data) is list else [data]

        if not configs or type(configs[0]) is not dict:
            msg = f"no widget config yet, create one at {PORTAL_URL}/{application_id}"
            raise WidgetError(msg)

        config = cast("dict[str, object]", configs[0])

        return WidgetConfig(
            id=str(config.get("config_id", "")),
            status=str(config.get("status", "")),
            fields=spec(config),
        )

    def push(self, application_id: str, user_id: str, fields: list[WidgetField]) -> None:
        url = f"{IDENTITY_API}/applications/{application_id}/users/{user_id}/identities/0/profile"
        hint = (
            "the app is not authorized for your account yet, finish its Social SDK form in the "
            f"Developer Portal, then open {authorize_url(application_id)}"
        )

        self._request("PATCH", url, payload=to_payload(fields), hints={NOT_AUTHORIZED: hint})

    def _request(
        self,
        method: str,
        url: str,
        payload: object = None,
        hints: Mapping[int, str] | None = None,
    ) -> object:
        try:
            response = httpx.request(
                method,
                url,
                headers=self._headers,
                json=payload,
                timeout=TIMEOUT,
            )
        except httpx.HTTPError as e:
            msg = f"could not reach Discord: {scrub(str(e))}"
            raise WidgetError(msg) from e

        if response.is_error:
            raise WidgetError(_explain(response, hints or {}))

        if not response.content:
            return None

        try:
            return cast("object", response.json())
        except ValueError as e:
            msg = "Discord returned a response that is not JSON"
            raise WidgetError(msg) from e


def push_all(widgets: list[Widget], api_for: Callable[[str], WidgetApi]) -> None:
    ready: list[tuple[Widget, WidgetApi, list[WidgetField]]] = []
    issues: list[str] = []

    # Check every widget before sending any, so a favourite never goes out half applied
    for widget in widgets:
        api = api_for(widget.application_id)
        wanted = api.config(widget.application_id).fields

        issues += [f"{widget.name}: {problem}" for problem in problems(widget.fields, wanted)]
        ready.append((widget, api, [field for field in widget.fields if field.name in wanted]))

    if issues:
        msg = "not pushed, fix these first:\n" + "\n".join(issues)
        raise WidgetError(msg)

    for widget, api, fields in ready:
        api.push(widget.application_id, api.application().owner_id, fields)


def _explain(response: httpx.Response, hints: Mapping[int, str]) -> str:
    try:
        body: Any = response.json()
    except ValueError:
        body = None

    if type(body) is not dict:
        return f"Discord rejected the request: {response.status_code} {scrub(response.text)}"

    error = cast("dict[str, Any]", body)
    text = (
        f"Discord rejected the request: {response.status_code} {scrub(str(error.get('message')))}"
    )

    # Field-level reasons for a rejected body, e.g. which dynamic value was wrong
    reasons = _reasons(error.get("errors"))

    if reasons:
        text += f" ({'; '.join(reasons)})"

    code = error.get("code")
    hint = hints.get(code) if type(code) is int else None

    return f"{text}, {hint}" if hint else text


def _reasons(errors: object, path: str = "") -> list[str]:
    if type(errors) is not dict:
        return []

    found: list[str] = []

    for key, value in cast("dict[str, object]", errors).items():
        if key == "_errors" and type(value) is list:
            found += [
                f"{path}: {scrub(str(cast('dict[str, object]', entry).get('message')))}"
                for entry in cast("list[object]", value)
                if type(entry) is dict
            ]
        else:
            found += _reasons(value, f"{path}.{key}" if path else key)

    return found


def _object(data: object, where: str) -> dict[str, object]:
    if type(data) is not dict:
        msg = f"{where}: Discord returned something that is not an object"
        raise WidgetError(msg)

    return cast("dict[str, object]", data)


def _text(value: object, where: str) -> str:
    if type(value) is not str or not value:
        msg = f"{where}: missing from Discord's response"
        raise WidgetError(msg)

    return value
