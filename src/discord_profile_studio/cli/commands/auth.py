from typing import NoReturn

import typer

from discord_profile_studio.auth.encrypted_store import EncryptedFileStore
from discord_profile_studio.auth.oauth import (
    DEFAULT_REDIRECT_URI,
    DEFAULT_SCOPES,
    OAuthFlow,
    extract_code,
    new_state,
)
from discord_profile_studio.auth.redaction import mask
from discord_profile_studio.auth.store import (
    TokenStore,
    availability,
    canonical,
    open_store,
)
from discord_profile_studio.auth.token import Token
from discord_profile_studio.cli.console import console, error, success, table
from discord_profile_studio.cli.options import BACKEND
from discord_profile_studio.core import config
from discord_profile_studio.core.exceptions import StudioError
from discord_profile_studio.core.paths import token_file

app = typer.Typer(no_args_is_help=True)


def _fail(message: str) -> NoReturn:
    error(message)

    raise typer.Exit(1)


def _passphrase(store: EncryptedFileStore) -> str:
    if store.initialized:
        return typer.prompt("Store passphrase", hide_input=True)

    console.print(f"Creating a new encrypted token store at {store.path}")

    return typer.prompt("New store passphrase", hide_input=True, confirmation_prompt=True)


def _store(backend: str | None) -> TokenStore:
    store = open_store(backend)

    if isinstance(store, EncryptedFileStore) and store.locked:
        store.unlock(_passphrase(store))

    return store


def _expiry(token: Token) -> str:
    if token.expires_at is None:
        return "never"

    stamp = token.expires_at.isoformat(timespec="seconds")

    return f"{stamp} (expired)" if token.expired else stamp


@app.command()
def login(
    account: str,
    client_id: str = typer.Option(..., "--client-id", "-c"),
    client_secret: str = typer.Option("", "--client-secret"),
    redirect_uri: str = typer.Option(DEFAULT_REDIRECT_URI, "--redirect-uri"),
    scope: list[str] = typer.Option([], "--scope"),
    backend: str | None = BACKEND,
    browser: bool = typer.Option(True, "--browser/--no-browser"),
) -> None:
    secret = client_secret or typer.prompt("Client secret", hide_input=True)
    scopes = tuple(scope) if scope else DEFAULT_SCOPES
    flow = OAuthFlow(client_id, secret, redirect_uri)
    state = new_state()

    try:
        url = flow.authorize_url(scopes, state=state)
        store = _store(backend)

        console.print("Approve the request in a browser:")
        console.print(url)

        if browser:
            typer.launch(url)

        console.print(f"Discord then redirects to {redirect_uri}")

        answer = typer.prompt("Paste the redirect URL or the code")
        token = flow.exchange(extract_code(answer, state))

        store.set(account, token)
        success(f"Stored a token for {account!r} in the {store.name} backend")
    except StudioError as e:
        _fail(str(e))


@app.command()
def logout(
    account: str,
    backend: str | None = BACKEND,
    revoke: bool = typer.Option(False, "--revoke"),
    client_id: str = typer.Option("", "--client-id", "-c"),
    client_secret: str = typer.Option("", "--client-secret"),
    redirect_uri: str = typer.Option(DEFAULT_REDIRECT_URI, "--redirect-uri"),
) -> None:
    try:
        store = _store(backend)
        token = store.get(account)

        if revoke:
            identifier = client_id or typer.prompt("Client id")
            secret = client_secret or typer.prompt("Client secret", hide_input=True)

            OAuthFlow(identifier, secret, redirect_uri).revoke(token)

        store.delete(account)
        success(f"Removed the token for {account!r} from the {store.name} backend")
    except StudioError as e:
        _fail(str(e))


@app.command()
def status(backend: str | None = BACKEND) -> None:
    health = table("Token backends", ["Backend", "Available"])

    for name, ready in availability().items():
        health.add_row(name, "yes" if ready else "no")

    console.print(health)

    try:
        store = _store(backend)
        accounts = store.accounts()

        if not accounts:
            console.print(f"No accounts are stored in the {store.name} backend")
            return

        listing = table(
            f"Accounts in {store.name}",
            ["Account", "Kind", "Scopes", "Expires", "Access token"],
        )

        for account in accounts:
            token = store.get(account)

            listing.add_row(
                account,
                token.kind.value,
                " ".join(token.scopes or []),
                _expiry(token),
                mask(token.access_token),
            )

        console.print(listing)
    except StudioError as e:
        _fail(str(e))


@app.command("list")
def list_accounts(backend: str | None = BACKEND) -> None:
    try:
        store = _store(backend)

        for account in store.accounts():
            console.print(account)
    except StudioError as e:
        _fail(str(e))


@app.command()
def store(backend: str | None = typer.Argument(None)) -> None:
    try:
        settings = config.load()

        if backend is None:
            listing = table("Token backends", ["Backend", "Available", "Selected"])

            for name, ready in availability().items():
                selected = "yes" if name == canonical(settings.token_backend) else ""

                listing.add_row(name, "yes" if ready else "no", selected)

            console.print(listing)
            console.print(f"The encrypted store lives at {token_file()}")
            return

        name = canonical(backend)

        open_store(name)

        settings.token_backend = name
        config.save(settings)

        success(f"The token backend is now {name}")
    except StudioError as e:
        _fail(str(e))
