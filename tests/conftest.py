import sys
from datetime import datetime
from pathlib import Path

import pytest

from discord_profile_studio.models import (
    ActivityType,
    Button,
    Favourite,
    Presence,
    TimestampMode,
    Timestamps,
    Widget,
    WidgetKind,
)

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
    moment = datetime(2026, 1, 2, 3, 4, 5)  # noqa: DTZ001
    return Favourite(
        name="Coding",
        presence=Presence(
            activity_type=ActivityType.WATCHING,
            details="Writing tests",
            timestamps=Timestamps(mode=TimestampMode.SINCE_START),
            buttons=[Button(label="Repo", url="https://example.com")],
        ),
        widgets=[Widget(kind=WidgetKind.LINK, title="Docs")],
        tags=["dev"],
        created_at=moment,
        updated_at=moment,
    )


@pytest.fixture
def store(tmp_path: Path) -> Path:
    raise NotImplementedError
