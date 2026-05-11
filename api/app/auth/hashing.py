from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65_536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
)


def hash_password(plain_password: str) -> str:
    """Derive an Argon2id password digest suitable for persistent storage."""
    return _hasher.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a password candidate against a stored Argon2id digest."""
    try:
        _hasher.verify(password_hash, plain_password)
        return True
    except VerifyMismatchError:
        return False


def verify_password_needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)
