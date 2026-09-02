from abc import ABC
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pystray
from PIL import Image

from discord_profile_studio.core.paths import APP_NAME
from discord_profile_studio.tray.backends.base import TrayBackend
from discord_profile_studio.tray.menu import TrayMenu, TrayMenuItem


def _callback(action: Callable[[], None] | None) -> Callable[[object, object], None] | None:
    if action is None:
        return None

    def invoke(_icon: object, _item: object) -> None:
        action()

    return invoke


def _checked(*, state: bool | None) -> Callable[[object], bool] | None:
    if state is None:
        return None

    def query(_item: object) -> bool:
        return state

    return query


def _entry(item: TrayMenuItem) -> pystray.MenuItem:
    if item.separator:
        return pystray.Menu.SEPARATOR

    if item.submenu is not None:
        return pystray.MenuItem(
            item.label,
            _convert(item.submenu),
            enabled=item.enabled,
        )

    return pystray.MenuItem(
        item.label,
        _callback(item.action),
        checked=_checked(state=item.checked),
        enabled=item.enabled,
    )


def _convert(items: list[TrayMenuItem]) -> pystray.Menu:
    return pystray.Menu(*(_entry(item) for item in items))


def _image(path: Path) -> Image.Image:
    with Image.open(path) as source:
        return source.convert("RGBA")



class PystrayBackend(TrayBackend, ABC):
    def __init__(self) -> None:
        self._icon: Any = None

    def run(self, menu: TrayMenu, icon_path: Path, tooltip: str) -> None:
        icon = pystray.Icon(
            APP_NAME,
            icon=_image(icon_path),
            title=tooltip,
            menu=_convert(menu.items),
        )

        self._icon = icon
        icon.run()

    def update(self, menu: TrayMenu, icon_path: Path, tooltip: str) -> None:
        icon = self._icon

        if icon is None:
            return

        icon.icon = _image(icon_path)
        icon.title = tooltip
        icon.menu = _convert(menu.items)
        icon.update_menu()

    def stop(self) -> None:
        icon = self._icon

        if icon is None:
            return

        self._icon = None
        icon.stop()
