from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass(slots=True)
class TrayMenuItem:
    label: str = ""
    action: Callable[[], None] | None = None
    checked: bool | None = None
    enabled: bool = True
    separator: bool = False
    submenu: "list[TrayMenuItem] | None" = None


@dataclass(slots=True)
class TrayMenu:
    items: list[TrayMenuItem] = field(default_factory=list)

    def add(self, item: TrayMenuItem) -> None:
        raise NotImplementedError

    def rebuild(self) -> None:
        raise NotImplementedError
