from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

import redis.asyncio as redis
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.auth.jwt import TokenValidationError, decode_access_token
from app.core.config import Settings, get_settings
from app.core.redis_client import get_redis_dependency
from app.db.session import SessionDep
from app.models.user import User

http_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    session: SessionDep,
    redis_client: Annotated[redis.Redis, Depends(get_redis_dependency)],
    settings: Annotated[Settings, Depends(get_settings)],
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(http_bearer),
    ],
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthorized", "message": "Authentication required."},
        )

    try:
        claims = decode_access_token(credentials.credentials, settings)
    except TokenValidationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": "Invalid or expired access token."},
        ) from None

    global_revoke = await redis_client.get(f"auth:revoked_all:{claims.user_id}")
    if global_revoke:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "sessions_invalidated", "message": "Credentials are no longer valid."},
        )

    revoked_marker = await redis_client.get(f"auth:revoked_session:{claims.session_id}")
    if revoked_marker:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "session_revoked", "message": "Session is no longer active."},
        )

    stmt = (
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == claims.user_id)
    )
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None or user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_subject", "message": "User context is not valid."},
        )
    return user


async def get_current_active_user(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    now_ts = datetime.now(timezone.utc)
    if user.locked_until is not None and user.locked_until > now_ts:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "account_locked", "message": "Account is temporarily locked."},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "account_inactive", "message": "Account is disabled."},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_active_user)]
