import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from discord_profile_studio.core.exceptions import AuthError

"""
KDF - Key Derivative Function

Password -> encryption key

Derived using PBKDF2 with SHA256
"""

SALT_BYTES = 16
KDF_ITERATIONS = 600_000
KEY_BYTES = 32
NONCE_BYTES = 12
KDF_NAME = "pbkdf2-sha256"


def new_salt() -> bytes:
    return os.urandom(SALT_BYTES)


def _checked(key: bytes) -> bytes:
    # AES-256 needs the 32-byte key
    if len(key) != KEY_BYTES:
        msg = f"Key must be {KEY_BYTES} bytes, got {len(key)}"
        raise AuthError(msg)

    return key


def derive_key(passphrase: str, salt: bytes, iterations: int = KDF_ITERATIONS) -> bytes:
    if not passphrase:
        msg = "The passphrase must not be empty"
        raise AuthError(msg)

    if len(salt) != SALT_BYTES:
        msg = f"Salt must be {SALT_BYTES} bytes, got {len(salt)}"
        raise AuthError(msg)

    if iterations < 1:
        msg = f"Iteration count must be positive, got {iterations}"
        raise AuthError(msg)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_BYTES,
        salt=salt,
        iterations=iterations,
    )

    return kdf.derive(passphrase.encode("utf-8"))


def encrypt(plaintext: bytes, key: bytes) -> bytes:
    nonce = os.urandom(NONCE_BYTES)

    return nonce + AESGCM(_checked(key)).encrypt(nonce, plaintext, None)


def decrypt(ciphertext: bytes, key: bytes) -> bytes:
    if len(ciphertext) <= NONCE_BYTES:
        msg = "The encrypted payload is truncated"
        raise AuthError(msg)

    nonce = ciphertext[:NONCE_BYTES]
    body = ciphertext[NONCE_BYTES:]

    try:
        return AESGCM(_checked(key)).decrypt(nonce, body, None)
    except InvalidTag as e:
        msg = "Could not decrypt the token store, wrong passphrase or corrupted file"
        raise AuthError(msg) from e
