from rich.console import Console
from rich.table import Table

console = Console()


def table(title: str, columns: list[str]) -> Table:
    raise NotImplementedError


def error(message: str) -> None:
    raise NotImplementedError


def success(message: str) -> None:
    raise NotImplementedError
