import json
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner, Result

from discord_profile_studio.cli import app
from discord_profile_studio.cli.commands import favourites as favourites_cli
from discord_profile_studio.storage.repository import FavouriteRepository

CUSTOMRP = Path(__file__).parent.parent / "fixtures" / "customrp"

runner = CliRunner()


@pytest.fixture(autouse=True)
def repository(store: Path, monkeypatch: pytest.MonkeyPatch) -> FavouriteRepository:
    monkeypatch.setattr(favourites_cli, "favourites_file", lambda: store)
    return FavouriteRepository(store)


def dps(*args: str) -> Result:
    return runner.invoke(app, list(args))


def names(repository: FavouriteRepository) -> list[str]:
    return [favourite.name for favourite in repository.all()]


def test_help() -> None:
    result = dps("--help")

    assert result.exit_code == 0, result.output
    assert "fav" in result.output


def test_importing_the_cli_does_not_load_pystray() -> None:
    probe = "import sys, discord_profile_studio.cli; print('pystray' in sys.modules)"
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", probe],
        capture_output=True,
        text=True,
        check=True,
    )

    assert result.stdout.strip() == "False"


def test_save_creates_then_changes_only_the_given_fields(repository: FavouriteRepository):
    assert dps("fav", "save", "Coding", "-d", "Writing", "-s", "Tests").exit_code == 0
    result = dps("fav", "save", "Coding", "-s", "Docs", "--large-image", "logo")

    assert result.exit_code == 0, result.output
    presence = repository.get("Coding").presence
    assert (presence.details, presence.state, presence.large_image.key) == (
        "Writing",
        "Docs",
        "logo",
    )


def test_save_refuses_a_blank_name(repository: FavouriteRepository):
    result = dps("fav", "save", " ")

    assert result.exit_code == 1
    assert names(repository) == []


def test_list_prints_names_with_brackets_literally():
    dps("fav", "save", "[test] a [/] b")

    result = dps("fav", "list")

    assert result.exit_code == 0, result.output
    assert "[test] a [/] b" in result.output


def test_list_with_no_favourites_says_so():
    result = dps("fav", "list")

    assert result.exit_code == 0
    assert "No favourites" in result.output


def test_show_prints_the_favourite_as_json():
    dps("fav", "save", "Coding", "-d", "Writing")

    result = dps("fav", "show", "Coding")

    assert result.exit_code == 0, result.output
    shown = json.loads(result.output)
    assert (shown["name"], shown["presence"]["details"]) == ("Coding", "Writing")


def test_delete_removes_only_that_favourite(repository: FavouriteRepository):
    dps("fav", "save", "Coding")
    dps("fav", "save", "Gaming")

    result = dps("fav", "delete", "Coding")

    assert result.exit_code == 0, result.output
    assert names(repository) == ["Gaming"]


def test_missing_favourite_fails_with_a_message():
    result = dps("fav", "delete", "Nope")

    assert result.exit_code == 1
    assert "no favourite named 'Nope'" in result.output


def test_import_customrp_presets_and_settings_with_free_names(repository: FavouriteRepository):
    assert dps("fav", "import", str(CUSTOMRP)).exit_code == 0
    assert dps("fav", "import", str(CUSTOMRP / "user.config")).exit_code == 0
    result = dps("fav", "import", str(CUSTOMRP / "preset.crp"))

    assert result.exit_code == 0, result.output
    assert names(repository) == ["preset", "CustomRP", "preset (1)"]


def test_import_refuses_an_unknown_source(repository: FavouriteRepository):
    result = dps("fav", "import", str(CUSTOMRP), "--source", "nope")

    assert result.exit_code == 1
    assert "unknown source" in result.output
    assert names(repository) == []


def test_import_of_an_empty_directory_fails(tmp_path: Path):
    empty = tmp_path / "empty"
    empty.mkdir()

    result = dps("fav", "import", str(empty))

    assert result.exit_code == 1
    assert "no favourites found" in result.output


def test_export_round_trips_through_dps_import(
    repository: FavouriteRepository,
    tmp_path: Path,
):
    dps("fav", "save", "Coding", "-d", "Writing")
    target = tmp_path / "coding.json"

    assert dps("fav", "export", "Coding", str(target)).exit_code == 0
    result = dps("fav", "import", str(target), "--source", "dps")

    assert result.exit_code == 0, result.output
    copy = repository.get("Coding (1)")
    assert copy.presence == repository.get("Coding").presence


def test_export_keeps_an_existing_file_unless_forced(tmp_path: Path):
    dps("fav", "save", "Coding")
    target = tmp_path / "coding.json"
    target.write_text("keep me")

    refused = dps("fav", "export", "Coding", str(target))

    assert refused.exit_code == 1
    assert "already exists" in refused.output
    assert target.read_text() == "keep me"

    assert dps("fav", "export", "Coding", str(target), "--force").exit_code == 0
    assert '"Coding"' in target.read_text()
