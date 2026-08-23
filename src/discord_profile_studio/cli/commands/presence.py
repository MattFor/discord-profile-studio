import typer

app = typer.Typer(no_args_is_help=True)


@app.command()
def apply(name: str) -> None:
    raise NotImplementedError


@app.command()
def run(name: str) -> None:
    raise NotImplementedError


@app.command()
def clear() -> None:
    raise NotImplementedError


@app.command()
def status() -> None:
    raise NotImplementedError
