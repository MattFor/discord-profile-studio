import pytest

from discord_profile_studio.core.color import MAX_COLOR, to_hex, to_int
from discord_profile_studio.core.exceptions import ValidationError

BLURPLE = 5793266


@pytest.mark.parametrize(
    ("input_value", "expected"),
    [
        ("#5865F2", BLURPLE),
        ("5865F2", BLURPLE),
        ("#5865f2", BLURPLE),
        ("  #5865F2  ", BLURPLE),
        ("#000000", 0),
        ("#FFFFFF", MAX_COLOR),
    ],
)
def test_to_int_parses_valid_hex(input_value, expected):
    assert to_int(input_value) == expected


@pytest.mark.parametrize(
    "input_value",
    ["", "#", "#12345", "#1234567", "#GGGGGG", "#-12345", "#+12345", "#1_2345", "# 12345"],
)
def test_to_int_rejects_invalid_hex(input_value):
    with pytest.raises(ValidationError):
        to_int(input_value)


@pytest.mark.parametrize("input_value", ["#5865F2", "#5865f2"])
def test_to_int_ignores_case(input_value):
    assert to_int(input_value) == BLURPLE


@pytest.mark.parametrize(
    ("input_value", "expected"),
    [
        (BLURPLE, "5865f2"),
        (0, "000000"),
        (MAX_COLOR, "ffffff"),
        (255, "0000ff"),
    ],
)
def test_to_hex_formats_int(input_value, expected):
    assert to_hex(input_value) == expected


def test_to_hex_omits_hash():
    assert not to_hex(BLURPLE).startswith("#")


def test_to_hex_has_six_characters():
    assert len(to_hex(BLURPLE)) == 6


def test_to_hex_is_lowercase():
    assert to_hex(MAX_COLOR).islower()


@pytest.mark.parametrize("input_value", [-1, MAX_COLOR + 1, 999_999_999])
def test_to_hex_rejects_out_of_range(input_value):
    with pytest.raises(ValidationError):
        to_hex(input_value)


@pytest.mark.parametrize("input_number", [0, 255, BLURPLE, MAX_COLOR])
def test_roundtrip_int_to_hex_to_int(input_number):
    assert to_int(to_hex(input_number)) == input_number


@pytest.mark.parametrize("input_value", ["000000", "5865f2", "ffffff"])
def test_roundtrip_hex_to_int_to_hex(input_value):
    assert to_hex(to_int(input_value)) == input_value


@pytest.mark.parametrize("input_value", ["#000000", "#5865f2", "#ffffff"])
def test_to_int_accepts_prefixed_form_of_to_hex_output(input_value):
    assert to_hex(to_int(input_value)) == input_value.removeprefix("#")
