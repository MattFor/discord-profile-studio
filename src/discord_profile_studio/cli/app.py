import importlib
import pkgutil

import typer

from discord_profile_studio.cli import commands
from discord_profile_studio.core.logging import get, setup

app = typer.Typer(
    name="dps",
    no_args_is_help=True,
    add_completion=True,
    rich_markup_mode=None,
)

log = get(__name__)

COMMAND_NAMES = {
    "widgets": "widget",
    "favourites": "fav",
}

# Dynamic module loading
for module_info in pkgutil.iter_modules(commands.__path__):
    module_name = module_info.name

    if module_name.startswith("_"):
        continue

    module = importlib.import_module(f"{commands.__name__}.{module_name}")

    if not hasattr(module, "app"):
        continue

    command_name = COMMAND_NAMES.get(module_name, module_name)

    app.add_typer(module.app, name=command_name)


@app.callback()
def root(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    setup(verbose=verbose)

    if ctx.invoked_subcommand:
        log.info("running command: %s", ctx.invoked_subcommand)
    else:
        log.info("running dps")


def main() -> None:
    app()
