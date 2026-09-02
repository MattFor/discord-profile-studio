import os
import sys
from enum import StrEnum
from typing import Final


class Platform(StrEnum):
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    UNKNOWN = "unknown"


_PLATFORMS: Final[dict[str, Platform]] = {
    "win32": Platform.WINDOWS,
    "linux": Platform.LINUX,
    "darwin": Platform.MACOS,
}

_DESKTOP_VARS: Final[tuple[str, ...]] = (
    "XDG_CURRENT_DESKTOP",
    "XDG_SESSION_DESKTOP",
    "DESKTOP_SESSION",
)

_DISPLAY_VARS: Final[tuple[str, ...]] = (
    "WAYLAND_DISPLAY",
    "DISPLAY",
)


def current() -> Platform:
    return _PLATFORMS.get(sys.platform, Platform.UNKNOWN)


def is_windows() -> bool:
    return current() is Platform.WINDOWS


def is_macos() -> bool:
    return current() is Platform.MACOS


def is_linux() -> bool:
    return current() is Platform.LINUX


def desktop_session() -> str:
    for name in _DESKTOP_VARS:
        value = os.environ.get(name, "").strip()
        if not value:
            continue
        # XDG_CURRENT_DESKTOP may be a colon separated list, most specific first?
        return value.partition(":")[0].lower()
    return ""


def has_display() -> bool:
    if not is_linux():
        return current() is not Platform.UNKNOWN

    return any(os.environ.get(name) for name in _DISPLAY_VARS)
