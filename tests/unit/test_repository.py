import dataclasses
import re
from pathlib import Path

import pytest

from discord_profile_studio.core.exceptions import StorageError
from discord_profile_studio.models import Favourite
from discord_profile_studio.storage import FavouriteRepository, document


def test_all_of_a_missing_file_is_empty_and_creates_nothing(store: Path):
    assert FavouriteRepository(store).all() == []
    assert not store.exists()


def test_all_reads_favourites_from_the_file(store: Path, favourite: Favourite):
    store.write_text(document.to_text([favourite]), encoding="utf-8")

    assert FavouriteRepository(store).all() == [favourite]


def test_all_reads_the_file_again_on_every_call(store: Path, favourite: Favourite):
    repository = FavouriteRepository(store)
    store.write_text(document.to_text([favourite]), encoding="utf-8")
    repository.all()
    second = dataclasses.replace(favourite, name="Other")
    store.write_text(document.to_text([favourite, second]), encoding="utf-8")

    assert repository.all() == [favourite, second]


def test_all_refuses_an_empty_file(store: Path):
    store.write_text("", encoding="utf-8")

    with pytest.raises(StorageError, match=re.escape("not valid JSON")):
        FavouriteRepository(store).all()


def test_all_leaves_a_broken_file_untouched(store: Path):
    store.write_text('{"version": 1, "favourites": [', encoding="utf-8")

    with pytest.raises(StorageError):
        FavouriteRepository(store).all()

    assert store.read_text(encoding="utf-8") == '{"version": 1, "favourites": ['


def test_all_wraps_bytes_that_are_not_utf8(store: Path):
    store.write_bytes(b'{"version": 1, "favourites": ["\xff"]}')

    with pytest.raises(StorageError, match=re.escape("cannot read")) as caught:
        FavouriteRepository(store).all()

    assert isinstance(caught.value.__cause__, UnicodeDecodeError)


def test_all_wraps_an_os_error(store: Path):
    store.mkdir()

    with pytest.raises(StorageError, match=re.escape("cannot read")) as caught:
        FavouriteRepository(store).all()

    assert isinstance(caught.value.__cause__, OSError)


@pytest.mark.skip
def test_add_and_get() -> None:
    raise NotImplementedError


@pytest.mark.skip
def test_delete_missing() -> None:
    raise NotImplementedError
