import json
from typing import Any, cast

import keyring
from keyring.backends import fail
from keyring.errors import KeyringError, PasswordDeleteError

from discord_profile_studio.auth.token import Token
from discord_profile_studio.core.exceptions import AuthError, TokenNotFoundError
from discord_profile_studio.core.logging import get

SERVICE = "discord-profile-studio"
INDEX_KEY = "__accounts__"

log = get(__name__)


class KeyringStore:
    name: str = "keyring"

    def available(self) -> bool:
        try:
            backend = keyring.get_keyring()

            if isinstance(backend, fail.Keyring):
                return False

            keyring.get_password(SERVICE, INDEX_KEY)
        except Exception:
            log.debug("the keyring backend is unusable", exc_info=True)
            return False
        else:
            return True

    def _check(self, account: str) -> str:
        if not account:
            msg = "An account name is required"
            raise AuthError(msg)

        if account == INDEX_KEY:
            msg = f"{INDEX_KEY!r} is reserved and cannot be used as an account name"
            raise AuthError(msg)

        return account

    def _read(self, account: str) -> str | None:
        # From the system keyring
        try:
            return keyring.get_password(SERVICE, account)
        except KeyringError as e:
            msg = f"Could not read from the keyring: {e}"
            raise AuthError(msg) from e

    def _write(self, account: str, payload: str) -> None:
        # To the system keyring
        try:
            keyring.set_password(SERVICE, account, payload)
        except KeyringError as e:
            msg = f"Could not write to the keyring: {e}"
            raise AuthError(msg) from e

    def _index(self) -> list[str]:
        # Keep track of which account names have stored tokens
        raw = self._read(INDEX_KEY)

        if not raw:
            return []

        try:
            entries: Any = json.loads(raw)
        except json.JSONDecodeError:
            # Broken index doe snot prevent keyring usage
            log.warning(
                "the keyring account index is corrupted, starting a new one")
            return []

        if not isinstance(entries, list):
            return []

        return sorted({str(entry) for entry in cast("list[Any]", entries)})

    def _remember(self, account: str) -> None:
        # Add account to index if not present
        entries = self._index()

        if account in entries:
            return

        self._write(INDEX_KEY, json.dumps(sorted([*entries, account])))

    def _forget(self, account: str) -> None:
        entries = [entry for entry in self._index() if entry != account]

        self._write(INDEX_KEY, json.dumps(entries))

    def get(self, account: str) -> Token:
        # Read + deserialise stored token for this account
        raw = self._read(self._check(account))

        if raw is None:
            msg = f"No token is stored for account {account!r}"
            raise TokenNotFoundError(msg)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            msg = f"The stored token for account {account!r} is corrupted"
            raise AuthError(msg) from e

        return Token.from_dict(data)

    def set(self, account: str, token: Token) -> None:
        # Store token and add account to index
        self._check(account)
        self._write(account, json.dumps(token.to_dict()))
        self._remember(account)

    def delete(self, account: str) -> None:
        self._check(account)

        try:
            keyring.delete_password(SERVICE, account)
        except PasswordDeleteError as e:
            msg = f"No token is stored for account {account!r}"
            raise TokenNotFoundError(msg) from e
        except KeyringError as e:
            msg = f"Could not remove the keyring entry: {e}"
            raise AuthError(msg) from e

        # Remove account only upon successful deletions!
        self._forget(account)

    def accounts(self) -> list[str]:
        return self._index()
