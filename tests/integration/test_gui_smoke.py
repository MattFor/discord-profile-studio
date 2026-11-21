from collections.abc import Iterator
from pathlib import Path
from tkinter import TclError

import pytest
from pytest_mock import MockerFixture

from discord_profile_studio.gui import app as app_module
from discord_profile_studio.gui.app import Application
from discord_profile_studio.gui.sections import Section
from discord_profile_studio.models import Favourite
from discord_profile_studio.storage.repository import FavouriteRepository

pytestmark = pytest.mark.gui


@pytest.fixture
def repository(store: Path, monkeypatch: pytest.MonkeyPatch) -> FavouriteRepository:
    monkeypatch.setattr(app_module, "favourites_file", lambda: store)
    return FavouriteRepository(store)


@pytest.fixture
def application(repository: FavouriteRepository) -> Iterator[Application]:
    assert repository
    try:
        instance = Application()
    except TclError:
        pytest.skip("no display server available")
    instance.withdraw()
    instance.build()
    yield instance
    instance.destroy()


def asked(mocker: MockerFixture, answer: str) -> None:
    mocker.patch.object(app_module.simpledialog, "askstring", return_value=answer)


def test_window_builds_with_the_widgets_tab(application: Application):
    assert list(application.editor.sections) == [Section.WIDGETS]


def test_save_names_and_adds_a_new_favourite(
    application: Application,
    repository: FavouriteRepository,
    mocker: MockerFixture,
):
    asked(mocker, " Coding ")

    application.save()

    assert [favourite.name for favourite in repository.all()] == ["Coding"]
    assert application.message.get() == "Saved Coding"


def test_saving_a_new_favourite_never_overwrites_an_existing_one(
    application: Application,
    repository: FavouriteRepository,
    mocker: MockerFixture,
):
    repository.add(Favourite(name="Coding", tags=["keep"]))
    asked(mocker, "Coding")

    application.save()

    assert repository.get("Coding").tags == ["keep"]
    assert "already exists" in application.message.get()
    assert application.state_store.current.name == ""


def test_save_updates_a_loaded_favourite(
    application: Application,
    repository: FavouriteRepository,
    favourite: Favourite,
):
    repository.add(favourite)
    application.state_store.set_current(repository.get("Coding"))
    application.editor.read()

    application.save()

    assert repository.get("Coding").updated_at > favourite.updated_at
    assert application.message.get() == "Saved Coding"
