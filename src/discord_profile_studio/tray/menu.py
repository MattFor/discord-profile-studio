from collections.abc import Callable
from dataclasses import dataclass, field, replace


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
        self.items.append(item)

    def rebuild(self) -> None:
        self.items = _normalise(self.items)


def _normalise(items: list[TrayMenuItem]) -> list[TrayMenuItem]:
    result: list[TrayMenuItem] = []
    for item in items:
        if item.separator:
            if not result:
                continue
            if result[-1].separator:
                continue
            result.append(item)
            continue

        entry = item
        if item.submenu is not None:
            cleaned = _normalise(item.submenu)
            if not cleaned:
                continue
            entry = replace(item, submenu=cleaned)
        result.append(entry)

    while result and result[-1].separator:
        result.pop()
    return result
