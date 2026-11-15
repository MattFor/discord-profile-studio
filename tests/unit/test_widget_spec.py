import json
import re
from typing import Any

import pytest

from discord_profile_studio.core.exceptions import WidgetError
from discord_profile_studio.models import FieldType, WidgetField
from discord_profile_studio.widgets.spec import from_payload, problems, spec, to_payload
from tests.conftest import WIDGET_CONFIG

TEXT, NUMBER, IMAGE = FieldType.TEXT, FieldType.NUMBER, FieldType.IMAGE
WANTED = {"rank": TEXT, "level": NUMBER, "cover": IMAGE}


def config_with(*fields: dict[str, Any]) -> dict[str, Any]:
    return {"surfaces": [{"components": [{"fields": list(fields)}]}]}


def data(name: object, presentation: object) -> dict[str, Any]:
    return {"value_type": "data", "value": name, "presentation_type": presentation}


def sample(*entries: object) -> dict[str, Any]:
    return {"data": {"dynamic": list(entries)}}


def test_spec_collects_user_data_and_skips_custom_strings():
    assert spec(WIDGET_CONFIG) == WANTED


def test_spec_finds_user_data_at_any_depth_and_in_id_keyed_objects():
    keyed = {"surfaces": {"main": {"components": {"top": {"fields": {"a": data("rank", "text")}}}}}}
    elsewhere = {"layout": [{"slots": [[data("level", "number")]]}]}

    assert spec(keyed) == {"rank": TEXT}
    assert spec(elsewhere) == {"level": NUMBER}


@pytest.mark.parametrize("config", [{}, [], None, {"surfaces": "x"}])
def test_spec_of_a_config_without_surfaces_is_empty(config: object):
    assert spec(config) == {}


@pytest.mark.parametrize("presentation", ["chart", None, ["text"]])
def test_spec_refuses_an_unknown_presentation(presentation: object):
    with pytest.raises(WidgetError, match="'rank' has an unknown presentation_type"):
        spec(config_with(data("rank", presentation)))


def test_spec_refuses_a_key_shown_as_two_types():
    with pytest.raises(WidgetError, match="'rank' is shown as both text and an image"):
        spec(config_with(data("rank", "text"), data("rank", "image")))


@pytest.mark.parametrize("key", ["", "  ", None, 5])
def test_spec_refuses_user_data_without_a_key(key: object):
    with pytest.raises(WidgetError, match="a user data field has no key"):
        spec(config_with(data(key, "text")))


def test_problems_is_empty_when_every_field_fits():
    fields = [
        WidgetField("rank", TEXT, "Gold"),
        WidgetField("level", NUMBER, "42"),
        WidgetField("cover", IMAGE, "https://example.com/a.png"),
        WidgetField("unused", TEXT, ""),
    ]

    assert problems(fields, WANTED) == []


@pytest.mark.parametrize(
    ("field", "expected"),
    [
        pytest.param(None, "level: missing, the widget shows a number here", id="missing"),
        pytest.param(WidgetField("level", TEXT, "x"), "this is text", id="wrong-kind"),
        pytest.param(WidgetField("level", NUMBER, "  "), "level: no value yet", id="blank"),
        pytest.param(WidgetField("level", NUMBER, "lots"), "expected a number", id="not-a-number"),
        pytest.param(WidgetField("level", NUMBER, "nan"), "expected a number", id="nan"),
    ],
)
def test_problems_names_what_is_wrong_with_a_number(field: WidgetField | None, expected: str):
    found = problems([field] if field else [], {"level": NUMBER})

    assert len(found) == 1
    assert expected in found[0]


def test_problems_wants_a_web_url_for_an_image():
    found = problems([WidgetField("cover", IMAGE, "ftp://example.com/a.png")], {"cover": IMAGE})

    assert found == ["cover: expected an image URL, got 'ftp://example.com/a.png'"]


def test_to_payload_writes_discord_type_codes_and_value_shapes():
    fields = [
        WidgetField("rank", TEXT, "Gold"),
        WidgetField("level", NUMBER, "42"),
        WidgetField("ratio", NUMBER, "0.5"),
        WidgetField("cover", IMAGE, " https://example.com/a.png "),
    ]

    assert to_payload(fields) == sample(
        {"name": "rank", "type": 1, "value": "Gold"},
        {"name": "level", "type": 2, "value": 42},
        {"name": "ratio", "type": 2, "value": 0.5},
        {"name": "cover", "type": 3, "value": {"url": "https://example.com/a.png"}},
    )


def test_to_payload_refuses_a_number_that_is_not_one():
    with pytest.raises(WidgetError, match="level: expected a number"):
        to_payload([WidgetField("level", NUMBER, "lots")])


def test_payload_survives_a_round_trip_through_json():
    fields = [
        WidgetField("rank", TEXT, "Gold"),
        WidgetField("level", NUMBER, "42"),
        WidgetField("ratio", NUMBER, "0.5"),
        WidgetField("cover", IMAGE, "https://example.com/a.png"),
    ]

    assert from_payload(json.loads(json.dumps(to_payload(fields)))) == fields


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        pytest.param({}, '{"data": {"dynamic": [...]}}', id="no-data"),
        pytest.param({"data": {"dynamic": {}}}, '{"data": {"dynamic"', id="object-for-dynamic"),
        pytest.param(sample("rank"), "data.dynamic[0]: expected an object", id="str-entry"),
        pytest.param(sample({"name": " ", "type": 1, "value": "x"}), "[0].name", id="blank-name"),
        pytest.param(sample({"name": "a", "type": 4, "value": "x"}), "[0].type", id="type-4"),
        pytest.param(sample({"name": "a", "type": True, "value": "x"}), "[0].type", id="bool-type"),
        pytest.param(sample({"name": "a", "type": 1, "value": 5}), "a string", id="int-text"),
        pytest.param(sample({"name": "a", "type": 2, "value": True}), "a number", id="bool-num"),
        pytest.param(sample({"name": "a", "type": 2, "value": "5"}), "a number", id="str-num"),
        pytest.param(
            sample({"name": "a", "type": 3, "value": "https://x"}), '{"url"', id="str-img"
        ),
    ],
)
def test_from_payload_refuses_malformed_sample_data(payload: object, message: str):
    with pytest.raises(WidgetError, match=re.escape(message)):
        from_payload(payload)
