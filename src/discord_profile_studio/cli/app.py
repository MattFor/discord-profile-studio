import typer

from discord_profile_studio.cli.commands import (
    auth,
    config,
    favourites,
    gui,
    presence,
    tray,
    widgets,
)

app = typer.Typer(name="dps", no_args_is_help=True, add_completion=True)
app.add_typer(presence.app, name="presence")
app.add_typer(widgets.app, name="widget")
app.add_typer(favourites.app, name="fav")
app.add_typer(auth.app, name="auth")
app.add_typer(tray.app, name="tray")
app.add_typer(config.app, name="config")
app.add_typer(gui.app, name="gui")


@app.callback()
def root(verbose: bool = typer.Option(False, "--verbose", "-v")) -> None:
    raise NotImplementedError


def main() -> None:
    app()
