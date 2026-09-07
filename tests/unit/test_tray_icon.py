import threading
import time
from pathlib import Path
from typing import NamedTuple

import pytest

from discord_profile_studio.assets import TRAY_CONNECTED, TRAY_IDLE
from discord_profile_studio.core.paths import APP_NAME
from discord_profile_studio.tray.backends.base import TrayBackend
from discord_profile_studio.tray.icon import TrayIcon
from discord_profile_studio.tray.menu import TrayMenu, TrayMenuItem

WAIT = 2.0
POLL = 0.01

pytestmark = pytest.mark.filterwarnings("ignore::pytest.PytestUnhandledThreadExceptionWarning")


class Call(NamedTuple):
    kind: str
    menu: TrayMenu | None = None
    path: Path | None = None
    tooltip: str = ""


class FakeBackend(TrayBackend):
    name = "fake"

    def __init__(self) -> None:
        self.calls: list[Call] = []
        self.started = threading.Event()
        self.released = threading.Event()

    def available(self) -> bool:
        return True

    def run(self, menu: TrayMenu, icon_path: Path, tooltip: str) -> None:
        self.calls.append(Call("run", menu, icon_path, tooltip))
        self.started.set()
        self.released.wait(timeout=WAIT)

    def update(self, menu: TrayMenu, icon_path: Path, tooltip: str) -> None:
        self.calls.append(Call("update", menu, icon_path, tooltip))

    def stop(self) -> None:
        self.calls.append(Call("stop"))
        self.released.set()


class ExplodingBackend(FakeBackend):
    def run(self, menu: TrayMenu, icon_path: Path, tooltip: str) -> None:
        self.calls.append(Call("run", menu, icon_path, tooltip))
        self.started.set()
        msg = "backend died"
        raise RuntimeError(msg)


def labels(menu: TrayMenu | None) -> tuple[str, ...]:
    assert menu is not None

    return tuple(item.label for item in menu.items)


def kinds(backend: FakeBackend) -> list[str]:
    return [call.kind for call in backend.calls]


def updates(backend: FakeBackend) -> list[Call]:
    return [call for call in backend.calls if call.kind == "update"]


@pytest.fixture
def backend() -> FakeBackend:
    return FakeBackend()


@pytest.fixture
def menu() -> TrayMenu:
    return TrayMenu(items=[TrayMenuItem(label="Show"), TrayMenuItem(label="Quit")])


@pytest.fixture
def icon(menu: TrayMenu, backend: FakeBackend):
    tray = TrayIcon(menu, backend)
    yield tray
    tray.stop()


def launch(icon: TrayIcon, backend: FakeBackend) -> None:
    backend.started.clear()
    icon.start()

    assert backend.started.wait(timeout=WAIT)


def settle(icon: TrayIcon) -> None:
    deadline = time.monotonic() + WAIT

    while icon.running and time.monotonic() < deadline:
        time.sleep(POLL)


def test_a_fresh_icon_is_not_running(icon: TrayIcon) -> None:
    assert icon.running is False


def test_start_marks_the_icon_as_running(icon: TrayIcon, backend: FakeBackend) -> None:
    launch(icon, backend)

    assert icon.running is True


def test_start_hands_the_menu_to_the_backend(icon: TrayIcon, backend: FakeBackend) -> None:
    launch(icon, backend)

    assert backend.calls[0].kind == "run"
    assert labels(backend.calls[0].menu) == ("Show", "Quit")


def test_start_uses_the_idle_icon_by_default(icon: TrayIcon, backend: FakeBackend) -> None:
    launch(icon, backend)

    assert backend.calls[0].path == TRAY_IDLE


def test_start_defaults_the_tooltip_to_the_app_name(icon: TrayIcon, backend: FakeBackend) -> None:
    launch(icon, backend)

    assert backend.calls[0].tooltip == APP_NAME


def test_start_is_idempotent(icon: TrayIcon, backend: FakeBackend) -> None:
    launch(icon, backend)
    icon.start()

    assert kinds(backend).count("run") == 1


def test_start_selects_a_backend_when_none_was_given(
    monkeypatch: pytest.MonkeyPatch, menu: TrayMenu, backend: FakeBackend
) -> None:
    monkeypatch.setattr("discord_profile_studio.tray.icon.select", lambda: backend)
    tray = TrayIcon(menu)

    try:
        launch(tray, backend)

        assert tray.backend is backend
    finally:
        tray.stop()


def test_start_keeps_an_explicit_backend(icon: TrayIcon, backend: FakeBackend) -> None:
    launch(icon, backend)

    assert icon.backend is backend


def test_stop_clears_the_running_flag(icon: TrayIcon, backend: FakeBackend) -> None:
    launch(icon, backend)
    icon.stop()

    assert icon.running is False


def test_stop_tells_the_backend_to_stop(icon: TrayIcon, backend: FakeBackend) -> None:
    launch(icon, backend)
    icon.stop()

    assert "stop" in kinds(backend)


def test_stop_before_start_does_nothing(icon: TrayIcon, backend: FakeBackend) -> None:
    icon.stop()

    assert backend.calls == []


def test_stop_is_idempotent(icon: TrayIcon, backend: FakeBackend) -> None:
    launch(icon, backend)
    icon.stop()
    icon.stop()

    assert kinds(backend).count("stop") == 1


def test_the_icon_can_be_restarted(icon: TrayIcon, backend: FakeBackend) -> None:
    launch(icon, backend)
    icon.stop()
    backend.released.clear()
    launch(icon, backend)

    assert kinds(backend).count("run") == 2


def test_a_failing_backend_leaves_the_icon_stopped(menu: TrayMenu) -> None:
    backend = ExplodingBackend()
    tray = TrayIcon(menu, backend)
    launch(tray, backend)
    settle(tray)

    assert tray.running is False


def test_a_tooltip_set_before_start_reaches_the_backend(
    icon: TrayIcon, backend: FakeBackend
) -> None:
    icon.set_tooltip("waiting")
    launch(icon, backend)

    assert backend.calls[0].tooltip == "waiting"


def test_setting_a_tooltip_before_start_does_not_update(
    icon: TrayIcon, backend: FakeBackend
) -> None:
    icon.set_tooltip("waiting")

    assert backend.calls == []


def test_setting_a_new_tooltip_updates_the_backend(icon: TrayIcon, backend: FakeBackend) -> None:
    launch(icon, backend)
    icon.set_tooltip("connected")

    assert updates(backend)[-1].tooltip == "connected"


def test_setting_the_same_tooltip_is_ignored(icon: TrayIcon, backend: FakeBackend) -> None:
    launch(icon, backend)
    icon.set_tooltip("connected")
    icon.set_tooltip("connected")

    assert len(updates(backend)) == 1


def test_connecting_switches_to_the_connected_icon(icon: TrayIcon, backend: FakeBackend) -> None:
    launch(icon, backend)
    icon.set_state(connected=True)

    assert updates(backend)[-1].path == TRAY_CONNECTED


def test_disconnecting_switches_back_to_the_idle_icon(icon: TrayIcon, backend: FakeBackend) -> None:
    launch(icon, backend)
    icon.set_state(connected=True)
    icon.set_state(connected=False)

    assert updates(backend)[-1].path == TRAY_IDLE


def test_setting_the_same_state_is_ignored(icon: TrayIcon, backend: FakeBackend) -> None:
    launch(icon, backend)
    icon.set_state(connected=True)
    icon.set_state(connected=True)

    assert len(updates(backend)) == 1


def test_state_set_before_start_reaches_the_backend(icon: TrayIcon, backend: FakeBackend) -> None:
    icon.set_state(connected=True)
    launch(icon, backend)

    assert backend.calls[0].path == TRAY_CONNECTED


def test_without_a_callback_the_menu_is_passed_through(
    icon: TrayIcon, backend: FakeBackend, menu: TrayMenu
) -> None:
    launch(icon, backend)

    assert backend.calls[0].menu is menu


def test_on_activate_prepends_an_entry(icon: TrayIcon, backend: FakeBackend) -> None:
    icon.on_activate(lambda: None)
    launch(icon, backend)

    assert labels(backend.calls[0].menu) == (APP_NAME, "Show", "Quit")


def test_the_activate_entry_is_the_default_one(icon: TrayIcon, backend: FakeBackend) -> None:
    icon.on_activate(lambda: None)
    launch(icon, backend)
    composed = backend.calls[0].menu

    assert composed is not None
    assert composed.items[0].default is True


def test_the_activate_entry_is_hidden(icon: TrayIcon, backend: FakeBackend) -> None:
    icon.on_activate(lambda: None)
    launch(icon, backend)
    composed = backend.calls[0].menu

    assert composed is not None
    assert composed.items[0].visible is False


def test_the_activate_entry_runs_the_callback(icon: TrayIcon, backend: FakeBackend) -> None:
    seen: list[str] = []
    icon.on_activate(lambda: seen.append("clicked"))
    launch(icon, backend)
    composed = backend.calls[0].menu

    assert composed is not None
    action = composed.items[0].action

    assert action is not None
    action()

    assert seen == ["clicked"]


def test_composing_does_not_touch_the_original_menu(
    icon: TrayIcon, backend: FakeBackend, menu: TrayMenu
) -> None:
    icon.on_activate(lambda: None)
    launch(icon, backend)
    icon.set_tooltip("again")

    assert labels(menu) == ("Show", "Quit")


def test_on_activate_updates_a_running_icon(icon: TrayIcon, backend: FakeBackend) -> None:
    launch(icon, backend)
    icon.on_activate(lambda: None)

    assert labels(updates(backend)[-1].menu) == (APP_NAME, "Show", "Quit")
