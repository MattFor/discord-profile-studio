import math
import reprlib
from collections.abc import Iterable, Iterator
from contextlib import suppress
from typing import Any, NoReturn, cast

from discord_profile_studio.core.exceptions import WidgetError
from discord_profile_studio.models.widget import FieldType, WidgetField

_NUMERIC = ("number", "integer", "decimal", "double", "float")
PRESENTATIONS = {"text": FieldType.TEXT, "image": FieldType.IMAGE} | dict.fromkeys(
    _NUMERIC,
    FieldType.NUMBER,
)
IMAGE_SCHEMES = ("https://", "http://")

# Data key -> the type of value the widget shows for it
type Spec = dict[str, FieldType]


def spec(config: object) -> Spec:
    found: Spec = {}

    for entry in _objects(config):
        # Custom strings are baked into the config, only user data needs a value
        if entry.get("value_type") != "data":
            continue

        name = _key(entry.get("value"))
        presentation = entry.get("presentation_type")
        kind = PRESENTATIONS.get(presentation) if type(presentation) is str else None

        if kind is None:
            _fail("widget config", f"{name!r} has an unknown presentation_type", presentation)

        if found.setdefault(name, kind) is not kind:
            msg = f"widget config: {name!r} is shown as both {_word(found[name])} and {_word(kind)}"
            raise WidgetError(msg)

    return found


def fit(fields: list[WidgetField], wanted: Spec) -> list[WidgetField]:
    # Later entries win, so a sample listed after stored values overrides them
    known = {field.name: field for field in fields}

    return [
        known[name] if name in known and known[name].kind is kind else WidgetField(name, kind)
        for name, kind in wanted.items()
    ]


def problems(fields: list[WidgetField], wanted: Spec) -> list[str]:
    given = {field.name: field for field in fields}
    found: list[str] = []

    for name, kind in wanted.items():
        field = given.get(name)

        if field is None:
            found.append(f"{name}: missing, the widget shows {_word(kind)} here")
        elif field.kind is not kind:
            found.append(f"{name}: the widget shows {_word(kind)}, this is {_word(field.kind)}")
        elif not field.value.strip():
            found.append(f"{name}: no value yet")
        elif kind is FieldType.NUMBER and number(field.value) is None:
            found.append(f"{name}: expected a number, got {field.value!r}")
        elif kind is FieldType.IMAGE and not field.value.strip().startswith(IMAGE_SCHEMES):
            found.append(f"{name}: expected an image URL, got {field.value!r}")

    return found


def number(text: str) -> int | float | None:
    with suppress(ValueError):
        return int(text)

    try:
        value = float(text)
    except ValueError:
        return None

    return value if math.isfinite(value) else None


def to_payload(fields: list[WidgetField]) -> dict[str, Any]:
    dynamic = [
        {"name": field.name, "type": field.kind.value, "value": _wire(field)} for field in fields
    ]

    return {"data": {"dynamic": dynamic}}


def from_payload(data: object) -> list[WidgetField]:
    inner = cast("dict[str, object]", data).get("data") if type(data) is dict else None
    dynamic = cast("dict[str, object]", inner).get("dynamic") if type(inner) is dict else None

    if type(dynamic) is not list:
        _fail("sample data", 'expected {"data": {"dynamic": [...]}}', data)

    return [
        _field(item, f"data.dynamic[{i}]") for i, item in enumerate(cast("list[object]", dynamic))
    ]


def _objects(node: object) -> Iterator[dict[str, object]]:
    # Every object at any depth, so the exact surfaces/components/fields nesting never matters
    if type(node) is dict:
        obj = cast("dict[str, object]", node)
        yield obj
        children: Iterable[object] = obj.values()
    elif type(node) is list:
        children = cast("list[object]", node)
    else:
        return

    for child in children:
        yield from _objects(child)


def _key(value: object) -> str:
    if type(value) is not str or not value.strip():
        _fail("widget config", "a user data field has no key", value)

    return value


def _wire(field: WidgetField) -> object:
    if field.kind is FieldType.NUMBER:
        value = number(field.value)

        if value is None:
            _fail(field.name, "expected a number", field.value)

        return value

    if field.kind is FieldType.IMAGE:
        return {"url": field.value.strip()}

    return field.value


def _field(item: object, where: str) -> WidgetField:
    if type(item) is not dict:
        _fail(where, "expected an object", item)

    entry = cast("dict[str, object]", item)
    name, code, value = entry.get("name"), entry.get("type"), entry.get("value")

    if type(name) is not str or not name.strip():
        _fail(f"{where}.name", "expected a non-blank string", name)

    if type(code) is not int or code not in FieldType:
        _fail(f"{where}.type", "expected 1 (text), 2 (number) or 3 (image)", code)

    kind = FieldType(code)

    if kind is FieldType.TEXT and type(value) is str:
        return WidgetField(name, kind, value)

    # bool is an int subclass, type() keeps true/false out
    if kind is FieldType.NUMBER and type(value) in {int, float}:
        return WidgetField(name, kind, str(value))

    url = cast("dict[str, object]", value).get("url") if type(value) is dict else None

    if kind is FieldType.IMAGE and type(url) is str:
        return WidgetField(name, kind, url)

    shapes = {
        FieldType.TEXT: "a string",
        FieldType.NUMBER: "a number",
        FieldType.IMAGE: 'an object like {"url": "..."}',
    }
    msg = f"{where}.value: expected {shapes[kind]}, got {reprlib.repr(value)}"
    raise WidgetError(msg)


def _word(kind: FieldType) -> str:
    return {FieldType.TEXT: "text", FieldType.NUMBER: "a number", FieldType.IMAGE: "an image"}[kind]


def _fail(where: str, problem: str, value: object) -> NoReturn:
    msg = f"{where}: {problem}, got {reprlib.repr(value)}"
    raise WidgetError(msg)
