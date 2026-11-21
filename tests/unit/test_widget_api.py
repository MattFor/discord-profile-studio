from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from discord_profile_studio.auth.token import Token, TokenKind
from discord_profile_studio.core.exceptions import WidgetError
from discord_profile_studio.models import FieldType, WidgetField
from discord_profile_studio.widgets.api import (
    API,
    IDENTITY_API,
    PORTAL_URL,
    Application,
    WidgetApi,
    authorize_url,
)
from tests.conftest import WIDGET_APP, WIDGET_OWNER, FakeDiscord

SECRET = "bot-secret-token"
ME = ("GET", f"{API}/oauth2/applications/@me")
CONFIGS = ("GET", f"{API}/applications/{WIDGET_APP}/widget-configs")
IDENTITY = (
    "PATCH",
    f"{IDENTITY_API}/applications/{WIDGET_APP}/users/{WIDGET_OWNER}/identities/0/profile",
)


@pytest.fixture
def api() -> WidgetApi:
    return WidgetApi(Token(kind=TokenKind.BOT, access_token=SECRET))


def test_application_sends_the_bot_token_and_a_discordbot_user_agent(
    api: WidgetApi,
    discord: FakeDiscord,
):
    assert api.application() == Application(id=WIDGET_APP, name="Stats", owner_id=WIDGET_OWNER)

    headers = discord.calls[0][2]
    assert headers["Authorization"] == f"Bot {SECRET}"
    assert headers["User-Agent"].startswith("DiscordBot (https://")


def test_application_of_a_team_app_lands_on_the_team_owner(api: WidgetApi, discord: FakeDiscord):
    discord.routes[ME] = httpx.Response(
        200,
        json={
            "id": WIDGET_APP,
            "name": "Stats",
            "owner": {"id": "7"},
            "team": {"owner_user_id": "8"},
        },
    )

    assert api.application().owner_id == "8"


def test_application_without_an_id_raises(api: WidgetApi, discord: FakeDiscord):
    discord.routes[ME] = httpx.Response(200, json={"name": "Stats", "owner": {"id": "7"}})

    with pytest.raises(WidgetError, match=r"application\.id: missing"):
        api.application()


def test_config_reads_status_and_user_data_fields(api: WidgetApi, discord: FakeDiscord):
    config = api.config(WIDGET_APP)

    assert (config.id, config.draft) == ("99", True)
    assert config.fields == {
        "rank": FieldType.TEXT,
        "level": FieldType.NUMBER,
        "cover": FieldType.IMAGE,
    }
    assert discord.calls[0][:2] == CONFIGS


def test_config_accepts_a_single_object(api: WidgetApi, discord: FakeDiscord):
    discord.routes[CONFIGS] = httpx.Response(200, json={"config_id": "5", "status": "published"})

    config = api.config(WIDGET_APP)

    assert (config.id, config.draft, config.fields) == ("5", False, {})


def test_missing_config_points_at_the_developer_portal(api: WidgetApi, discord: FakeDiscord):
    discord.routes[CONFIGS] = httpx.Response(200, json=[])

    with pytest.raises(WidgetError, match=f"{PORTAL_URL}/{WIDGET_APP}"):
        api.config(WIDGET_APP)


def test_push_patches_the_identity_profile_with_the_payload(api: WidgetApi, discord: FakeDiscord):
    api.push(WIDGET_APP, WIDGET_OWNER, [WidgetField("level", FieldType.NUMBER, "42")])

    assert discord.calls[0][:2] == IDENTITY
    assert discord.calls[0][3] == {"data": {"dynamic": [{"name": "level", "type": 2, "value": 42}]}}


def test_push_to_an_unauthorized_app_says_how_to_authorize(api: WidgetApi, discord: FakeDiscord):
    discord.routes[IDENTITY] = httpx.Response(
        401,
        json={"code": 50025, "message": "Invalid OAuth2 access token"},
    )

    with pytest.raises(WidgetError) as caught:
        api.push(WIDGET_APP, WIDGET_OWNER, [])

    assert "Invalid OAuth2 access token" in str(caught.value)
    assert authorize_url(WIDGET_APP) in str(caught.value)


def test_rejected_body_shows_discords_field_errors(api: WidgetApi, discord: FakeDiscord):
    reason = {"code": "BASE_TYPE_REQUIRED", "message": "This field is required"}
    errors = {"data": {"dynamic": {"0": {"value": {"_errors": [reason]}}}}}
    discord.routes[IDENTITY] = httpx.Response(
        400,
        json={"code": 50035, "message": "Invalid Form Body", "errors": errors},
    )

    with pytest.raises(WidgetError) as caught:
        api.push(WIDGET_APP, WIDGET_OWNER, [])

    assert str(caught.value) == (
        "Discord rejected the request: 400 Invalid Form Body "
        "(data.dynamic.0.value: This field is required)"
    )


def test_network_errors_never_echo_the_token(api: WidgetApi, discord: FakeDiscord):
    discord.routes[ME] = httpx.ConnectError(f"refused, Authorization: Bot {SECRET}")

    with pytest.raises(WidgetError, match="could not reach Discord") as caught:
        api.application()

    assert SECRET not in str(caught.value)


def test_authorize_url_asks_for_the_identity_scope_with_the_implicit_grant():
    query = parse_qs(urlparse(authorize_url(WIDGET_APP)).query)

    assert query == {
        "client_id": [WIDGET_APP],
        "response_type": ["token"],
        "scope": ["sdk.social_layer_presence"],
    }
