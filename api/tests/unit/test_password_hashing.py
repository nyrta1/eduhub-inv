from __future__ import annotations

from app.auth.hashing import hash_password, verify_password, verify_password_needs_rehash


def test_hash_and_verify_roundtrip() -> None:
    digest = hash_password("Aa1!SecureExample")
    assert verify_password("Aa1!SecureExample", digest)
    assert not verify_password("wrong", digest)


def test_needs_rehash_is_boolean() -> None:
    digest = hash_password("Aa1!SecureExample")
    assert isinstance(verify_password_needs_rehash(digest), bool)
