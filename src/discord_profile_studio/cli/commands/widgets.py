import json
from pathlib import Path

import typer
from rich.markup import escape

from discord_profile_studio.auth.store import TokenStore
from discord_profile_studio.auth.token import Token, TokenKind
from discord_profile_studio.cli.commands.auth import unlocked_store
from discord_profile_studio.cli.console import console, fail, success, table
from discord_profile_studio.cli.options import BACKEND
from discord_profile_studio.core.exceptions import StudioError, TokenNotFoundError
from discord_profile_studio.core.paths import favourites_file
from discord_profile_studio.models.favourite import Favourite
from discord_profile_studio.models.widget import Widget, WidgetField
from discord_profile_studio.storage.repository import FavouriteRepository
from discord_profile_studio.widgets.api import WidgetApi, authorize_url
from discord_profile_studio.widgets.spec import from_payload, problems

app = typer.Typer(no_args_is_help=True)


def _account(application_id: str) -> str:
    return f"widget:{application_id}"


def _api(store: TokenStore, application_id: str) -> WidgetApi:
    try:
        return WidgetApi(store.get(_account(application_id)))
    except TokenNotFoundError:
        fail(f"no bot token for application {application_id}, store one with: dps widget token")


def _widget(favourite: Favourite, application_id: str) -> Widget:
    widget = next((w for w in favourite.widgets if w.application_id == application_id), None)

    if widget is None:
        fail(f"{favourite.name!r} has no widget for application {application_id}")

    return widget


def _sample(path: Path) -> list[WidgetField]:
    try:
        data: object = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        fail(f"{path}: not valid JSON: {e}")

    return from_payload(data)


@app.command()
def token(backend: str | None = BACKEND) -> None:
    secret = typer.prompt("Bot token of the widget's application", hide_input=True).strip()
    bot = Token(kind=TokenKind.BOT, access_token=secret)

    try:
        application = WidgetApi(bot).application()
        store = unlocked_store(backend)

        store.set(_account(application.id), bot)
    except StudioError as e:
        fail(str(e))

    success(f"Stored the bot token for {application.name} ({application.id}) in {store.name}")
    console.print("If you have not yet, authorize the app for your account once:")
    console.print(authorize_url(application.id), soft_wrap=True)


@app.command()
def show(application_id: str, backend: str | None = BACKEND) -> None:
    try:
        config = _api(unlocked_store(backend), application_id).config(application_id)
    except StudioError as e:
        fail(str(e))

    if config.draft:
        console.print("This widget config is a draft, only the app's developers can see it")

    if not config.fields:
        console.print("The widget shows no user data, there is nothing to fill in")
        return

    listing = table(f"User data of {application_id}", ["Name", "Type"])

    for name, kind in config.fields.items():
        listing.add_row(escape(name), kind.name.lower())

    console.print(listing)


@app.command()
def add(
    favourite: str,
    application_id: str,
    sample: Path | None = typer.Option(None, "--sample"),
    backend: str | None = BACKEND,
) -> None:
    repository = FavouriteRepository(favourites_file())

    try:
        stored = repository.get(favourite)
        api = _api(unlocked_store(backend), application_id)
        wanted = api.config(application_id).fields
        current = next((w for w in stored.widgets if w.application_id == application_id), None)

        # Re-adding refreshes the fields from the live config and keeps values that still fit
        known = {field.name: field for field in current.fields} if current else {}

        if sample is not None:
            known |= {field.name: field for field in _sample(sample)}

        fields = [
            known[name] if name in known and known[name].kind is kind else WidgetField(name, kind)
            for name, kind in wanted.items()
        ]
        widget = Widget(application_id, api.application().name, fields)

        if current is None:
            stored.widgets.append(widget)
        else:
            stored.widgets[stored.widgets.index(current)] = widget

        repository.update(stored)
    except (StudioError, OSError) as e:
        fail(str(e))

    success(f"{'Updated' if current else 'Added'} {widget.name} on {favourite!r}")

    for problem in problems(widget.fields, wanted):
        console.print(f"  {escape(problem)}")


@app.command("set")
def set_(favourite: str, application_id: str, name: str, value: str) -> None:
    repository = FavouriteRepository(favourites_file())

    try:
        stored = repository.get(favourite)
        widget = _widget(stored, application_id)
        field = next((field for field in widget.fields if field.name == name), None)

        if field is None:
            names = ", ".join(field.name for field in widget.fields) or "none"
            fail(f"{widget.name} has no field {name!r}, it has: {names}")

        issues = problems([WidgetField(name, field.kind, value)], {name: field.kind})

        if issues:
            fail(issues[0])

        field.value = value
        repository.update(stored)
    except StudioError as e:
        fail(str(e))

    success(f"Set {name!r} on {widget.name}")


@app.command()
def remove(favourite: str, application_id: str) -> None:
    repository = FavouriteRepository(favourites_file())

    try:
        stored = repository.get(favourite)
        stored.widgets.remove(_widget(stored, application_id))
        repository.update(stored)
    except StudioError as e:
        fail(str(e))

    success(f"Removed the widget for {application_id} from {favourite!r}")


@app.command()
def push(favourite: str, backend: str | None = BACKEND) -> None:
    try:
        stored = FavouriteRepository(favourites_file()).get(favourite)

        if not stored.widgets:
            fail(f"{favourite!r} has no widgets, add one with: dps widget add")

        store = unlocked_store(backend)
        ready: list[tuple[Widget, WidgetApi, list[WidgetField]]] = []
        issues: list[str] = []

        # Check every widget before sending any, so a favourite never goes out half applied
        for widget in stored.widgets:
            api = _api(store, widget.application_id)
            wanted = api.config(widget.application_id).fields

            issues += [f"{widget.name}: {problem}" for problem in problems(widget.fields, wanted)]
            ready.append((widget, api, [field for field in widget.fields if field.name in wanted]))

        if issues:
            fail("not pushed, fix these first:\n" + "\n".join(issues))

        for widget, api, fields in ready:
            api.push(widget.application_id, api.application().owner_id, fields)
            success(f"Pushed {widget.name}")
    except StudioError as e:
        fail(str(e))
