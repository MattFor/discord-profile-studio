import json
import reprlib
from collections.abc import Collection
from typing import Any, cast

from discord_profile_studio.core.exceptions import StorageError
from discord_profile_studio.models.favourite import Favourite
from discord_profile_studio.storage.migrations import SCHEMA_VERSION, migrate
from discord_profile_studio.storage.serializers import favourite_from_dict, favourite_to_dict

_KEYS = frozenset({"version", "favourites"})


def to_text(favourites: list[Favourite]) -> str:
    document = {
        "version": SCHEMA_VERSION,
        "favourites": [favourite_to_dict(favourite) for favourite in favourites],
    }
    try:
        text = json.dumps(document, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        from_text(text)
    except (StorageError, TypeError, ValueError) as e:
        msg = f"refusing to save, the file would not load back: {e}"
        raise StorageError(msg) from e
    return text


def free_name(name: str, taken: Collection[str]) -> str:
    if name not in taken:
        return name
    n = 1
    while f"{name} ({n})" in taken:
        n += 1
    return f"{name} ({n})"


def from_text(text: str) -> list[Favourite]:
    try:
        data: object = json.loads(text, object_pairs_hook=_unique_keys)
    except json.JSONDecodeError as e:
        msg = f"not valid JSON: {e}"
        raise StorageError(msg) from e
    if type(data) is not dict:
        msg = f"expected an object at the top level, got {reprlib.repr(data)}"
        raise StorageError(msg)
    document = migrate(cast("dict[str, Any]", data))
    for key in sorted(document.keys() - _KEYS):
        msg = f"{key}: unknown key"
        raise StorageError(msg)
    if "favourites" not in document:
        msg = "favourites: required key is missing"
        raise StorageError(msg)
    items: object = document["favourites"]
    if type(items) is not list:
        msg = f"favourites: expected list, got {reprlib.repr(items)}"
        raise StorageError(msg)
    return _favourites(cast("list[object]", items))


def _favourites(items: list[object]) -> list[Favourite]:
    first_seen: dict[str, int] = {}
    favourites: list[Favourite] = []
    for i, item in enumerate(items):
        favourite = favourite_from_dict(item, where=f"favourites[{i}]")
        if favourite.name in first_seen:
            msg = (
                f"favourites[{i}].name: duplicate of favourites[{first_seen[favourite.name]}], "
                f"got {reprlib.repr(favourite.name)}"
            )
            raise StorageError(msg)
        first_seen[favourite.name] = i
        favourites.append(favourite)
    return favourites


def _unique_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    obj: dict[str, Any] = {}
    for key, value in pairs:
        if key in obj:
            msg = f"duplicate key {reprlib.repr(key)} in a JSON object"
            raise StorageError(msg)
        obj[key] = value
    return obj
