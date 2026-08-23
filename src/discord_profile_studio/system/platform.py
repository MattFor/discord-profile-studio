from enum import StrEnum


class Platform(StrEnum):
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    UNKNOWN = "unknown"


def current() -> Platform:
    raise NotImplementedError


def is_windows() -> bool:
    raise NotImplementedError


def is_linux() -> bool:
    raise NotImplementedError


def desktop_session() -> str:
    raise NotImplementedError


def has_display() -> bool:
    raise NotImplementedError
