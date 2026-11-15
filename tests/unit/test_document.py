import dataclasses
import json
import re
from datetime import UTC, datetime
from typing import Any

import pytest

from discord_profile_studio.core.exceptions import StorageError
from discord_profile_studio.models import Favourite
from discord_profile_studio.storage import document
from discord_profile_studio.storage.migrations import SCHEMA_VERSION


def as_data(favourites: list[Favourite]) -> dict[str, Any]:
    return json.loads(document.to_text(favourites))


def test_round_trip_returns_equal_favourites_in_the_same_order(favourite: Favourite):
    second = dataclasses.replace(favourite, name="Alpha")

    assert document.from_text(document.to_text([favourite, second])) == [favourite, second]


def test_no_favourites_round_trip_to_an_empty_list():
    assert document.from_text(document.to_text([])) == []


def test_dumps_writes_the_schema_version_first(favourite: Favourite):
    text = document.to_text([favourite])

    assert text.startswith(f'{{\n  "version": {SCHEMA_VERSION},\n  "favourites": [')


def test_dumps_ends_with_a_newline(favourite: Favourite):
    assert document.to_text([favourite]).endswith("}\n")


def test_dumps_keeps_non_ascii_text_readable(favourite: Favourite):
    favourite.presence.details = "Zażółć gęślą jaźń"

    assert "Zażółć gęślą jaźń" in document.to_text([favourite])


def test_dumps_refuses_a_naive_timestamp(favourite: Favourite):
    favourite.updated_at = datetime(2026, 1, 2)  # noqa: DTZ001

    with pytest.raises(StorageError, match=re.escape("refusing to save")) as caught:
        document.to_text([favourite])

    assert "favourites[0].updated_at: timestamp has no time zone" in str(caught.value)


def test_dumps_refuses_a_blank_name(favourite: Favourite):
    favourite.name = "  "

    with pytest.raises(StorageError, match=re.escape("favourites[0].name: name is blank")):
        document.to_text([favourite])


def test_dumps_refuses_duplicate_names(favourite: Favourite):
    with pytest.raises(StorageError, match=re.escape("favourites[1].name: duplicate")):
        document.to_text([favourite, dataclasses.replace(favourite)])


@pytest.mark.parametrize("text", ["", "   \n", "{", '{"version": 1,'])
def test_loads_refuses_text_that_is_not_json(text: str):
    with pytest.raises(StorageError, match=re.escape("not valid JSON")):
        document.from_text(text)


@pytest.mark.parametrize("text", ["[]", "1", "null", '"favourites"'])
def test_loads_refuses_a_top_level_value_that_is_not_an_object(text: str):
    with pytest.raises(StorageError, match=re.escape("expected an object at the top level")):
        document.from_text(text)


def test_loads_refuses_a_duplicate_key_at_the_top_level():
    with pytest.raises(StorageError, match=re.escape("duplicate key 'version'")):
        document.from_text('{"version": 1, "version": 1, "favourites": []}')


def test_loads_refuses_a_duplicate_key_inside_a_favourite(favourite: Favourite):
    text = document.to_text([favourite]).replace(
        '"name": "Coding",',
        '"name": "Coding",\n      "name": "Other",',
    )

    with pytest.raises(StorageError, match=re.escape("duplicate key 'name'")):
        document.from_text(text)


def test_loads_refuses_an_unknown_top_level_key():
    with pytest.raises(StorageError, match=re.escape("favorites: unknown key")):
        document.from_text('{"version": 1, "favourites": [], "favorites": []}')


def test_loads_refuses_a_document_without_favourites():
    with pytest.raises(StorageError, match=re.escape("favourites: required key is missing")):
        document.from_text('{"version": 1}')


def test_loads_refuses_favourites_that_are_not_a_list():
    with pytest.raises(StorageError, match=re.escape("favourites: expected list")):
        document.from_text('{"version": 1, "favourites": {}}')


def test_loads_refuses_a_file_from_a_newer_version():
    with pytest.raises(StorageError, match=re.escape("version: file is version")):
        document.from_text(f'{{"version": {SCHEMA_VERSION + 1}, "favourites": []}}')


def test_loads_refuses_duplicate_names_and_names_both_places(favourite: Favourite):
    data = as_data([favourite, dataclasses.replace(favourite, name="Other")])
    data["favourites"][1]["name"] = favourite.name

    with pytest.raises(
        StorageError, match=re.escape("favourites[1].name: duplicate of favourites[0]")
    ):
        document.from_text(json.dumps(data))


def test_loads_treats_names_that_differ_only_in_case_as_distinct(favourite: Favourite):
    upper = dataclasses.replace(favourite, name="CODING")

    assert [f.name for f in document.from_text(document.to_text([favourite, upper]))] == [
        "Coding",
        "CODING",
    ]


def test_loads_points_at_the_broken_favourite_by_index(favourite: Favourite):
    data = as_data([favourite, dataclasses.replace(favourite, name="Other")])
    data["favourites"][1]["presence"]["activity_type"] = 99

    with pytest.raises(StorageError, match=re.escape("favourites[1].presence.activity_type")):
        document.from_text(json.dumps(data))


def test_loads_reads_timestamps_back_as_aware_utc(favourite: Favourite):
    loaded = document.from_text(document.to_text([favourite]))[0]

    assert loaded.created_at == datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
    assert loaded.created_at.utcoffset() is not None


def test_free_name_returns_the_name_when_it_is_not_taken():
    assert document.free_name("Coding", ["Gaming"]) == "Coding"


def test_free_name_adds_the_first_free_number():
    assert document.free_name("Coding", ["Coding"]) == "Coding (1)"


def test_free_name_skips_numbers_already_taken():
    assert document.free_name("Coding", ["Coding", "Coding (1)", "Coding (2)"]) == "Coding (3)"


def test_free_name_compares_names_exactly():
    assert document.free_name("coding", ["Coding"]) == "coding"
