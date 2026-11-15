import re
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from discord_profile_studio.core.exceptions import StorageError
from discord_profile_studio.importers.customrp import (
    default_config_paths,
    load_all,
    load_preset,
    load_settings,
)
from discord_profile_studio.models import (
    ActivityType,
    Asset,
    Button,
    Party,
    Presence,
    StatusDisplay,
    TimestampMode,
    Timestamps,
)

FIXTURES = Path(__file__).parent.parent / "fixtures" / "customrp"
PRESET = FIXTURES / "preset.crp"
SETTINGS = FIXTURES / "user.config"
PLUS_ONE = timezone(timedelta(hours=1))
PLUS_THREE = timezone(timedelta(hours=3))


def write_preset(path: Path, *elements: str) -> Path:
    path.write_text(f"<Preset>{''.join(elements)}</Preset>", encoding="utf-8")
    return path


@pytest.mark.parametrize("fixture", [PRESET, SETTINGS], ids=["preset", "settings"])
def test_fixtures_keep_the_crlf_and_missing_bom_of_the_real_files(fixture: Path):
    data = fixture.read_bytes()

    assert b"\r\n" in data
    assert b"\n" not in data.replace(b"\r\n", b"")
    assert not data.startswith(b"\xef\xbb\xbf")


def test_load_preset_maps_every_field_of_the_real_sample():
    favourite = load_preset(PRESET, tz=PLUS_ONE)

    assert favourite.name == "preset"
    assert favourite.presence == Presence(
        client_id="111111111111111111",
        name="Preset Activity",
        activity_type=ActivityType.WATCHING,
        status_display=StatusDisplay.DETAILS,
        details="Preset details",
        details_url="https://example.com/preset/details",
        state="Preset state",
        state_url="https://example.com/preset/state",
        large_image=Asset(
            "preset_large_key", "Preset large text", "https://example.com/preset/large"
        ),
        small_image=Asset(
            "preset_small_key", "Preset small text", "https://example.com/preset/small"
        ),
        party=Party(size=2, maximum=5),
        timestamps=Timestamps(mode=TimestampMode.CUSTOM, start=1794681009, end=2966092209),
        buttons=[
            Button("Preset button one", "https://example.com/preset/button1"),
            Button("Preset button two", "https://example.com/preset/button2"),
        ],
    )


def test_load_preset_rebuilds_enum_members_not_raw_values():
    presence = load_preset(PRESET, tz=PLUS_ONE).presence

    assert type(presence.activity_type) is ActivityType
    assert type(presence.status_display) is StatusDisplay
    assert type(presence.timestamps.mode) is TimestampMode


def test_load_preset_shifts_only_naive_times_with_the_given_time_zone():
    timestamps = load_preset(PRESET, tz=PLUS_THREE).presence.timestamps

    assert timestamps.start == 1794681009
    assert timestamps.end == 2966092209 - 2 * 3600


def test_load_preset_reads_naive_times_as_local_time_by_default():
    expected = int(datetime(2063, 12, 28, 19, 30, 9).astimezone().timestamp())

    assert load_preset(PRESET).presence.timestamps.end == expected


def test_load_settings_maps_every_field_and_ignores_app_settings():
    favourite = load_settings(SETTINGS, tz=PLUS_ONE)

    assert favourite.name == "CustomRP"
    assert favourite.presence == Presence(
        client_id="222222222222222222",
        name="Settings Activity",
        activity_type=ActivityType.LISTENING,
        status_display=StatusDisplay.NAME,
        details="Settings details",
        details_url="https://example.com/settings/details",
        state="Settings state",
        state_url="https://example.com/settings/state",
        large_image=Asset(
            "settings_large_key", "Settings large text", "https://example.com/settings/large"
        ),
        small_image=Asset(
            "settings_small_key", "Settings small text", "https://example.com/settings/small"
        ),
        party=Party(size=3, maximum=7),
        timestamps=Timestamps(mode=TimestampMode.CUSTOM, start=1794681009, end=2966092209),
        buttons=[
            Button("Settings button one", "https://example.com/settings/button1"),
            Button("Settings button two", "https://example.com/settings/button2"),
        ],
    )


def test_load_settings_refuses_a_file_without_the_customrp_section(tmp_path: Path):
    path = tmp_path / "user.config"
    path.write_text("<configuration><userSettings/></configuration>", encoding="utf-8")

    with pytest.raises(StorageError, match=re.escape("CustomRPC.Properties.Settings")):
        load_settings(path)


def test_load_settings_refuses_a_time_not_in_the_settings_format(tmp_path: Path):
    text = SETTINGS.read_text(encoding="utf-8").replace("11/14/2026 19:30:09", "2026-11-14")
    path = tmp_path / "user.config"
    path.write_text(text, encoding="utf-8")

    with pytest.raises(StorageError, match=re.escape("customTimestamp: expected a date")):
        load_settings(path)


def test_load_preset_of_an_empty_preset_gives_customrp_defaults(tmp_path: Path):
    favourite = load_preset(write_preset(tmp_path / "empty.crp"))

    assert favourite.presence == Presence(timestamps=Timestamps(mode=TimestampMode.SINCE_CONNECT))


@pytest.mark.parametrize(
    ("raw", "mode"),
    [
        ("0", TimestampMode.SINCE_CONNECT),
        ("1", TimestampMode.SINCE_START),
        ("2", TimestampMode.LOCAL_TIME),
        ("3", TimestampMode.CUSTOM),
        ("4", TimestampMode.SINCE_UPDATE),
    ],
)
def test_load_preset_maps_each_customrp_timestamp_mode(
    tmp_path: Path, raw: str, mode: TimestampMode
):
    path = write_preset(tmp_path / "p.crp", f"<Timestamps>{raw}</Timestamps>")

    assert load_preset(path).presence.timestamps.mode is mode


def test_load_preset_drops_custom_times_outside_custom_mode(tmp_path: Path):
    path = write_preset(
        tmp_path / "p.crp",
        "<Timestamps>1</Timestamps>",
        "<CustomTimestamp>2026-11-14T19:30:09+01:00</CustomTimestamp>",
        "<CustomTimestampEndEnabled>true</CustomTimestampEndEnabled>",
        "<CustomTimestampEnd>not a time</CustomTimestampEnd>",
    )

    assert load_preset(path).presence.timestamps == Timestamps(mode=TimestampMode.SINCE_START)


def test_load_preset_ignores_the_end_time_when_it_is_disabled(tmp_path: Path):
    path = write_preset(
        tmp_path / "p.crp",
        "<Timestamps>3</Timestamps>",
        "<CustomTimestamp>2026-11-14T19:30:09+01:00</CustomTimestamp>",
        "<CustomTimestampEndEnabled>false</CustomTimestampEndEnabled>",
        "<CustomTimestampEnd>2063-12-28T19:30:09</CustomTimestampEnd>",
    )

    assert load_preset(path).presence.timestamps == Timestamps(
        mode=TimestampMode.CUSTOM, start=1794681009, end=None
    )


def test_load_preset_keeps_only_buttons_with_label_and_url(tmp_path: Path):
    path = write_preset(
        tmp_path / "p.crp",
        "<Button1Text>Label only</Button1Text>",
        "<Button2Text>Both</Button2Text>",
        "<Button2URL>https://example.com</Button2URL>",
    )

    assert load_preset(path).presence.buttons == [Button("Both", "https://example.com")]


def test_load_preset_ignores_unknown_elements(tmp_path: Path):
    path = write_preset(tmp_path / "p.crp", "<FutureField>x</FutureField>", "<Name>Known</Name>")

    assert load_preset(path).presence.name == "Known"


@pytest.mark.parametrize(
    ("element", "message"),
    [
        ("<Type>1</Type>", "Type: unknown activity type"),
        ("<Display>3</Display>", "Display: unknown status display"),
        ("<Timestamps>5</Timestamps>", "Timestamps: unknown timestamp mode"),
        ("<PartySize>two</PartySize>", "PartySize: expected an integer"),
        ("<PartyMax>3_0</PartyMax>", "PartyMax: expected an integer"),
        (
            "<Timestamps>3</Timestamps><CustomTimestampEndEnabled>yes</CustomTimestampEndEnabled>",
            "CustomTimestampEndEnabled: expected true or false",
        ),
        (
            "<Timestamps>3</Timestamps><CustomTimestamp>yesterday</CustomTimestamp>",
            "CustomTimestamp: expected a date and time",
        ),
    ],
)
def test_load_preset_refuses_a_bad_field_and_names_it(tmp_path: Path, element: str, message: str):
    path = write_preset(tmp_path / "bad.crp", element)

    with pytest.raises(StorageError, match=re.escape(f"bad.crp: {message}")):
        load_preset(path)


def test_load_preset_refuses_a_file_that_is_not_xml(tmp_path: Path):
    path = tmp_path / "p.crp"
    path.write_text("<Preset>", encoding="utf-8")

    with pytest.raises(StorageError, match=re.escape("not valid XML")):
        load_preset(path)


def test_load_preset_refuses_another_root_element():
    with pytest.raises(StorageError, match=re.escape("expected a <Preset> element")):
        load_preset(SETTINGS)


def test_load_preset_wraps_a_missing_file(tmp_path: Path):
    with pytest.raises(StorageError, match=re.escape("cannot read")):
        load_preset(tmp_path / "missing.crp")


def test_load_all_loads_every_preset_of_a_directory_sorted_by_name(tmp_path: Path):
    write_preset(tmp_path / "b.crp", "<Name>B</Name>")
    write_preset(tmp_path / "a.crp", "<Name>A</Name>")
    (tmp_path / "notes.txt").write_text("not a preset", encoding="utf-8")

    assert [f.name for f in load_all(tmp_path)] == ["a", "b"]


def test_load_all_fails_as_a_whole_on_one_broken_preset(tmp_path: Path):
    write_preset(tmp_path / "good.crp")
    write_preset(tmp_path / "broken.crp", "<Type>9</Type>")

    with pytest.raises(StorageError, match=re.escape("broken.crp")):
        load_all(tmp_path)


def test_load_all_refuses_a_missing_directory(tmp_path: Path):
    with pytest.raises(StorageError, match=re.escape("not a directory")):
        load_all(tmp_path / "missing")


def test_default_config_paths_finds_every_settings_file_under_the_root(tmp_path: Path):
    first = tmp_path / "maximmax42" / "CustomRP.exe_Url_aaa" / "1.0.0.0" / "user.config"
    second = tmp_path / "maximmax42" / "CustomRP.exe_Url_bbb" / "1.0.0.0" / "user.config"
    for path in (first, second):
        path.parent.mkdir(parents=True)
        shutil.copy(SETTINGS, path)
    (tmp_path / "maximmax42" / "Other.exe_Url_ccc").mkdir()

    assert default_config_paths(tmp_path) == [first, second]


def test_default_config_paths_is_empty_when_customrp_never_ran(tmp_path: Path):
    assert default_config_paths(tmp_path) == []
