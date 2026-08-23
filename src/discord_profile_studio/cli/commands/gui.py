import typer

app = typer.Typer(no_args_is_help=False, invoke_without_command=True)


@app.callback(invoke_without_command=True)
def launch(
    favourite: str | None = typer.Option(None, "--favourite", "-f"),
    minimized: bool = typer.Option(False, "--minimized"),
    tray: bool = typer.Option(True, "--tray/--no-tray"),
) -> None:
    raise NotImplementedError
