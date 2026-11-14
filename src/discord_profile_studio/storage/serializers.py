import reprlib
from dataclasses import asdict, fields
from datetime import datetime
from enum import Enum
from typing import Any, NoReturn, Protocol, cast

from discord_profile_studio.core.color import to_hex, to_int
from discord_profile_studio.core.exceptions import StorageError, ValidationError
from discord_profile_studio.models.favourite import Favourite
from discord_profile_studio.models.presence import (
    ActivityType,
    Asset,
    Button,
    Party,
    Presence,
    TimestampMode,
    Timestamps,
)
from discord_profile_studio.models.widget import Widget, WidgetKind

_NOTHING_REQUIRED: frozenset[str] = frozenset()
_FAVOURITE_REQUIRED = frozenset({"name", "created_at", "updated_at"})


class _Reader[T](Protocol):
    def __call__(self, data: object, *, where: str) -> T: ...


def presence_to_dict(presence: Presence) -> dict[str, Any]:
    data = asdict(presence)
    data["activity_type"] = presence.activity_type.value
    data["timestamps"]["mode"] = presence.timestamps.mode.value
    return data


def presence_from_dict(data: object, *, where: str = "presence") -> Presence:
    obj = _object(data, Presence, where)
    default = Presence()
    return Presence(
        client_id=_value(obj, "client_id", str, default.client_id, where),
        activity_type=_enum(obj, "activity_type", ActivityType, default.activity_type, where),
        details=_value(obj, "details", str, default.details, where),
        state=_value(obj, "state", str, default.state, where),
        large_image=_nested(obj, "large_image", _asset, Asset, where),
        small_image=_nested(obj, "small_image", _asset, Asset, where),
        party=_nested(obj, "party", _party, Party, where),
        timestamps=_nested(obj, "timestamps", _timestamps, Timestamps, where),
        buttons=_list(obj, "buttons", _button, where),
    )


def widget_to_dict(widget: Widget) -> dict[str, Any]:
    data = asdict(widget)
    data["kind"] = widget.kind.value
    return data


def widget_from_dict(data: object, *, where: str = "widget") -> Widget:
    obj = _object(data, Widget, where)
    default = Widget()
    return Widget(
        kind=_enum(obj, "kind", WidgetKind, default.kind, where),
        title=_value(obj, "title", str, default.title, where),
        body=_value(obj, "body", str, default.body, where),
        icon=_value(obj, "icon", str, default.icon, where),
        accent=_accent(obj, default.accent, where),
        enabled=_value(obj, "enabled", bool, default.enabled, where),
        options=_options(obj, where),
    )


def favourite_to_dict(favourite: Favourite) -> dict[str, Any]:
    return {
        "name": favourite.name,
        "presence": presence_to_dict(favourite.presence),
        "widgets": [widget_to_dict(widget) for widget in favourite.widgets],
        "tags": list(favourite.tags),
        "created_at": favourite.created_at.isoformat(),
        "updated_at": favourite.updated_at.isoformat(),
    }


def favourite_from_dict(data: object, *, where: str = "favourite") -> Favourite:
    obj = _object(data, Favourite, where, required=_FAVOURITE_REQUIRED)
    return Favourite(
        name=_name(obj, where),
        presence=presence_from_dict(obj.get("presence", {}), where=f"{where}.presence"),
        widgets=_list(obj, "widgets", widget_from_dict, where),
        tags=_list(obj, "tags", _string, where),
        created_at=_moment(obj, "created_at", where),
        updated_at=_moment(obj, "updated_at", where),
    )


def _fail(where: str, problem: str, value: object) -> NoReturn:
    msg = f"{where}: {problem}, got {reprlib.repr(value)}"
    raise StorageError(msg)


def _object(
    data: object,
    model: type,
    where: str,
    required: frozenset[str] = _NOTHING_REQUIRED,
) -> dict[str, Any]:
    if type(data) is not dict:
        _fail(where, "expected an object", data)
    obj = cast("dict[str, Any]", data)
    allowed = {entry.name for entry in fields(model)}
    for key in obj:
        if key not in allowed:
            _fail(f"{where}.{key}", "unknown key", obj[key])
    for key in sorted(required - obj.keys()):
        _fail(f"{where}.{key}", "required key is missing", obj)
    return obj


def _value[T](obj: dict[str, Any], key: str, kind: type[T], default: T, where: str) -> T:
    if key not in obj:
        return default
    value = obj[key]
    if type(value) is not kind:
        _fail(f"{where}.{key}", f"expected {kind.__name__}", value)
    return cast("T", value)


def _enum[E: Enum](obj: dict[str, Any], key: str, enum: type[E], default: E, where: str) -> E:
    raw = _value(obj, key, type(default.value), default.value, where)
    try:
        return enum(raw)
    except ValueError as e:
        msg = f"{where}.{key}: unknown {enum.__name__} value, got {reprlib.repr(raw)}"
        raise StorageError(msg) from e


def _nested[T](
    obj: dict[str, Any],
    key: str,
    read: _Reader[T],
    factory: type[T],
    where: str,
) -> T:
    if key not in obj:
        return factory()
    return read(obj[key], where=f"{where}.{key}")


def _list[T](obj: dict[str, Any], key: str, read: _Reader[T], where: str) -> list[T]:
    items = cast("list[object]", _value(obj, key, list, [], where))
    return [read(item, where=f"{where}.{key}[{i}]") for i, item in enumerate(items)]


def _asset(data: object, *, where: str) -> Asset:
    obj = _object(data, Asset, where)
    return Asset(
        key=_value(obj, "key", str, "", where),
        text=_value(obj, "text", str, "", where),
    )


def _button(data: object, *, where: str) -> Button:
    obj = _object(data, Button, where)
    return Button(
        label=_value(obj, "label", str, "", where),
        url=_value(obj, "url", str, "", where),
    )


def _party(data: object, *, where: str) -> Party:
    obj = _object(data, Party, where)
    return Party(
        size=_value(obj, "size", int, 0, where),
        maximum=_value(obj, "maximum", int, 0, where),
    )


def _timestamps(data: object, *, where: str) -> Timestamps:
    obj = _object(data, Timestamps, where)
    return Timestamps(
        mode=_enum(obj, "mode", TimestampMode, TimestampMode.NONE, where),
        start=_optional_int(obj, "start", where),
        end=_optional_int(obj, "end", where),
    )


def _optional_int(obj: dict[str, Any], key: str, where: str) -> int | None:
    value = obj.get(key)
    if value is None:
        return None
    return _value(obj, key, int, 0, where)


def _name(obj: dict[str, Any], where: str) -> str:
    name = _value(obj, "name", str, "", where)
    if not name.strip():
        _fail(f"{where}.name", "name is blank", name)
    return name


def _string(data: object, *, where: str) -> str:
    if type(data) is not str:
        _fail(where, "expected str", data)
    return data


def _options(obj: dict[str, Any], where: str) -> dict[str, str]:
    if "options" not in obj:
        return {}
    value = obj["options"]
    if type(value) is not dict:
        _fail(f"{where}.options", "expected an object", value)
    options = cast("dict[object, object]", value)
    result: dict[str, str] = {}
    for key, item in options.items():
        name = _string(key, where=f"{where}.options")
        result[name] = _string(item, where=f"{where}.options.{name}")
    return result


def _accent(obj: dict[str, Any], default: str, where: str) -> str:
    raw = _value(obj, "accent", str, default, where)
    try:
        return "#" + to_hex(to_int(raw))
    except ValidationError as e:
        msg = f"{where}.accent: invalid colour, got {reprlib.repr(raw)}"
        raise StorageError(msg) from e


def _moment(obj: dict[str, Any], key: str, where: str) -> datetime:
    raw = _value(obj, key, str, "", where)
    try:
        moment = datetime.fromisoformat(raw)
    except ValueError as e:
        msg = f"{where}.{key}: invalid ISO 8601 timestamp, got {reprlib.repr(raw)}"
        raise StorageError(msg) from e
    if moment.tzinfo is None:
        _fail(f"{where}.{key}", "timestamp has no time zone", raw)
    return moment
