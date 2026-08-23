SALT_BYTES = 16
KDF_ITERATIONS = 600_000


def derive_key(passphrase: str, salt: bytes) -> bytes:
    raise NotImplementedError


def encrypt(plaintext: bytes, key: bytes) -> bytes:
    raise NotImplementedError


def decrypt(ciphertext: bytes, key: bytes) -> bytes:
    raise NotImplementedError
