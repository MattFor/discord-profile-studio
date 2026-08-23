from typing import Final

FONT_FAMILY: Final[str] = ""

DARK: Final[dict[str, str]] = {}
LIGHT: Final[dict[str, str]] = {}


def palette(name: str) -> dict[str, str]:
    raise NotImplementedError


def apply(root: object, name: str) -> None:
    raise NotImplementedError
