import pytest

from discord_profile_studio.auth.crypto import (
    KEY_BYTES,
    NONCE_BYTES,
    SALT_BYTES,
    decrypt,
    derive_key,
    encrypt,
    new_salt,
)
from discord_profile_studio.auth.redaction import MASK_CHAR, mask, scrub
from discord_profile_studio.core.exceptions import AuthError

PASSPHRASE = "correct horse battery staple"
SECRET = b'{"accounts": {"main": {"access_token": "abcdef"}}}'
ITERATIONS = 1_000
BOT_TOKEN = "MTIzNDU2Nzg5MDEyMzQ1Njc4.GaBcDe.abcdefghijklmnopqrstuvwxyz1234567"


@pytest.fixture
def salt():
    return new_salt()


@pytest.fixture
def key(salt):
    return derive_key(PASSPHRASE, salt, ITERATIONS)


def test_new_salt_has_the_expected_size():
    assert len(new_salt()) == SALT_BYTES


def test_new_salt_is_random():
    assert new_salt() != new_salt()


def test_derive_key_has_the_expected_size(key):
    assert len(key) == KEY_BYTES


def test_derive_key_is_deterministic(salt):
    assert derive_key(PASSPHRASE, salt, ITERATIONS) == derive_key(PASSPHRASE, salt, ITERATIONS)


def test_derive_key_depends_on_the_salt():
    assert derive_key(PASSPHRASE, new_salt(), ITERATIONS) != derive_key(
        PASSPHRASE, new_salt(), ITERATIONS
    )


def test_derive_key_depends_on_the_passphrase(salt):
    assert derive_key(PASSPHRASE, salt, ITERATIONS) != derive_key("other", salt, ITERATIONS)


def test_derive_key_rejects_an_empty_passphrase(salt):
    with pytest.raises(AuthError):
        derive_key("", salt, ITERATIONS)


@pytest.mark.parametrize("size", [0, 8, 15, 17, 32])
def test_derive_key_rejects_a_wrong_salt_size(size):
    with pytest.raises(AuthError):
        derive_key(PASSPHRASE, b"0" * size, ITERATIONS)


def test_derive_key_rejects_a_useless_iteration_count(salt):
    with pytest.raises(AuthError):
        derive_key(PASSPHRASE, salt, 0)


def test_encrypt_roundtrip(key):
    assert decrypt(encrypt(SECRET, key), key) == SECRET


def test_encrypt_hides_the_plaintext(key):
    assert SECRET not in encrypt(SECRET, key)


def test_encrypt_uses_a_fresh_nonce(key):
    assert encrypt(SECRET, key) != encrypt(SECRET, key)


def test_decrypt_rejects_another_key(key, salt):
    with pytest.raises(AuthError):
        decrypt(encrypt(SECRET, key), derive_key("other", salt, ITERATIONS))


def test_decrypt_rejects_tampered_ciphertext(key):
    payload = bytearray(encrypt(SECRET, key))
    payload[-1] ^= 0xFF

    with pytest.raises(AuthError):
        decrypt(bytes(payload), key)


def test_decrypt_rejects_a_tampered_nonce(key):
    payload = bytearray(encrypt(SECRET, key))
    payload[0] ^= 0xFF

    with pytest.raises(AuthError):
        decrypt(bytes(payload), key)


@pytest.mark.parametrize("size", [0, 1, NONCE_BYTES])
def test_decrypt_rejects_truncated_input(key, size):
    with pytest.raises(AuthError):
        decrypt(b"0" * size, key)


@pytest.mark.parametrize("size", [0, 16, 31, 33])
def test_encrypt_rejects_a_wrong_key_size(size):
    with pytest.raises(AuthError):
        encrypt(SECRET, b"0" * size)


def test_mask_keeps_only_the_tail():
    assert mask("abcdefghijkl") == MASK_CHAR * 8 + "ijkl"


def test_mask_hides_the_length():
    assert len(mask("a" * 40)) == len(mask("a" * 12))


def test_mask_of_a_short_secret_shows_nothing():
    assert mask("abc") == MASK_CHAR * 8


def test_mask_of_nothing_is_nothing():
    assert mask("") == ""


def test_mask_honours_the_visible_count():
    assert mask("abcdefghijkl", visible=2) == MASK_CHAR * 8 + "kl"


@pytest.mark.parametrize(
    "text",
    [
        f"Authorization: Bearer {BOT_TOKEN}",
        f"Authorization: Bot {BOT_TOKEN}",
        f'{{"access_token": "{BOT_TOKEN}"}}',
        f"refresh_token={BOT_TOKEN}&grant_type=refresh_token",
        f"client_secret={BOT_TOKEN}",
        f"the token is {BOT_TOKEN} apparently",
    ],
)
def test_scrub_removes_secrets(text):
    assert BOT_TOKEN not in scrub(text)


def test_scrub_keeps_the_surrounding_text():
    assert scrub(f"Authorization: Bearer {BOT_TOKEN}").startswith("Authorization: Bearer ")


def test_scrub_masks_an_authorisation_code():
    assert "n0tAr3alC0de" not in scrub("?code=n0tAr3alC0de&state=xyz")


def test_scrub_leaves_ordinary_text_alone():
    message = "Could not reach Discord: connection refused"

    assert scrub(message) == message


def test_scrub_is_stable():
    once = scrub(f'{{"access_token": "{BOT_TOKEN}"}}')

    assert scrub(once) == once
