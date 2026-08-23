import typer

app = typer.Typer(no_args_is_help=True)


@app.command()
def show() -> None:
    raise NotImplementedError


@app.command("set")
def set_(key: str, value: str) -> None:
    raise NotImplementedError


@app.command()
def path() -> None:
    raise NotImplementedError
