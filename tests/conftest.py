import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from discord_profile_studio.models import (
    ActivityType,
    Asset,
    Button,
    Favourite,
    Presence,
    StatusDisplay,
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
    moment = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
    return Favourite(
        name="Coding",
        presence=Presence(
            name="Studio",
            activity_type=ActivityType.WATCHING,
            status_display=StatusDisplay.DETAILS,
            details="Writing tests",
            details_url="https://example.com/details",
            state_url="https://example.com/state",
            large_image=Asset(key="logo", url="https://example.com/logo.png"),
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
    return tmp_path / "favourites.json"
