from typing import NoReturn

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table

console = Console()


# Time for some fancy printing!!!
def table(title: str, columns: list[str]) -> Table:
    result = Table(title=title, title_justify="left", header_style="bold")

    for column in columns:
        result.add_column(column)

    return result


def error(message: str) -> None:
    console.print(f"[bold red]error[/bold red] {escape(message)}")


def success(message: str) -> None:
    console.print(f"[bold green]ok[/bold green] {escape(message)}")


def fail(message: str) -> NoReturn:
    error(message)

    raise typer.Exit(1)
