import json
from pathlib import Path

import httpx
import pytest
from typer.testing import CliRunner, Result

from discord_profile_studio.auth.token import TokenKind
from discord_profile_studio.cli import app
from discord_profile_studio.cli.commands import widgets as widgets_cli
from discord_profile_studio.models import Favourite, FieldType, Widget, WidgetField
from discord_profile_studio.storage.repository import FavouriteRepository
from discord_profile_studio.widgets.api import API, token_account
from tests.conftest import WIDGET_APP, FakeDiscord, MemoryStore

ACCOUNT = token_account(WIDGET_APP)

runner = CliRunner()


@pytest.fixture(autouse=True)
def repository(store: Path, monkeypatch: pytest.MonkeyPatch) -> FavouriteRepository:
    monkeypatch.setattr(widgets_cli, "favourites_file", lambda: store)
    repository = FavouriteRepository(store)
    repository.add(Favourite(name="Coding"))
    return repository


@pytest.fixture(autouse=True)
def tokens(monkeypatch: pytest.MonkeyPatch) -> MemoryStore:
    tokens = MemoryStore()
    monkeypatch.setattr(widgets_cli, "unlocked_store", lambda _backend: tokens)  # pyright: ignore[reportUnknownLambdaType]
    return tokens


def dps(*args: str, prompt: str | None = None) -> Result:
    return runner.invoke(app, ["widget", *args], input=prompt)


def with_widget(repository: FavouriteRepository, **values: str) -> None:
    kinds = {"rank": FieldType.TEXT, "level": FieldType.NUMBER, "cover": FieldType.IMAGE}
    fields = [WidgetField(name, kind, values.get(name, "")) for name, kind in kinds.items()]
    favourite = repository.get("Coding")
    favourite.widgets = [Widget(WIDGET_APP, "Stats", fields)]
    repository.update(favourite)


def values(repository: FavouriteRepository) -> dict[str, str]:
    return {field.name: field.value for field in repository.get("Coding").widgets[0].fields}


def test_token_is_checked_with_discord_then_stored(tokens: MemoryStore, discord: FakeDiscord):
    tokens.tokens.clear()

    result = dps("token", prompt="  fresh-token  \n")

    assert result.exit_code == 0, result.output
    assert tokens.tokens[ACCOUNT].access_token == "fresh-token"
    assert tokens.tokens[ACCOUNT].kind is TokenKind.BOT
    assert discord.calls[0][2]["Authorization"] == "Bot fresh-token"
    assert "sdk.social_layer_presence" in result.output


def test_token_that_discord_rejects_is_not_stored(tokens: MemoryStore, discord: FakeDiscord):
    tokens.tokens.clear()
    discord.routes["GET", f"{API}/oauth2/applications/@me"] = httpx.Response(
        401,
        json={"code": 0, "message": "401: Unauthorized"},
    )

    result = dps("token", prompt="wrong\n")

    assert result.exit_code == 1
    assert "401: Unauthorized" in result.output
    assert tokens.tokens == {}


@pytest.mark.usefixtures("discord")
def test_commands_without_a_stored_token_say_how_to_add_one(tokens: MemoryStore):
    tokens.tokens.clear()

    result = dps("show", WIDGET_APP)

    assert result.exit_code == 1
    assert "dps widget token" in result.output


@pytest.mark.usefixtures("discord")
def test_show_lists_the_user_data_and_warns_about_a_draft():
    result = dps("show", WIDGET_APP)

    assert result.exit_code == 0, result.output
    assert "draft" in result.output
    for name in ("rank", "level", "cover"):
        assert name in result.output


@pytest.mark.usefixtures("discord")
def test_add_takes_the_fields_from_the_live_config(repository: FavouriteRepository):
    result = dps("add", "Coding", WIDGET_APP)

    assert result.exit_code == 0, result.output
    widget = repository.get("Coding").widgets[0]
    assert (widget.application_id, widget.name) == (WIDGET_APP, "Stats")
    assert [(field.name, field.kind) for field in widget.fields] == [
        ("rank", FieldType.TEXT),
        ("level", FieldType.NUMBER),
        ("cover", FieldType.IMAGE),
    ]
    assert "level: no value yet" in result.output


@pytest.mark.usefixtures("discord")
def test_add_with_a_sample_fills_the_values_that_fit(
    repository: FavouriteRepository,
    tmp_path: Path,
):
    sample = tmp_path / "sample.json"
    entries = [
        {"name": "rank", "type": 1, "value": "Gold"},
        {"name": "level", "type": 1, "value": "wrong type"},
        {"name": "extra", "type": 1, "value": "not in the config"},
    ]
    sample.write_text(json.dumps({"data": {"dynamic": entries}}))

    result = dps("add", "Coding", WIDGET_APP, "--sample", str(sample))

    assert result.exit_code == 0, result.output
    assert values(repository) == {"rank": "Gold", "level": "", "cover": ""}


@pytest.mark.usefixtures("discord")
def test_adding_again_keeps_values_that_still_fit(repository: FavouriteRepository):
    with_widget(repository, rank="Gold", level="7")

    result = dps("add", "Coding", WIDGET_APP)

    assert result.exit_code == 0, result.output
    assert "Updated" in result.output
    assert values(repository) == {"rank": "Gold", "level": "7", "cover": ""}
    assert len(repository.get("Coding").widgets) == 1


def test_set_checks_the_value_against_the_field_type(repository: FavouriteRepository):
    with_widget(repository)

    refused = dps("set", "Coding", WIDGET_APP, "level", "lots")
    accepted = dps("set", "Coding", WIDGET_APP, "level", "12")

    assert refused.exit_code == 1
    assert "expected a number" in refused.output
    assert accepted.exit_code == 0, accepted.output
    assert values(repository)["level"] == "12"


def test_set_of_an_unknown_field_lists_the_real_ones(repository: FavouriteRepository):
    with_widget(repository)

    result = dps("set", "Coding", WIDGET_APP, "lvl", "12")

    assert result.exit_code == 1
    assert "has no field 'lvl', it has: rank, level, cover" in result.output


def test_push_sends_nothing_while_a_value_is_missing(
    repository: FavouriteRepository,
    discord: FakeDiscord,
):
    with_widget(repository, rank="Gold")

    result = dps("push", "Coding")

    assert result.exit_code == 1
    assert "Stats: level: no value yet" in result.output
    assert all(method != "PATCH" for method, *_ in discord.calls)


def test_push_sends_the_values_to_the_owners_identity(
    repository: FavouriteRepository,
    discord: FakeDiscord,
):
    with_widget(repository, rank="Gold", level="7", cover="https://example.com/a.png")

    result = dps("push", "Coding")

    assert result.exit_code == 0, result.output
    patches = [payload for method, _, _, payload in discord.calls if method == "PATCH"]
    assert patches == [
        {
            "data": {
                "dynamic": [
                    {"name": "rank", "type": 1, "value": "Gold"},
                    {"name": "level", "type": 2, "value": 7},
                    {"name": "cover", "type": 3, "value": {"url": "https://example.com/a.png"}},
                ],
            },
        },
    ]


def test_remove_drops_the_widget(repository: FavouriteRepository):
    with_widget(repository)

    result = dps("remove", "Coding", WIDGET_APP)

    assert result.exit_code == 0, result.output
    assert repository.get("Coding").widgets == []
