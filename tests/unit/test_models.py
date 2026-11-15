from collections.abc import Callable
from dataclasses import fields
from datetime import UTC, datetime
from enum import Enum

import pytest

from discord_profile_studio.core.color import to_hex
from discord_profile_studio.models import (
    Account,
    ActivityType,
    Asset,
    Button,
    Favourite,
    Party,
    Presence,
    Profile,
    StatusDisplay,
    TimestampMode,
    Timestamps,
    Widget,
    WidgetKind,
)


def test_presence_text_fields_default_to_empty_strings():
    presence = Presence()

    assert presence.client_id == ""
    assert presence.name == ""
    assert presence.details == ""
    assert presence.details_url == ""
    assert presence.state == ""
    assert presence.state_url == ""


def test_presence_activity_type_defaults_to_playing():
    assert Presence().activity_type is ActivityType.PLAYING


def test_presence_status_display_defaults_to_activity_name():
    assert Presence().status_display is StatusDisplay.NAME


def test_presence_nested_fields_default_to_empty_objects():
    presence = Presence()

    assert presence.large_image == Asset(key="", text="", url="")
    assert presence.small_image == Asset(key="", text="", url="")
    assert presence.party == Party(size=0, maximum=0)
    assert presence.timestamps == Timestamps(mode=TimestampMode.NONE, start=None, end=None)
    assert presence.buttons == []


def test_timestamps_default_to_no_mode_and_no_bounds():
    timestamps = Timestamps()

    assert timestamps.mode is TimestampMode.NONE
    assert timestamps.start is None
    assert timestamps.end is None


def test_widget_defaults_to_enabled_custom_kind_with_empty_content():
    widget = Widget()

    assert widget.kind is WidgetKind.CUSTOM
    assert widget.enabled is True
    assert widget.title == ""
    assert widget.body == ""
    assert widget.icon == ""
    assert widget.options == {}


def test_widget_default_accent_is_discord_blurple_in_to_hex_spelling():
    assert Widget().accent == "#" + to_hex(0x5865F2)


def test_favourite_defaults_to_unnamed_default_presence_without_widgets_or_tags():
    favourite = Favourite()

    assert favourite.name == ""
    assert favourite.presence == Presence()
    assert favourite.widgets == []
    assert favourite.tags == []


def test_favourite_timestamps_are_taken_at_construction():
    before = datetime.now(UTC)
    favourite = Favourite()
    after = datetime.now(UTC)

    assert before <= favourite.created_at <= after
    assert before <= favourite.updated_at <= after


def test_favourite_timestamps_default_to_aware_utc():
    favourite = Favourite()

    assert favourite.created_at.tzinfo is UTC
    assert favourite.updated_at.tzinfo is UTC


def test_fresh_favourites_always_have_updated_at_equal_to_created_at():
    favourites = [Favourite() for _ in range(10_000)]

    assert all(f.updated_at == f.created_at for f in favourites)


def test_favourite_with_only_created_at_given_copies_it_to_updated_at():
    moment = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)

    assert Favourite(created_at=moment).updated_at == moment


def test_favourite_keeps_explicit_updated_at():
    created = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
    updated = datetime(2026, 2, 3, 4, 5, 6, tzinfo=UTC)

    favourite = Favourite(created_at=created, updated_at=updated)

    assert favourite.created_at == created
    assert favourite.updated_at == updated


def test_profile_defaults_to_version_one_with_no_favourites():
    profile = Profile()

    assert profile.version == 1
    assert profile.active == ""
    assert profile.favourites == []


def test_account_fields_default_to_empty_strings():
    assert Account() == Account(label="", application_id="", user_id="", username="", token_ref="")


def test_presence_buttons_are_not_shared_between_instances():
    first = Presence()
    second = Presence()

    first.buttons.append(Button(label="Join", url="https://example.com"))

    assert second.buttons == []


@pytest.mark.parametrize(
    ("model", "field_name"),
    [
        pytest.param(Presence, "large_image", id="Presence.large_image"),
        pytest.param(Presence, "small_image", id="Presence.small_image"),
        pytest.param(Presence, "party", id="Presence.party"),
        pytest.param(Presence, "timestamps", id="Presence.timestamps"),
        pytest.param(Widget, "options", id="Widget.options"),
        pytest.param(Favourite, "presence", id="Favourite.presence"),
        pytest.param(Favourite, "widgets", id="Favourite.widgets"),
        pytest.param(Favourite, "tags", id="Favourite.tags"),
        pytest.param(Profile, "favourites", id="Profile.favourites"),
    ],
)
def test_mutable_default_is_a_fresh_object_per_instance(
    model: Callable[[], object], field_name: str
):
    assert getattr(model(), field_name) is not getattr(model(), field_name)


@pytest.mark.parametrize(
    ("enum", "expected"),
    [
        pytest.param(
            ActivityType,
            {"PLAYING": 0, "LISTENING": 2, "WATCHING": 3, "COMPETING": 5},
            id="ActivityType",
        ),
        pytest.param(
            StatusDisplay,
            {"NAME": 0, "STATE": 1, "DETAILS": 2},
            id="StatusDisplay",
        ),
        pytest.param(
            TimestampMode,
            {
                "NONE": "none",
                "SINCE_START": "since_start",
                "SINCE_CONNECT": "since_connect",
                "SINCE_UPDATE": "since_update",
                "LOCAL_TIME": "local_time",
                "CUSTOM": "custom",
            },
            id="TimestampMode",
        ),
        pytest.param(
            WidgetKind,
            {
                "STATUS": "status",
                "MEDIA": "media",
                "ACTIVITY": "activity",
                "LINK": "link",
                "CUSTOM": "custom",
            },
            id="WidgetKind",
        ),
    ],
)
def test_enum_members_match_their_wire_values_exactly(
    enum: type[Enum], expected: dict[str, int | str]
):
    assert {member.name: member.value for member in enum} == expected


def test_enum_members_equal_their_plain_values():
    assert ActivityType.LISTENING == 2
    assert TimestampMode.SINCE_START == "since_start"
    assert WidgetKind.LINK == "link"


@pytest.mark.parametrize(
    ("model", "field_name"),
    [
        pytest.param(Presence, "detials", id="Presence"),
        pytest.param(Widget, "titel", id="Widget"),
        pytest.param(Favourite, "tag", id="Favourite"),
    ],
)
def test_setting_unknown_attribute_raises(model: Callable[[], object], field_name: str):
    instance = model()

    with pytest.raises(AttributeError):
        setattr(instance, field_name, "x")


def test_presences_with_equal_field_values_are_equal():
    def build() -> Presence:
        return Presence(
            details="Coding",
            large_image=Asset(key="logo", text="Logo"),
            buttons=[Button(label="Repo", url="https://example.com")],
        )

    first = build()
    second = build()

    assert first is not second
    assert first == second


def test_presences_differing_in_one_nested_field_are_not_equal():
    first = Presence()
    second = Presence()

    second.large_image.key = "logo"

    assert first != second


@pytest.mark.parametrize("field_name", [f.name for f in fields(Favourite)])
def test_favourite_fixture_differs_from_default_in_every_field(
    favourite: Favourite, field_name: str
):
    assert getattr(favourite, field_name) != getattr(Favourite(), field_name)
