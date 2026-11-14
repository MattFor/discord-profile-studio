import json
import re
from datetime import UTC, datetime
from typing import Any

import pytest

from discord_profile_studio.core.exceptions import StorageError
from discord_profile_studio.models import (
    ActivityType,
    Favourite,
    Presence,
    TimestampMode,
    Timestamps,
    Widget,
    WidgetKind,
)
from discord_profile_studio.storage.serializers import (
    favourite_from_dict,
    favourite_to_dict,
    presence_from_dict,
    presence_to_dict,
    widget_from_dict,
    widget_to_dict,
)

MOMENT = "2026-01-02T03:04:05+00:00"
PLAIN_JSON_TYPES = {dict, list, str, int, bool, type(None)}


def version_1_document() -> dict[str, Any]:
    return {
        "name": "Coding",
        "presence": {
            "client_id": "",
            "activity_type": 3,
            "details": "Writing tests",
            "state": "",
            "large_image": {"key": "", "text": ""},
            "small_image": {"key": "", "text": ""},
            "party": {"size": 0, "maximum": 0},
            "timestamps": {"mode": "since_start", "start": None, "end": None},
            "buttons": [{"label": "Repo", "url": "https://example.com"}],
        },
        "widgets": [
            {
                "kind": "link",
                "title": "Docs",
                "body": "",
                "icon": "",
                "accent": "#5865F2",
                "enabled": True,
                "options": {},
            },
        ],
        "tags": ["dev"],
        "created_at": MOMENT,
        "updated_at": MOMENT,
    }


def steps(path: str) -> list[str | int]:
    return [int(index) if index else key for key, index in re.findall(r"(\w+)|\[(\d+)\]", path)]


def replace_at(document: dict[str, Any], path: str, value: object) -> None:
    *parents, last = steps(path)
    target: Any = document
    for step in parents:
        target = target[step]
    target[last] = value


def json_types(value: object) -> set[type]:
    found: set[type] = {type(value)}
    if isinstance(value, dict):
        for item in value.values():  # pyright: ignore[reportUnknownVariableType]
            found |= json_types(item)
    if isinstance(value, list):
        for item in value:  # pyright: ignore[reportUnknownVariableType]
            found |= json_types(item)
    return found


def test_favourite_to_dict_writes_the_version_1_format(favourite: Favourite):
    assert favourite_to_dict(favourite) == version_1_document()


def test_favourite_to_dict_holds_only_plain_json_types(favourite: Favourite):
    assert json_types(favourite_to_dict(favourite)) <= PLAIN_JSON_TYPES


def test_favourite_survives_a_round_trip_through_json_text(favourite: Favourite):
    text = json.dumps(favourite_to_dict(favourite))

    assert favourite_from_dict(json.loads(text)) == favourite


def test_round_trip_rebuilds_enum_members_not_raw_values(favourite: Favourite):
    loaded = favourite_from_dict(json.loads(json.dumps(favourite_to_dict(favourite))))

    assert type(loaded.presence.activity_type) is ActivityType
    assert type(loaded.presence.timestamps.mode) is TimestampMode
    assert type(loaded.widgets[0].kind) is WidgetKind


def test_presence_and_widget_survive_their_own_round_trip(favourite: Favourite):
    widget = Widget(kind=WidgetKind.MEDIA, options={"mode": "compact"}, enabled=False)

    assert presence_from_dict(presence_to_dict(favourite.presence)) == favourite.presence
    assert widget_from_dict(widget_to_dict(widget)) == widget


def test_favourite_with_only_required_keys_gets_model_defaults():
    loaded = favourite_from_dict({"name": "Bare", "created_at": MOMENT, "updated_at": MOMENT})

    moment = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
    assert loaded == Favourite(name="Bare", created_at=moment, updated_at=moment)


def test_nested_objects_with_no_keys_get_model_defaults():
    assert presence_from_dict({"timestamps": {}, "party": {}}) == Presence()
    assert widget_from_dict({}) == Widget()


def test_timestamps_start_and_end_accept_null_and_integers():
    loaded = presence_from_dict({"timestamps": {"start": 10, "end": None}})

    assert loaded.timestamps == Timestamps(start=10, end=None)


@pytest.mark.parametrize("key", ["name", "created_at", "updated_at"])
def test_missing_required_key_raises_with_its_path(key: str):
    document = version_1_document()
    del document[key]

    with pytest.raises(StorageError, match=re.escape(f"favourite.{key}: required key")):
        favourite_from_dict(document)


@pytest.mark.parametrize(
    "path",
    [
        "detials",
        "presence.detials",
        "presence.timestamps.begin",
        "presence.buttons[0].href",
        "widgets[0].colour",
    ],
)
def test_unknown_key_raises_with_its_path(path: str):
    document = version_1_document()
    replace_at(document, path, "x")

    with pytest.raises(StorageError, match=re.escape(f"favourite.{path}: unknown key")):
        favourite_from_dict(document)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        pytest.param("name", 1, id="int-for-str"),
        pytest.param("presence.party.size", True, id="bool-for-int"),
        pytest.param("presence.party.maximum", 2.0, id="float-for-int"),
        pytest.param("presence.timestamps.start", "1", id="str-for-optional-int"),
        pytest.param("presence.activity_type", "3", id="str-for-int-enum"),
        pytest.param("presence.activity_type", 3.0, id="float-for-int-enum"),
        pytest.param("presence", [], id="list-for-object"),
        pytest.param("presence.buttons", {}, id="object-for-list"),
        pytest.param("presence.buttons[0]", "Repo", id="str-for-button"),
        pytest.param("widgets[0].enabled", 1, id="int-for-bool"),
        pytest.param("widgets[0].options", [], id="list-for-options"),
        pytest.param("widgets[0].options", {"mode": 1}, id="int-option-value"),
        pytest.param("tags[0]", 7, id="int-tag"),
        pytest.param("created_at", 1767323045, id="int-for-timestamp"),
    ],
)
def test_wrong_type_raises_with_its_path(path: str, value: object):
    document = version_1_document()
    replace_at(document, path, value)

    with pytest.raises(StorageError, match=re.escape(f"favourite.{path}")) as caught:
        favourite_from_dict(document)

    assert "expected" in str(caught.value)


def test_favourite_that_is_not_an_object_raises():
    with pytest.raises(StorageError, match=re.escape("favourite: expected an object")):
        favourite_from_dict(["Coding"])


@pytest.mark.parametrize(
    ("path", "value"),
    [
        ("presence.activity_type", 1),
        ("presence.timestamps.mode", "later"),
        ("widgets[0].kind", "banner"),
    ],
)
def test_unknown_enum_value_raises_and_chains_the_lookup_error(path: str, value: object):
    document = version_1_document()
    replace_at(document, path, value)

    with pytest.raises(StorageError, match=re.escape(f"favourite.{path}: unknown")) as caught:
        favourite_from_dict(document)

    assert type(caught.value.__cause__) is ValueError


def test_naive_timestamp_raises():
    document = version_1_document()
    replace_at(document, "updated_at", "2026-01-02T03:04:05")

    with pytest.raises(StorageError, match=re.escape("updated_at: timestamp has no time zone")):
        favourite_from_dict(document)


def test_malformed_timestamp_raises_and_chains_the_parse_error():
    document = version_1_document()
    replace_at(document, "created_at", "yesterday")

    with pytest.raises(StorageError, match=re.escape("created_at: invalid ISO 8601")) as caught:
        favourite_from_dict(document)

    assert type(caught.value.__cause__) is ValueError


def test_timestamp_offset_is_kept_as_the_same_instant():
    document = version_1_document()
    replace_at(document, "created_at", "2026-01-02T05:04:05+02:00")

    loaded = favourite_from_dict(document)

    assert loaded.created_at == datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)


@pytest.mark.parametrize("raw", ["#5865f2", "5865F2", " #5865f2 "])
def test_accent_is_normalized_to_uppercase_with_hash_on_read(raw: str):
    assert widget_from_dict({"accent": raw}).accent == "#5865F2"


def test_invalid_accent_raises_and_chains_the_colour_error():
    with pytest.raises(StorageError, match=re.escape("widget.accent: invalid colour")) as caught:
        widget_from_dict({"accent": "#12345"})

    assert caught.value.__cause__ is not None


def test_error_message_shows_the_bad_value():
    document = version_1_document()
    replace_at(document, "presence.party.size", "four")

    with pytest.raises(StorageError, match=re.escape("got 'four'")):
        favourite_from_dict(document)


def test_error_path_starts_with_the_given_location():
    document = version_1_document()
    del document["name"]

    with pytest.raises(StorageError, match=re.escape("favourites[2].name")):
        favourite_from_dict(document, where="favourites[2]")
