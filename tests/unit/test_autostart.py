import sys

import pytest

from discord_profile_studio.core.exceptions import AutostartError
from discord_profile_studio.system.autostart.base import START_MINIMIZED
from discord_profile_studio.system.autostart.factory import backend
from discord_profile_studio.system.autostart.linux import DESKTOP_FILE, LinuxAutostart

TEST_VALUE_NAME = "DPS-Test-DoNotUse"

on_windows = pytest.mark.skipif(sys.platform != "win32", reason="requires Windows")
on_linux = pytest.mark.skipif(sys.platform != "linux", reason="requires Linux")


@pytest.fixture
def linux_backend(tmp_path):
    return LinuxAutostart(autostart_dir=tmp_path)


@pytest.fixture
def windows_backend():
    from discord_profile_studio.system.autostart.windows import WindowsAutostart  # noqa: PLC0415

    instance = WindowsAutostart(value_name=TEST_VALUE_NAME)
    instance.disable()
    yield instance
    instance.disable()


@pytest.mark.parametrize(
    "key",
    ["[Desktop Entry]", "Type=Application", "Name=", "Exec=", "Terminal=false"],
)
def test_linux_render_contains_required_keys(linux_backend, key):
    assert key in linux_backend.render_desktop_entry(minimized=True)


def test_linux_render_ends_with_newline(linux_backend):
    assert linux_backend.render_desktop_entry(minimized=True).endswith("\n")


def test_linux_render_includes_flag_when_minimized(linux_backend):
    assert START_MINIMIZED in linux_backend.render_desktop_entry(minimized=True)


def test_linux_render_omits_flag_when_not_minimized(linux_backend):
    assert START_MINIMIZED not in linux_backend.render_desktop_entry(minimized=False)


def test_linux_render_puts_flag_on_exec_line(linux_backend):
    rendered = linux_backend.render_desktop_entry(minimized=True)
    exec_line = next(line for line in rendered.splitlines() if line.startswith("Exec="))
    assert START_MINIMIZED in exec_line


def test_linux_render_disables_terminal(linux_backend):
    assert "Terminal=false" in linux_backend.render_desktop_entry(minimized=True)


def test_linux_enabled_is_false_without_entry(linux_backend):
    assert not linux_backend.enabled()


def test_linux_enable_creates_desktop_file(linux_backend, tmp_path):
    linux_backend.enable(minimized=True)
    assert (tmp_path / DESKTOP_FILE).exists()


def test_linux_enable_sets_enabled(linux_backend):
    linux_backend.enable(minimized=True)
    assert linux_backend.enabled()


def test_linux_enable_writes_rendered_entry(linux_backend, tmp_path):
    linux_backend.enable(minimized=True)
    written = (tmp_path / DESKTOP_FILE).read_text(encoding="utf-8")
    assert written == linux_backend.render_desktop_entry(minimized=True)


def test_linux_enable_twice_keeps_single_file(linux_backend, tmp_path):
    linux_backend.enable(minimized=True)
    linux_backend.enable(minimized=True)
    assert len(list(tmp_path.iterdir())) == 1


def test_linux_enable_creates_missing_directory(tmp_path):
    directory = tmp_path / "missing" / "autostart"
    LinuxAutostart(autostart_dir=directory).enable(minimized=True)
    assert (directory / DESKTOP_FILE).exists()


def test_linux_disable_removes_desktop_file(linux_backend, tmp_path):
    linux_backend.enable(minimized=True)
    linux_backend.disable()
    assert not (tmp_path / DESKTOP_FILE).exists()


def test_linux_disable_without_entry_is_silent(linux_backend):
    linux_backend.disable()
    assert not linux_backend.enabled()


def test_linux_disable_twice_is_silent(linux_backend):
    linux_backend.enable(minimized=True)
    linux_backend.disable()
    linux_backend.disable()
    assert not linux_backend.enabled()


@on_linux
@pytest.mark.linux
def test_linux_default_directory_is_config_autostart():
    assert LinuxAutostart()._dir().parts[-2:] == (".config", "autostart")


def test_backend_returns_linux_on_linux(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    assert isinstance(backend(), LinuxAutostart)


@pytest.mark.parametrize("platform", ["darwin", "freebsd", "cygwin"])
def test_backend_rejects_unsupported_platform(monkeypatch, platform):
    monkeypatch.setattr(sys, "platform", platform)
    with pytest.raises(AutostartError):
        backend()


@on_windows
@pytest.mark.windows
def test_backend_returns_windows_on_win32(monkeypatch):
    from discord_profile_studio.system.autostart.windows import WindowsAutostart  # noqa: PLC0415

    monkeypatch.setattr(sys, "platform", "win32")
    assert isinstance(backend(), WindowsAutostart)


@on_windows
@pytest.mark.windows
def test_windows_enabled_is_false_without_value(windows_backend):
    assert not windows_backend.enabled()


@on_windows
@pytest.mark.windows
def test_windows_enable_sets_enabled(windows_backend):
    windows_backend.enable(minimized=True)
    assert windows_backend.enabled()


@on_windows
@pytest.mark.windows
def test_windows_disable_clears_enabled(windows_backend):
    windows_backend.enable(minimized=True)
    windows_backend.disable()
    assert not windows_backend.enabled()


@on_windows
@pytest.mark.windows
def test_windows_disable_without_value_is_silent(windows_backend):
    windows_backend.disable()
    assert not windows_backend.enabled()


@on_windows
@pytest.mark.windows
def test_windows_enable_writes_flag(windows_backend):
    import winreg  # noqa: PLC0415

    from discord_profile_studio.system.autostart.windows import RUN_KEY  # noqa: PLC0415

    windows_backend.enable(minimized=True)
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ) as key:
        value, _ = winreg.QueryValueEx(key, TEST_VALUE_NAME)
    assert START_MINIMIZED in value
