import stat
import sys
from datetime import UTC, datetime, timedelta

import keyring
import pytest
from keyring.backend import KeyringBackend
from keyring.errors import PasswordDeleteError

from discord_profile_studio.auth import encrypted_store, store as store_module
from discord_profile_studio.auth.encrypted_store import EncryptedFileStore
from discord_profile_studio.auth.keyring_store import INDEX_KEY, KeyringStore
from discord_profile_studio.auth.store import (
    AUTO,
    ENCRYPTED_FILE,
    KEYRING,
    canonical,
    open_store,
)
from discord_profile_studio.auth.token import Token, TokenKind
from discord_profile_studio.core.config import Settings
from discord_profile_studio.core.exceptions import AuthError, StoreLockedError, TokenNotFoundError

ACCESS = "aBcDeFgHiJkLmNoPqRsTuVwXyZ012345"
REFRESH = "0123456789abcdefghijklmnopqrstuv"
PASSPHRASE = "correct horse battery staple"
OTHER_PASSPHRASE = "a different passphrase"

on_posix = pytest.mark.skipif(sys.platform == "win32",
                              reason="requires POSIX file modes")


class MemoryKeyring(KeyringBackend):
    priority = 1

    def __init__(self):
        super().__init__()
        self.entries = {}

    def get_password(self, service, username):
        return self.entries.get((service, username))

    def set_password(self, service, username, password):
        self.entries[(service, username)] = password

    def delete_password(self, service, username):
        if (service, username) not in self.entries:
            raise PasswordDeleteError(username)

        del self.entries[(service, username)]


def make_token(access=ACCESS, refresh=REFRESH):
    return Token(
        kind=TokenKind.OAUTH,
        access_token=access,
        refresh_token=refresh,
        scopes=["identify", "rpc"],
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )


@pytest.fixture(autouse=True)
def fast_kdf(monkeypatch):
    monkeypatch.setattr(encrypted_store, "KDF_ITERATIONS", 1_000)


@pytest.fixture
def keyring_store():
    previous = keyring.get_keyring()
    keyring.set_keyring(MemoryKeyring())

    yield KeyringStore()

    keyring.set_keyring(previous)


@pytest.fixture
def token_path(tmp_path):
    return tmp_path / "secrets" / "tokens.enc"


@pytest.fixture
def file_store(token_path):
    return EncryptedFileStore(token_path, PASSPHRASE)


def test_keyring_roundtrip(keyring_store):
    token = make_token()

    keyring_store.set("main", token)

    assert keyring_store.get("main") == token


def test_keyring_reports_itself_available(keyring_store):
    assert keyring_store.available()


def test_keyring_lists_stored_accounts(keyring_store):
    keyring_store.set("second", make_token())
    keyring_store.set("first", make_token())

    assert keyring_store.accounts() == ["first", "second"]


def test_keyring_hides_the_index_from_the_account_list(keyring_store):
    keyring_store.set("main", make_token())

    assert INDEX_KEY not in keyring_store.accounts()


def test_keyring_delete_forgets_the_account(keyring_store):
    keyring_store.set("main", make_token())
    keyring_store.delete("main")

    assert keyring_store.accounts() == []

    with pytest.raises(TokenNotFoundError):
        keyring_store.get("main")


def test_keyring_get_missing_account_raises(keyring_store):
    with pytest.raises(TokenNotFoundError):
        keyring_store.get("missing")


def test_keyring_delete_missing_account_raises(keyring_store):
    with pytest.raises(TokenNotFoundError):
        keyring_store.delete("missing")


def test_keyring_rejects_the_reserved_account_name(keyring_store):
    with pytest.raises(AuthError):
        keyring_store.set(INDEX_KEY, make_token())


@on_posix
def test_encrypted_file_permissions(file_store, token_path):
    file_store.set("main", make_token())

    assert stat.S_IMODE(token_path.stat().st_mode) == 0o600
    assert stat.S_IMODE(token_path.parent.stat().st_mode) == 0o700


@on_posix
def test_encrypted_file_permissions_survive_a_rewrite(file_store, token_path):
    file_store.set("main", make_token())
    token_path.chmod(0o666)
    file_store.set("other", make_token())

    assert stat.S_IMODE(token_path.stat().st_mode) == 0o600


def test_encrypted_file_never_holds_the_plain_secret(file_store, token_path):
    file_store.set("main", make_token())

    contents = token_path.read_bytes()

    assert ACCESS.encode() not in contents
    assert REFRESH.encode() not in contents


def test_encrypted_roundtrip(file_store):
    token = make_token()

    file_store.set("main", token)

    assert file_store.get("main") == token


def test_encrypted_store_survives_a_reopen(file_store, token_path):
    token = make_token()
    file_store.set("main", token)

    reopened = EncryptedFileStore(token_path)
    reopened.unlock(PASSPHRASE)

    assert reopened.get("main") == token


def test_encrypted_store_keeps_several_accounts(file_store):
    file_store.set("second", make_token())
    file_store.set("first", make_token(access="another-access-token"))

    assert file_store.accounts() == ["first", "second"]
    assert file_store.get("first").access_token == "another-access-token"


def test_encrypted_delete_removes_the_account(file_store):
    file_store.set("main", make_token())
    file_store.delete("main")

    assert file_store.accounts() == []


def test_encrypted_delete_missing_account_raises(file_store):
    file_store.set("main", make_token())

    with pytest.raises(TokenNotFoundError):
        file_store.delete("missing")


def test_encrypted_store_rejects_a_wrong_passphrase(file_store, token_path):
    file_store.set("main", make_token())

    with pytest.raises(AuthError):
        EncryptedFileStore(token_path, OTHER_PASSPHRASE).accounts()


def test_encrypted_store_rejects_a_corrupted_file(file_store, token_path):
    file_store.set("main", make_token())
    token_path.write_text("not json at all", encoding="utf-8")

    with pytest.raises(AuthError):
        file_store.accounts()


def test_locked_store_raises(token_path):
    locked = EncryptedFileStore(token_path)

    assert locked.locked

    with pytest.raises(StoreLockedError):
        locked.accounts()

    with pytest.raises(StoreLockedError):
        locked.set("main", make_token())

    with pytest.raises(StoreLockedError):
        locked.get("main")


def test_locking_forgets_the_passphrase(file_store):
    file_store.set("main", make_token())
    file_store.lock()

    with pytest.raises(StoreLockedError):
        file_store.accounts()

    file_store.unlock(PASSPHRASE)

    assert file_store.accounts() == ["main"]


def test_store_is_uninitialized_until_it_is_written(file_store):
    assert not file_store.initialized

    file_store.set("main", make_token())

    assert file_store.initialized


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        ("keyring", KEYRING),
        ("KEYRING", KEYRING),
        ("encrypted-file", ENCRYPTED_FILE),
        ("encrypted_file", ENCRYPTED_FILE),
        ("file", ENCRYPTED_FILE),
        ("  Encrypted  ", ENCRYPTED_FILE),
        ("default", AUTO),
    ],
)
def test_canonical_resolves_backend_names(given, expected):
    assert canonical(given) == expected


@pytest.mark.parametrize("given", ["", "vault", "gnome-keyring", "1password"])
def test_canonical_rejects_unknown_backends(given):
    with pytest.raises(AuthError):
        canonical(given)


def test_open_store_honours_an_explicit_file_backend(monkeypatch, token_path):
    monkeypatch.setattr(store_module, "token_file", lambda: token_path)

    assert open_store(ENCRYPTED_FILE).name == ENCRYPTED_FILE


# def test_open_store_passes_the_passphrase_through(monkeypatch, token_path):
# monkeypatch.setattr(store_module, "token_file", lambda: token_path)
#
# assert not open_store(ENCRYPTED_FILE, passphrase=PASSPHRASE).locked


@pytest.mark.usefixtures("keyring_store")
def test_open_store_prefers_the_keyring_when_it_works(monkeypatch, token_path):
    monkeypatch.setattr(store_module, "token_file", lambda: token_path)
    monkeypatch.setattr(store_module.config, "load", Settings)

    assert open_store().name == KEYRING


def test_open_store_falls_back_when_the_keyring_is_missing(
        monkeypatch, token_path):
    monkeypatch.setattr(store_module, "token_file", lambda: token_path)
    monkeypatch.setattr(store_module.config, "load", Settings)
    monkeypatch.setattr(KeyringStore, "available", lambda _: False)

    assert open_store().name == ENCRYPTED_FILE


def test_open_store_refuses_an_unavailable_keyring_when_asked_for_it(
        monkeypatch):
    monkeypatch.setattr(KeyringStore, "available", lambda _: False)

    with pytest.raises(AuthError):
        open_store(KEYRING)
