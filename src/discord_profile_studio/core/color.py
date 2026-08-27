import re

from discord_profile_studio.core.exceptions import ValidationError

MAX_COLOR = 0xFFFFFF


def to_int(value: str) -> int:
    s = value.strip().removeprefix("#")

    if not re.fullmatch(r"[0-9a-fA-F]{6}", s):
        msg = f"Invalid color value: {value}"
        raise ValidationError(msg)

    return int(s, 16)


def to_hex(value: int) -> str:
    if not (0 <= value <= MAX_COLOR):
        msg = f"Invalid color value: {value}"
        raise ValidationError(msg)
    return f"{value:06x}"
