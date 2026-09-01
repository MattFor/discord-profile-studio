from typing import Protocol, runtime_checkable

from discord_profile_studio.auth.token import Token
from discord_profile_studio.core import config
from discord_profile_studio.core.exceptions import AuthError, ConfigError
from discord_profile_studio.core.logging import get
from discord_profile_studio.core.paths import token_file

AUTO = "auto"
KEYRING = "keyring"
ENCRYPTED_FILE = "encrypted-file"

BACKENDS = (KEYRING, ENCRYPTED_FILE)
ALIASES = {
    "encrypted": ENCRYPTED_FILE,
    "encrypted_file": ENCRYPTED_FILE,
    "file": ENCRYPTED_FILE,
    "default": AUTO,
}

log = get(__name__)


@runtime_checkable
class TokenStore(Protocol):
    name: str

    def available(self) -> bool: ...

    def get(self, account: str) -> Token: ...

    def set(self, account: str, token: Token) -> None: ...

    def delete(self, account: str) -> None: ...

    def accounts(self) -> list[str]: ...


def canonical(name: str) -> str:
    key = name.strip().lower().replace(" ", "-")
    resolved = ALIASES.get(key, key)

    if resolved not in (AUTO, *BACKENDS):
        known = ", ".join((AUTO, *BACKENDS))
        msg = f"Unknown token backend {name!r}, expected one of: {known}"
        raise AuthError(msg)

    return resolved


def _keyring_store() -> TokenStore:
    from discord_profile_studio.auth.keyring_store import KeyringStore  # noqa: PLC0415

    return KeyringStore()


def _file_store(passphrase: str | None = None) -> TokenStore:
    from discord_profile_studio.auth.encrypted_store import EncryptedFileStore  # noqa: PLC0415

    return EncryptedFileStore(token_file(), passphrase)


def _configured() -> str:
    try:
        name = config.load().token_backend
    except ConfigError:
        log.warning("the settings could not be read, picking a token backend automatically")
        return AUTO

    try:
        return canonical(name)
    except AuthError:
        log.warning("unknown token backend %r in the settings, picking one automatically", name)
        return AUTO


def availability() -> dict[str, bool]:
    return {
        KEYRING: _keyring_store().available(),
        ENCRYPTED_FILE: _file_store().available(),
    }


def open_store(preferred: str | None = None, passphrase: str | None = None) -> TokenStore:
    name = canonical(preferred) if preferred is not None else _configured()

    if name == ENCRYPTED_FILE:
        return _file_store(passphrase)

    store = _keyring_store()

    if store.available():
        return store

    if name == KEYRING and preferred is not None:
        msg = f"The OS keyring is not available here, use the {ENCRYPTED_FILE} backend instead"
        raise AuthError(msg)

    log.warning("the OS keyring is not available, falling back to the %s backend", ENCRYPTED_FILE)

    return _file_store(passphrase)
