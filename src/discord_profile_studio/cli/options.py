import typer

CLIENT_ID = typer.Option(None, "--client-id", "-c")
NAME = typer.Argument(..., metavar="NAME")
DETAILS = typer.Option(None, "--details", "-d")
STATE = typer.Option(None, "--state", "-s")
LARGE_IMAGE = typer.Option(None, "--large-image")
SMALL_IMAGE = typer.Option(None, "--small-image")
JSON_OUTPUT = typer.Option(False, "--json")
BACKEND = typer.Option(None, "--backend", "-b")
