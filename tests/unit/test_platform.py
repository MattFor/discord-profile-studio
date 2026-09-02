import sys

import pytest

from discord_profile_studio.system.platform import (
    Platform,
    current,
    desktop_session,
    has_display,
    is_linux,
    is_windows,
)

DESKTOP_VARS = ("XDG_CURRENT_DESKTOP", "XDG_SESSION_DESKTOP", "DESKTOP_SESSION")
DISPLAY_VARS = ("WAYLAND_DISPLAY", "DISPLAY")


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch):
    for name in (*DESKTOP_VARS, *DISPLAY_VARS):
        monkeypatch.delenv(name, raising=False)


def test_platform_members_compare_as_strings():
    assert Platform.WINDOWS == "windows"
    assert f"{Platform.LINUX}" == "linux"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("win32", Platform.WINDOWS),
        ("linux", Platform.LINUX),
        ("darwin", Platform.MACOS),
        ("freebsd14", Platform.UNKNOWN),
        ("emscripten", Platform.UNKNOWN),
        ("", Platform.UNKNOWN),
    ],
)
def test_current_maps_sys_platform(monkeypatch: pytest.MonkeyPatch, raw, expected):
    monkeypatch.setattr(sys, "platform", raw)

    assert current() is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("win32", Platform.WINDOWS),
        ("linux", Platform.LINUX),
        ("darwin", Platform.MACOS),
        ("freebsd14", Platform.UNKNOWN),
    ],
)
def test_predicates_follow_current(
    monkeypatch: pytest.MonkeyPatch, raw: str, expected: Platform
) -> None:
    monkeypatch.setattr(sys, "platform", raw)

    assert is_windows() is (expected is Platform.WINDOWS)
    assert is_linux() is (expected is Platform.LINUX)


def test_desktop_session_returns_empty_when_unset():
    assert desktop_session() == ""


def test_desktop_session_lowercases_value(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "GNOME")

    assert desktop_session() == "gnome"


def test_desktop_session_takes_first_entry_of_colon_list(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "ubuntu:GNOME")

    assert desktop_session() == "ubuntu"


def test_desktop_session_strips_whitespace(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "  KDE  ")

    assert desktop_session() == "kde"


def test_desktop_session_prefers_xdg_current_desktop(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "GNOME")
    monkeypatch.setenv("XDG_SESSION_DESKTOP", "kde")
    monkeypatch.setenv("DESKTOP_SESSION", "xfce")

    assert desktop_session() == "gnome"


def test_desktop_session_falls_back_to_session_desktop(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("XDG_SESSION_DESKTOP", "KDE")
    monkeypatch.setenv("DESKTOP_SESSION", "xfce")

    assert desktop_session() == "kde"


def test_desktop_session_falls_back_to_desktop_session(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DESKTOP_SESSION", "XFCE")

    assert desktop_session() == "xfce"


def test_desktop_session_skips_blank_variables(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("XDG_CURRENT_DESKTOP", "")
    monkeypatch.setenv("XDG_SESSION_DESKTOP", "   ")
    monkeypatch.setenv("DESKTOP_SESSION", "sway")

    assert desktop_session() == "sway"


def test_desktop_session_returns_empty_when_all_blank(monkeypatch: pytest.MonkeyPatch):
    for name in DESKTOP_VARS:
        monkeypatch.setenv(name, "")

    assert desktop_session() == ""


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("win32", True),
        ("darwin", True),
        ("freebsd14", False),
        ("", False),
    ],
)
def test_has_display_off_linux_ignores_environment(monkeypatch: pytest.MonkeyPatch, raw, expected):
    monkeypatch.setattr(sys, "platform", raw)

    assert has_display() is expected


@pytest.mark.parametrize("name", ["WAYLAND_DISPLAY", "DISPLAY"])
def test_has_display_on_linux_accepts_either_server(monkeypatch: pytest.MonkeyPatch, name):
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv(name, ":0")

    assert has_display() is True


def test_has_display_on_linux_accepts_both_servers(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    monkeypatch.setenv("DISPLAY", ":0")

    assert has_display() is True


def test_has_display_on_linux_without_session(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(sys, "platform", "linux")

    assert has_display() is False


def test_has_display_on_linux_ignores_blank_variables(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("WAYLAND_DISPLAY", "")
    monkeypatch.setenv("DISPLAY", "")

    assert has_display() is False


@pytest.mark.parametrize("raw", ["win32", "darwin"])
def test_has_display_true_on_desktop_platforms(monkeypatch: pytest.MonkeyPatch, raw: str) -> None:
    monkeypatch.setattr(sys, "platform", raw)

    assert has_display() is True


@pytest.mark.parametrize("raw", ["freebsd14", ""])
def test_has_display_false_on_unknown_platform(monkeypatch: pytest.MonkeyPatch, raw: str) -> None:
    monkeypatch.setattr(sys, "platform", raw)

    assert has_display() is False
