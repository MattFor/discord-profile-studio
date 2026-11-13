import sys
from pathlib import Path

import pytest

from discord_profile_studio.models.favourite import Favourite

PLATFORM_MARKERS = {
    "windows": (sys.platform == "win32", "requires Windows"),
    "linux": (sys.platform == "linux", "requires Linux"),
    "macos": (sys.platform == "darwin", "requires macOS"),
    "posix": (sys.platform != "win32", "requires POSIX"),
}


def pytest_runtest_setup(item: pytest.Item) -> None:
    for name, (supported, reason) in PLATFORM_MARKERS.items():
        if not supported and item.get_closest_marker(name) is not None:
            pytest.skip(reason)


@pytest.fixture
def favourite() -> Favourite:
    raise NotImplementedError


@pytest.fixture
def store(tmp_path: Path) -> Path:
    raise NotImplementedError
