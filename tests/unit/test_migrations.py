import re
from typing import Any

import pytest

from discord_profile_studio.core.exceptions import StorageError
from discord_profile_studio.storage.migrations import SCHEMA_VERSION, migrate


def test_current_version_passes_through_unchanged():
    document: dict[str, Any] = {"version": SCHEMA_VERSION, "favourites": []}

    assert migrate(document) == {"version": SCHEMA_VERSION, "favourites": []}


def test_missing_version_raises():
    with pytest.raises(StorageError, match=re.escape("version: required key is missing")):
        migrate({"favourites": []})


@pytest.mark.parametrize("version", [0, -1, True, 1.0, "1", None])
def test_version_that_is_not_a_positive_int_raises(version: object):
    with pytest.raises(StorageError, match=re.escape("version: expected a positive int")):
        migrate({"version": version, "favourites": []})


def test_version_newer_than_the_program_raises():
    with pytest.raises(StorageError, match=re.escape(f"reads up to {SCHEMA_VERSION}")):
        migrate({"version": SCHEMA_VERSION + 1, "favourites": []})
