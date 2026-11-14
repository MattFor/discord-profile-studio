import dataclasses
import re
from datetime import UTC, datetime
from pathlib import Path

import pytest

from discord_profile_studio.core.exceptions import FavouriteNotFoundError, StorageError
from discord_profile_studio.models import Favourite
from discord_profile_studio.storage import FavouriteRepository, document, repository

BOM = b"\xef\xbb\xbf"
LATER = datetime(2026, 3, 4, 5, 6, 7, tzinfo=UTC)


def at_later() -> datetime:
    return LATER


def test_all_of_a_missing_file_is_empty_and_creates_nothing(store: Path):
    assert FavouriteRepository(store).all() == []
    assert not store.exists()


def test_all_reads_favourites_from_the_file(store: Path, favourite: Favourite):
    store.write_text(document.to_text([favourite]), encoding="utf-8")

    assert FavouriteRepository(store).all() == [favourite]


def test_all_reads_the_file_again_on_every_call(store: Path, favourite: Favourite):
    repo = FavouriteRepository(store)
    store.write_text(document.to_text([favourite]), encoding="utf-8")
    repo.all()
    second = dataclasses.replace(favourite, name="Other")
    store.write_text(document.to_text([favourite, second]), encoding="utf-8")

    assert repo.all() == [favourite, second]


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


def test_all_reads_a_file_with_a_bom(store: Path, favourite: Favourite):
    store.write_bytes(BOM + document.to_text([favourite]).encode("utf-8"))

    assert FavouriteRepository(store).all() == [favourite]


def test_add_then_get_returns_the_favourite(store: Path, favourite: Favourite):
    repo = FavouriteRepository(store)
    repo.add(favourite)

    assert repo.get("Coding") == favourite


def test_add_persists_for_a_new_repository_on_the_same_path(store: Path, favourite: Favourite):
    FavouriteRepository(store).add(favourite)

    assert FavouriteRepository(store).all() == [favourite]


def test_add_appends_at_the_end(store: Path, favourite: Favourite):
    repo = FavouriteRepository(store)
    repo.add(dataclasses.replace(favourite, name="Other"))
    repo.add(favourite)

    assert [f.name for f in repo.all()] == ["Other", "Coding"]


def test_add_keeps_the_timestamps_of_the_favourite(store: Path, favourite: Favourite):
    repo = FavouriteRepository(store, clock=at_later)
    repo.add(favourite)

    stored = repo.get("Coding")
    assert (stored.created_at, stored.updated_at) == (favourite.created_at, favourite.updated_at)


def test_add_of_a_taken_name_raises_and_leaves_the_file_unchanged(
    store: Path, favourite: Favourite
):
    repo = FavouriteRepository(store)
    repo.add(favourite)
    before = store.read_bytes()

    with pytest.raises(StorageError, match=re.escape("already exists")):
        repo.add(dataclasses.replace(favourite, tags=["other"]))

    assert store.read_bytes() == before


def test_add_of_a_blank_name_raises_and_writes_nothing(store: Path, favourite: Favourite):
    with pytest.raises(StorageError, match=re.escape("refusing to save")):
        FavouriteRepository(store).add(dataclasses.replace(favourite, name="  "))

    assert not store.exists()


def test_add_after_a_failed_load_leaves_the_broken_file_untouched(
    store: Path, favourite: Favourite
):
    store.write_text('{"version": 1, "favourites": [', encoding="utf-8")

    with pytest.raises(StorageError):
        FavouriteRepository(store).add(favourite)

    assert store.read_text(encoding="utf-8") == '{"version": 1, "favourites": ['


def test_saved_file_is_the_document_text_without_bom_or_crlf(store: Path, favourite: Favourite):
    FavouriteRepository(store).add(favourite)

    data = store.read_bytes()
    assert not data.startswith(BOM)
    assert b"\r" not in data
    assert data == document.to_text([favourite]).encode("utf-8")


def test_saving_over_a_file_with_a_bom_drops_the_bom(store: Path, favourite: Favourite):
    store.write_bytes(BOM + document.to_text([favourite]).encode("utf-8"))

    FavouriteRepository(store).delete("Coding")

    assert not store.read_bytes().startswith(BOM)


def test_save_wraps_an_os_error(store: Path, favourite: Favourite, monkeypatch: pytest.MonkeyPatch):
    def refuse(path: Path, _data: str | bytes) -> Path:
        raise PermissionError(path)

    monkeypatch.setattr(repository, "write_private", refuse)

    with pytest.raises(StorageError, match=re.escape("cannot write")) as caught:
        FavouriteRepository(store).add(favourite)

    assert isinstance(caught.value.__cause__, PermissionError)


def test_get_of_a_missing_name_raises_favourite_not_found(store: Path, favourite: Favourite):
    repo = FavouriteRepository(store)
    repo.add(favourite)

    with pytest.raises(FavouriteNotFoundError, match=re.escape("'coding'")):
        repo.get("coding")


def test_update_replaces_the_favourite_in_place(store: Path, favourite: Favourite):
    repo = FavouriteRepository(store, clock=at_later)
    repo.add(favourite)
    repo.add(dataclasses.replace(favourite, name="Other"))

    repo.update(dataclasses.replace(favourite, tags=["changed"]))

    assert [(f.name, f.tags) for f in FavouriteRepository(store).all()] == [
        ("Coding", ["changed"]),
        ("Other", ["dev"]),
    ]


def test_update_sets_updated_at_and_keeps_the_stored_created_at(store: Path, favourite: Favourite):
    repo = FavouriteRepository(store, clock=at_later)
    repo.add(favourite)

    repo.update(dataclasses.replace(favourite, created_at=LATER))

    stored = repo.get("Coding")
    assert (stored.created_at, stored.updated_at) == (favourite.created_at, LATER)


def test_update_does_not_change_the_given_favourite(store: Path, favourite: Favourite):
    repo = FavouriteRepository(store, clock=at_later)
    repo.add(favourite)
    given = dataclasses.replace(favourite, tags=["changed"])

    repo.update(given)

    assert given.updated_at == favourite.updated_at


def test_update_of_a_missing_name_raises_favourite_not_found(store: Path, favourite: Favourite):
    with pytest.raises(FavouriteNotFoundError):
        FavouriteRepository(store).update(favourite)

    assert not store.exists()


def test_delete_removes_only_that_favourite(store: Path, favourite: Favourite):
    repo = FavouriteRepository(store)
    repo.add(favourite)
    repo.add(dataclasses.replace(favourite, name="Other"))

    repo.delete("Coding")

    assert [f.name for f in FavouriteRepository(store).all()] == ["Other"]


def test_delete_of_a_missing_name_raises_favourite_not_found(store: Path):
    with pytest.raises(FavouriteNotFoundError):
        FavouriteRepository(store).delete("Coding")


def test_rename_keeps_the_position_and_sets_updated_at(store: Path, favourite: Favourite):
    repo = FavouriteRepository(store, clock=at_later)
    repo.add(favourite)
    repo.add(dataclasses.replace(favourite, name="Other"))

    repo.rename("Coding", "Work")

    renamed = FavouriteRepository(store).all()
    assert [f.name for f in renamed] == ["Work", "Other"]
    assert (renamed[0].created_at, renamed[0].updated_at) == (favourite.created_at, LATER)


def test_rename_onto_a_taken_name_raises_and_leaves_the_file_unchanged(
    store: Path, favourite: Favourite
):
    repo = FavouriteRepository(store)
    repo.add(favourite)
    repo.add(dataclasses.replace(favourite, name="Other"))
    before = store.read_bytes()

    with pytest.raises(StorageError, match=re.escape("already exists")):
        repo.rename("Coding", "Other")

    assert store.read_bytes() == before


def test_rename_onto_its_own_name_raises(store: Path, favourite: Favourite):
    repo = FavouriteRepository(store)
    repo.add(favourite)

    with pytest.raises(StorageError, match=re.escape("already exists")):
        repo.rename("Coding", "Coding")


def test_rename_of_a_missing_name_raises_favourite_not_found(store: Path):
    with pytest.raises(FavouriteNotFoundError):
        FavouriteRepository(store).rename("Coding", "Work")
