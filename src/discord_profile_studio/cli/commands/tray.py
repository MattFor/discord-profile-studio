import typer

app = typer.Typer(no_args_is_help=True)


@app.command()
def run(favourite: str | None = typer.Option(None, "--favourite", "-f")) -> None:
    raise NotImplementedError


@app.command()
def status() -> None:
    raise NotImplementedError


@app.command()
def autostart(enable: bool = typer.Option(True, "--enable/--disable")) -> None:
    raise NotImplementedError
