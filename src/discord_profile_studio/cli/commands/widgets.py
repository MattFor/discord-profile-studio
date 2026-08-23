import typer

app = typer.Typer(no_args_is_help=True)


@app.command("list")
def list_kinds() -> None:
    raise NotImplementedError


@app.command()
def add(favourite: str, kind: str) -> None:
    raise NotImplementedError


@app.command()
def remove(favourite: str, index: int) -> None:
    raise NotImplementedError
