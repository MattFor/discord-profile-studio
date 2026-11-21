import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from discord_profile_studio.models import (
    ActivityType,
    Asset,
    Button,
    Favourite,
    FieldType,
    Presence,
    StatusDisplay,
    TimestampMode,
    Timestamps,
    Widget,
    WidgetField,
)
from discord_profile_studio.widgets.api import API, IDENTITY_API

WIDGET_APP = "1234567890"
WIDGET_OWNER = "42"

# Shape inferred from the Widget Identity Creator, see widgets/spec.py
WIDGET_CONFIG = {
    "config_id": "99",
    "status": "draft",
    "surfaces": [
        {
            "components": [
                {
                    "fields": [
                        {"value_type": "static", "value": "Season 3", "presentation_type": "text"},
                        {"value_type": "data", "value": "rank", "presentation_type": "text"},
                        {"value_type": "data", "value": "level", "presentation_type": "integer"},
                    ],
                },
                {
                    "fields": [
                        {"value_type": "data", "value": "cover", "presentation_type": "image"},
                        {"value_type": "data", "value": "level", "presentation_type": "number"},
                    ],
                },
            ],
        },
    ],
}

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
        widgets=[
            Widget(
                application_id="1234567890",
                name="Stats",
                fields=[WidgetField(name="level", kind=FieldType.NUMBER, value="42")],
            ),
        ],
        tags=["dev"],
        created_at=moment,
        updated_at=moment,
    )


@pytest.fixture
def store(tmp_path: Path) -> Path:
    return tmp_path / "favourites.json"


class FakeDiscord:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, str], object]] = []
        identity = (
            f"{IDENTITY_API}/applications/{WIDGET_APP}/users/{WIDGET_OWNER}/identities/0/profile"
        )
        application = {"id": WIDGET_APP, "name": "Stats", "owner": {"id": WIDGET_OWNER}}
        self.routes: dict[tuple[str, str], httpx.Response | httpx.HTTPError] = {
            ("GET", f"{API}/oauth2/applications/@me"): httpx.Response(200, json=application),
            ("GET", f"{API}/applications/{WIDGET_APP}/widget-configs"): httpx.Response(
                200,
                json=[WIDGET_CONFIG],
            ),
            ("PATCH", identity): httpx.Response(204),
        }

    def __call__(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        json: object,
        **_: object,
    ) -> httpx.Response:
        self.calls.append((method, url, headers, json))
        result = self.routes[method, url]

        if isinstance(result, httpx.HTTPError):
            raise result

        return result


@pytest.fixture
def discord(monkeypatch: pytest.MonkeyPatch) -> FakeDiscord:
    fake = FakeDiscord()
    monkeypatch.setattr(httpx, "request", fake)
    return fake
