from __future__ import annotations

import hashlib
import hmac


def fingerprint_refresh_token(token: str, pepper: str) -> str:
    """Create a deterministic fingerprint for refresh tokens stored server-side."""
    return hmac.new(pepper.encode("utf-8"), token.encode("utf-8"), hashlib.sha256).hexdigest()


def fingerprints_match(expected_hex_digest: str, candidate_token: str, pepper: str) -> bool:
    candidate = fingerprint_refresh_token(candidate_token, pepper)
    return hmac.compare_digest(expected_hex_digest, candidate)
