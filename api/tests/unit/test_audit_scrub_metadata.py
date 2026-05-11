from __future__ import annotations

from app.security.audit import _scrub_metadata


def test_scrub_strips_sensitive_keys() -> None:
    out = _scrub_metadata({"password": "secret", "refresh_token": "x", "safe": "ok"})
    assert out == {"safe": "ok"}
