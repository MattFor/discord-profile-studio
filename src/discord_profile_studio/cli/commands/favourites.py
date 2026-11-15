from pathlib import Path

import typer
from rich.markup import escape

from discord_profile_studio.cli.console import console, fail, success, table
from discord_profile_studio.cli.options import (
    CLIENT_ID,
    DETAILS,
    LARGE_IMAGE,
    SMALL_IMAGE,
    STATE,
)
from discord_profile_studio.core.exceptions import FavouriteNotFoundError, StudioError
from discord_profile_studio.core.paths import favourites_file
from discord_profile_studio.importers.customrp import load_all, load_preset, load_settings
from discord_profile_studio.models.favourite import Favourite
from discord_profile_studio.storage.document import free_name, from_text, to_text
from discord_profile_studio.storage.repository import FavouriteRepository
from discord_profile_studio.storage.serializers import favourite_to_dict

app = typer.Typer(no_args_is_help=True)


def _customrp(path: Path) -> list[Favourite]:
    if path.is_dir():
        return load_all(path)

    if path.suffix.lower() == ".crp":
        return [load_preset(path)]

    return [load_settings(path)]


def _dps(path: Path) -> list[Favourite]:
    return from_text(path.read_text(encoding="utf-8-sig"))


IMPORTERS = {"customrp": _customrp, "dps": _dps}


@app.command("list")
def list_favourites() -> None:
    try:
        favourites = FavouriteRepository(favourites_file()).all()
    except StudioError as e:
        fail(str(e))

    if not favourites:
        console.print("No favourites saved yet")
        return

    listing = table("Favourites", ["Name", "Details", "State", "Tags", "Updated"])

    for favourite in favourites:
        cells = (
            favourite.name,
            favourite.presence.details,
            favourite.presence.state,
            ", ".join(favourite.tags),
            favourite.updated_at.astimezone().strftime("%Y-%m-%d %H:%M"),
        )

        listing.add_row(*map(escape, cells))

    console.print(listing)


@app.command()
def show(name: str) -> None:
    try:
        favourite = FavouriteRepository(favourites_file()).get(name)
    except StudioError as e:
        fail(str(e))

    console.print_json(data=favourite_to_dict(favourite))


@app.command()
def save(
    name: str,
    client_id: str | None = CLIENT_ID,
    details: str | None = DETAILS,
    state: str | None = STATE,
    large_image: str | None = LARGE_IMAGE,
    small_image: str | None = SMALL_IMAGE,
) -> None:
    repository = FavouriteRepository(favourites_file())

    try:
        try:
            favourite = repository.get(name)
            store = repository.update
        except FavouriteNotFoundError:
            favourite = Favourite(name=name)
            store = repository.add

        # Options left out keep the stored value
        presence = favourite.presence

        if client_id is not None:
            presence.client_id = client_id

        if details is not None:
            presence.details = details

        if state is not None:
            presence.state = state

        if large_image is not None:
            presence.large_image.key = large_image

        if small_image is not None:
            presence.small_image.key = small_image

        store(favourite)
    except StudioError as e:
        fail(str(e))

    success(f"Saved {name!r}")


@app.command()
def delete(name: str) -> None:
    try:
        FavouriteRepository(favourites_file()).delete(name)
    except StudioError as e:
        fail(str(e))

    success(f"Deleted {name!r}")


@app.command("import")
def import_(path: Path, source: str = "customrp") -> None:
    read = IMPORTERS.get(source)

    if read is None:
        fail(f"unknown source {source!r}, expected one of: {', '.join(IMPORTERS)}")

    repository = FavouriteRepository(favourites_file())

    try:
        favourites = read(path)

        if not favourites:
            fail(f"no favourites found in {path}")

        taken = {favourite.name for favourite in repository.all()}

        for favourite in favourites:
            favourite.name = free_name(favourite.name, taken)
            taken.add(favourite.name)

            repository.add(favourite)
            success(f"Imported {favourite.name!r}")
    except (StudioError, OSError) as e:
        fail(str(e))


@app.command("export")
def export(
    name: str,
    path: Path,
    force: bool = typer.Option(False, "--force", "-f"),
) -> None:
    try:
        text = to_text([FavouriteRepository(favourites_file()).get(name)])

        with path.open("w" if force else "x", encoding="utf-8", newline="\n") as file:
            file.write(text)
    except FileExistsError:
        fail(f"{path} already exists, pass --force to overwrite it")
    except (StudioError, OSError) as e:
        fail(str(e))

    success(f"Exported {name!r} to {path}")
