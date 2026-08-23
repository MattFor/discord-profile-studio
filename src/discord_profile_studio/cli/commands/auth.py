import typer

app = typer.Typer(no_args_is_help=True)


@app.command()
def login(account: str, client_id: str = typer.Option(..., "--client-id", "-c")) -> None:
    raise NotImplementedError


@app.command()
def logout(account: str) -> None:
    raise NotImplementedError


@app.command()
def status() -> None:
    raise NotImplementedError


@app.command("list")
def list_accounts() -> None:
    raise NotImplementedError


@app.command()
def store(backend: str | None = typer.Argument(None)) -> None:
    raise NotImplementedError
