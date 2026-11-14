import reprlib
from collections.abc import Callable
from typing import Any

from discord_profile_studio.core.exceptions import StorageError

SCHEMA_VERSION = 1

type Step = Callable[[dict[str, Any]], dict[str, Any]]

_STEPS: dict[int, Step] = {}


def migrate(data: dict[str, Any]) -> dict[str, Any]:
    if "version" not in data:
        msg = "version: required key is missing"
        raise StorageError(msg)
    version = data["version"]
    if type(version) is not int or version < 1:
        msg = f"version: expected a positive int, got {reprlib.repr(version)}"
        raise StorageError(msg)
    if version > SCHEMA_VERSION:
        msg = f"version: file is version {version}, this program reads up to {SCHEMA_VERSION}"
        raise StorageError(msg)
    for current in range(version, SCHEMA_VERSION):
        data = {**_STEPS[current](data), "version": current + 1}
    return data
