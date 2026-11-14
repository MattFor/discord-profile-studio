import re
import reprlib
import xml.etree.ElementTree as ET
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime, tzinfo
from pathlib import Path
from typing import NoReturn, final

from discord_profile_studio.core.exceptions import StorageError
from discord_profile_studio.models.favourite import Favourite
from discord_profile_studio.models.presence import (
    ActivityType,
    Asset,
    Button,
    Party,
    Presence,
    StatusDisplay,
    TimestampMode,
    Timestamps,
)

SETTINGS_NAME = "CustomRP"
SETTINGS_PATTERN = "maximmax42/CustomRP.exe_Url_*/*/user.config"
_SETTINGS_SECTION = "userSettings/CustomRPC.Properties.Settings"
_SETTINGS_TIME_FORMAT = "%m/%d/%Y %H:%M:%S"
_INTEGER = re.compile(r"-?[0-9]+")
_BOOLEANS = {"true": True, "1": True, "false": False, "0": False}

_TIMESTAMP_MODES = {
    0: TimestampMode.SINCE_CONNECT,
    1: TimestampMode.SINCE_START,
    2: TimestampMode.LOCAL_TIME,
    3: TimestampMode.CUSTOM,
    4: TimestampMode.SINCE_UPDATE,
}

type _ParseTime = Callable[[str], datetime]


def default_config_paths(root: Path) -> list[Path]:
    return sorted(path for path in root.glob(SETTINGS_PATTERN) if path.is_file())


def load_preset(path: Path, *, tz: tzinfo | None = None) -> Favourite:
    root = _parse(path)
    if root.tag != "Preset":
        _fail(path, "root", "expected a <Preset> element", root.tag)
    fields = _Fields.of(path, ((child.tag, child.text or "") for child in root))
    presence = _presence(fields, datetime.fromisoformat, tz)
    return Favourite(name=path.stem, presence=presence)


def load_settings(path: Path, *, tz: tzinfo | None = None) -> Favourite:
    section = _parse(path).find(_SETTINGS_SECTION)
    if section is None:
        _fail(path, "root", f"expected {_SETTINGS_SECTION}", None)
    pairs = ((s.get("name", ""), s.findtext("value", "")) for s in section.iter("setting"))
    presence = _presence(_Fields.of(path, pairs), _settings_time, tz)
    return Favourite(name=SETTINGS_NAME, presence=presence)


def load_all(directory: Path, *, tz: tzinfo | None = None) -> list[Favourite]:
    if not directory.is_dir():
        _fail(directory, "directory", "not a directory", str(directory))
    return [load_preset(path, tz=tz) for path in sorted(directory.glob("*.crp"))]


def _parse(path: Path) -> ET.Element:
    try:
        return ET.fromstring(path.read_bytes())  # noqa: S314
    except OSError as e:
        msg = f"{path.name}: cannot read: {e}"
        raise StorageError(msg) from e
    except ET.ParseError as e:
        msg = f"{path.name}: not valid XML: {e}"
        raise StorageError(msg) from e


def _fail(path: Path, field: str, problem: str, value: object) -> NoReturn:
    msg = f"{path.name}: {field}: {problem}, got {reprlib.repr(value)}"
    raise StorageError(msg)


@final
@dataclass(slots=True, frozen=True)
class _Fields:
    path: Path
    values: dict[str, tuple[str, str]]

    @classmethod
    def of(cls, path: Path, pairs: Iterable[tuple[str, str]]) -> "_Fields":
        return cls(path, {name.lower(): (name, text) for name, text in pairs})

    def _get(self, key: str) -> tuple[str, str | None]:
        return self.values.get(key.lower(), (key, None))

    def text(self, key: str) -> str:
        return self._get(key)[1] or ""

    def integer(self, key: str) -> int:
        name, raw = self._get(key)
        if raw is None:
            return 0
        if not _INTEGER.fullmatch(raw.strip()):
            _fail(self.path, name, "expected an integer", raw)
        return int(raw)

    def boolean(self, key: str) -> bool:
        name, raw = self._get(key)
        if raw is None:
            return False
        value = _BOOLEANS.get(raw.strip().lower())
        if value is None:
            _fail(self.path, name, "expected true or false", raw)
        return value

    def choice[T](self, key: str, read: Callable[[int], T], what: str) -> T:
        raw = self.integer(key)
        try:
            return read(raw)
        except (KeyError, ValueError):
            _fail(self.path, self._get(key)[0], f"unknown {what}", raw)

    def seconds(self, key: str, parse: _ParseTime, tz: tzinfo | None) -> int | None:
        name, raw = self._get(key)
        if raw is None:
            return None
        try:
            moment = parse(raw.strip())
            if moment.tzinfo is None:
                moment = moment.astimezone() if tz is None else moment.replace(tzinfo=tz)
            return int(moment.timestamp())
        except (ValueError, OverflowError, OSError):
            _fail(self.path, name, "expected a date and time", raw)


def _settings_time(raw: str) -> datetime:
    return datetime.strptime(raw, _SETTINGS_TIME_FORMAT)  # noqa: DTZ007


def _presence(fields: _Fields, parse: _ParseTime, tz: tzinfo | None) -> Presence:
    return Presence(
        client_id=fields.text("ID"),
        name=fields.text("Name"),
        activity_type=fields.choice("Type", ActivityType, "activity type"),
        status_display=fields.choice("Display", StatusDisplay, "status display"),
        details=fields.text("Details"),
        details_url=fields.text("DetailsURL"),
        state=fields.text("State"),
        state_url=fields.text("StateURL"),
        large_image=_asset(fields, "Large"),
        small_image=_asset(fields, "Small"),
        party=Party(size=fields.integer("PartySize"), maximum=fields.integer("PartyMax")),
        timestamps=_timestamps(fields, parse, tz),
        buttons=_buttons(fields),
    )


def _asset(fields: _Fields, prefix: str) -> Asset:
    return Asset(
        key=fields.text(f"{prefix}Key"),
        text=fields.text(f"{prefix}Text"),
        url=fields.text(f"{prefix}URL"),
    )


def _buttons(fields: _Fields) -> list[Button]:
    buttons = [
        Button(label=fields.text(f"Button{n}Text"), url=fields.text(f"Button{n}URL"))
        for n in (1, 2)
    ]
    return [button for button in buttons if button.label and button.url]


def _timestamps(fields: _Fields, parse: _ParseTime, tz: tzinfo | None) -> Timestamps:
    mode = fields.choice("Timestamps", _TIMESTAMP_MODES.__getitem__, "timestamp mode")
    if mode is not TimestampMode.CUSTOM:
        return Timestamps(mode=mode)
    end = None
    if fields.boolean("CustomTimestampEndEnabled"):
        end = fields.seconds("CustomTimestampEnd", parse, tz)
    return Timestamps(mode=mode, start=fields.seconds("CustomTimestamp", parse, tz), end=end)
