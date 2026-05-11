from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from app.auth.jwt import TokenValidationError, decode_access_token, issue_access_token
from app.core.config import Settings


def _minimal_settings() -> Settings:
    return Settings(
        app_secret_key="x" * 32,
        database_url="postgresql+asyncpg://u:p@localhost:5432/db",
        redis_url="redis://localhost:6379/0",
    )


def test_issue_and_decode_roundtrip() -> None:
    settings = _minimal_settings()
    uid = uuid.uuid4()
    sid = uuid.uuid4()
    jti = uuid.uuid4()
    raw = issue_access_token(user_id=uid, session_id=sid, access_jti=jti, settings=settings)
    claims = decode_access_token(raw, settings)
    assert claims.user_id == uid
    assert claims.session_id == sid


def test_decode_rejects_tampered_signature() -> None:
    settings = _minimal_settings()
    uid = uuid.uuid4()
    raw = issue_access_token(
        user_id=uid,
        session_id=uuid.uuid4(),
        access_jti=uuid.uuid4(),
        settings=settings,
    )
    parts = raw.split(".")
    parts[2] = "tampered"
    bad = ".".join(parts)
    with pytest.raises(TokenValidationError):
        decode_access_token(bad, settings)


def test_decode_rejects_expired_token() -> None:
    settings = _minimal_settings()
    now = datetime.now(UTC)
    past = now - timedelta(minutes=5)
    payload = {
        "sub": str(uuid.uuid4()),
        "sid": str(uuid.uuid4()),
        "jti": str(uuid.uuid4()),
        "typ": "access",
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience_access,
        "iat": int(past.timestamp()),
        "exp": int((past + timedelta(seconds=30)).timestamp()),
    }
    raw = jwt.encode(
        payload, settings.resolved_jwt_access_secret(), algorithm=settings.jwt_algorithm
    )
    with pytest.raises(TokenValidationError):
        decode_access_token(raw, settings)
