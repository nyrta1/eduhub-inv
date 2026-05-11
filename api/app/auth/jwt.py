from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import jwt
from jwt import InvalidTokenError

from app.core.config import Settings


class TokenValidationError(Exception):
    """Raised when a token cannot be cryptographically validated or is malformed."""


@dataclass(frozen=True, slots=True)
class AccessTokenClaims:
    user_id: UUID
    session_id: UUID
    access_jti: UUID


@dataclass(frozen=True, slots=True)
class RefreshTokenClaims:
    user_id: UUID
    session_id: UUID
    refresh_jti: UUID
    family_id: UUID


def issue_access_token(
    *,
    user_id: UUID,
    session_id: UUID,
    access_jti: UUID,
    settings: Settings,
) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(seconds=settings.jwt_access_ttl_seconds)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "sid": str(session_id),
        "jti": str(access_jti),
        "typ": "access",
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience_access,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(
        payload,
        settings.resolved_jwt_access_secret(),
        algorithm=settings.jwt_algorithm,
    )


def issue_refresh_token(
    *,
    user_id: UUID,
    session_id: UUID,
    refresh_jti: UUID,
    family_id: UUID,
    settings: Settings,
) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(seconds=settings.jwt_refresh_ttl_seconds)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "sid": str(session_id),
        "jti": str(refresh_jti),
        "fam": str(family_id),
        "typ": "refresh",
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience_refresh,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(
        payload,
        settings.resolved_jwt_refresh_secret(),
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str, settings: Settings) -> AccessTokenClaims:
    try:
        payload = jwt.decode(
            token,
            settings.resolved_jwt_access_secret(),
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience_access,
            issuer=settings.jwt_issuer,
            options={"require": ["exp", "iat", "sub", "sid", "jti"]},
        )
    except InvalidTokenError as exc:
        raise TokenValidationError("invalid access token") from exc

    if payload.get("typ") != "access":
        raise TokenValidationError("unexpected token type")

    return AccessTokenClaims(
        user_id=UUID(payload["sub"]),
        session_id=UUID(payload["sid"]),
        access_jti=UUID(payload["jti"]),
    )


def decode_refresh_token(token: str, settings: Settings) -> RefreshTokenClaims:
    try:
        payload = jwt.decode(
            token,
            settings.resolved_jwt_refresh_secret(),
            algorithms=[settings.jwt_algorithm],
            audience=settings.jwt_audience_refresh,
            issuer=settings.jwt_issuer,
            options={"require": ["exp", "iat", "sub", "sid", "jti", "fam"]},
        )
    except InvalidTokenError as exc:
        raise TokenValidationError("invalid refresh token") from exc

    if payload.get("typ") != "refresh":
        raise TokenValidationError("unexpected token type")

    return RefreshTokenClaims(
        user_id=UUID(payload["sub"]),
        session_id=UUID(payload["sid"]),
        refresh_jti=UUID(payload["jti"]),
        family_id=UUID(payload["fam"]),
    )
