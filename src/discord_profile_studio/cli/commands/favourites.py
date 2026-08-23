from pathlib import Path

import typer

app = typer.Typer(no_args_is_help=True)


@app.command("list")
def list_favourites() -> None:
    raise NotImplementedError


@app.command()
def show(name: str) -> None:
    raise NotImplementedError


@app.command()
def save(name: str) -> None:
    raise NotImplementedError


@app.command()
def delete(name: str) -> None:
    raise NotImplementedError


@app.command("import")
def import_(path: Path, source: str = "customrp") -> None:
    raise NotImplementedError


@app.command("export")
def export(name: str, path: Path) -> None:
    raise NotImplementedError
