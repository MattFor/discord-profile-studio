import base64
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from discord_profile_studio.auth.crypto import (
    KDF_ITERATIONS,
    KDF_NAME,
    decrypt,
    derive_key,
    encrypt,
    new_salt,
)
from discord_profile_studio.auth.token import Token
from discord_profile_studio.core.exceptions import AuthError, StoreLockedError, TokenNotFoundError
from discord_profile_studio.core.paths import ensure_private, write_private

FILE_MODE = 0o600  # Least perms, owner only
VERSION = 1
LOCKED_MESSAGE = "The encrypted token store is locked; unlock it with a passphrase first"


@dataclass(slots=True)
class Envelope:
    salt: bytes
    iterations: int
    payload: bytes


def _encode(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def _decode(raw: str) -> bytes:
    return base64.b64decode(raw, validate=True)


class EncryptedFileStore:
    name: str = "encrypted-file"

    def __init__(self, path: Path, passphrase: str | None = None) -> None:
        self.path: Path = path
        self.passphrase: str | None = passphrase

        # Key is in memory while the unlocking process is going on
        self._key: bytes | None = None
        self._salt: bytes | None = None
        self._iterations: int = KDF_ITERATIONS

    @property
    def initialized(self) -> bool:
        return self.path.exists()

    @property
    def locked(self) -> bool:
        return self._key is None and self.passphrase is None

    def available(self) -> bool:
        # Can the store be accessed with private perms?
        try:
            ensure_private(self.path)
        except OSError:
            return False
        else:
            return True

    def lock(self) -> None:
        # Remove all sensitive stuff from memory
        self.passphrase = None
        self._key = None
        self._salt = None

    def unlock(self, passphrase: str) -> None:
        # The action of deriving the key also verifies that the passphrase can decrypt the store
        self._key = self._derive(passphrase, self._read_envelope())
        self.passphrase = passphrase

    def _read_envelope(self) -> Envelope | None:
        if not self.path.exists():
            return None

        try:
            loaded: Any = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            msg = f"Could not read the token store at {self.path}: {e}"
            raise AuthError(msg) from e

        if not isinstance(loaded, dict):
            msg = f"The token store at {self.path} is malformed"
            raise AuthError(msg)

        raw = cast("dict[str, Any]", loaded)

        # My own version system, anything that doesn't match is out
        version = raw.get("version")

        if version != VERSION:
            msg = f"Unsupported token store version {version!r}, expected {VERSION}"
            raise AuthError(msg)

        # Make sure the expected key derivation method's used
        if raw.get("kdf") != KDF_NAME:
            msg = f"Unsupported key derivation {raw.get('kdf')!r}, expected {KDF_NAME!r}"
            raise AuthError(msg)

        try:
            return Envelope(
                salt=_decode(str(raw["salt"])),
                iterations=int(raw["iterations"]),
                payload=_decode(str(raw["payload"])),
            )
        except (KeyError, TypeError, ValueError) as e:
            msg = f"The token store at {self.path} is malformed"
            raise AuthError(msg) from e

    def _derive(self, passphrase: str, envelope: Envelope | None) -> bytes:
        if envelope is None:
            self._salt = new_salt()
            self._iterations = KDF_ITERATIONS

            return derive_key(passphrase, self._salt, self._iterations)

        key = derive_key(passphrase, envelope.salt, envelope.iterations)
        decrypt(envelope.payload,
                key)  # Correct stores verifies the passphrase is good

        self._salt = envelope.salt
        self._iterations = envelope.iterations

        return key

    def _key_for(self, envelope: Envelope | None) -> bytes:
        if self._key is None:
            if self.passphrase is None:
                raise StoreLockedError(LOCKED_MESSAGE)

            # Lazy derivation when first needed
            self._key = self._derive(self.passphrase, envelope)

        return self._key

    def _records(self) -> dict[str, Any]:
        envelope = self._read_envelope()

        if envelope is None:
            self._key_for(envelope)
            return {}

        plaintext = decrypt(envelope.payload, self._key_for(envelope))

        try:
            data: Any = json.loads(plaintext.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            msg = f"The token store at {self.path} is malformed"
            raise AuthError(msg) from e

        if not isinstance(data, dict):
            msg = f"The token store at {self.path} is malformed"
            raise AuthError(msg)

        accounts: Any = cast("dict[str, Any]", data).get("accounts")

        if not isinstance(accounts, dict):
            msg = f"The token store at {self.path} is malformed"
            raise AuthError(msg)

        return cast("dict[str, Any]", accounts)

    def _write(self, records: dict[str, Any]) -> None:
        # Reuse existing whenever possible
        key = self._key_for(self._read_envelope())
        salt = self._salt

        if salt is None:
            raise StoreLockedError(LOCKED_MESSAGE)

        payload = encrypt(
            json.dumps({
                "accounts": records
            }).encode("utf-8"), key)
        envelope = {
            "version": VERSION,
            "kdf": KDF_NAME,
            "iterations": self._iterations,
            "salt": _encode(salt),
            "payload": _encode(payload),
        }

        try:
            write_private(self.path, json.dumps(envelope, indent=2) + "\n")
        except OSError as e:
            msg = f"Could not write the token store at {self.path}: {e}"
            raise AuthError(msg) from e

    def get(self, account: str) -> Token:
        record = self._records().get(account)

        if record is None:
            msg = f"No token is stored for account {account!r}"
            raise TokenNotFoundError(msg)

        return Token.from_dict(record)

    def set(self, account: str, token: Token) -> None:
        if not account:
            msg = "An account name is required"
            raise AuthError(msg)

        records = self._records()
        records[account] = token.to_dict()

        self._write(records)

    def delete(self, account: str) -> None:
        records = self._records()

        if account not in records:
            msg = f"No token is stored for account {account!r}"
            raise TokenNotFoundError(msg)

        del records[account]

        self._write(records)

    def accounts(self) -> list[str]:
        return sorted(self._records())
