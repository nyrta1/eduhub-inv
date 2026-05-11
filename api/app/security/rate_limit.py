from __future__ import annotations

import hashlib

import redis.asyncio as redis
from fastapi import HTTPException, status

from app.core.config import Settings


class RateLimiterExhausted(Exception):
    def __init__(self, *, retry_after_seconds: int) -> None:
        super().__init__("rate limit exceeded")
        self.retry_after_seconds = retry_after_seconds


async def increment_sliding_window(
    redis_client: redis.Redis,
    *,
    key: str,
    limit: int,
    window_seconds: int,
) -> None:
    current = await redis_client.incr(key)
    if current == 1:
        await redis_client.expire(key, window_seconds)

    ttl = await redis_client.ttl(key)
    effective_ttl = ttl if ttl and ttl > 0 else window_seconds

    if current > limit:
        raise RateLimiterExhausted(retry_after_seconds=int(effective_ttl))


def _hash_identifier(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class AuthRateLimiter:
    """Redis-backed counters for abusive authentication traffic."""

    def __init__(self, redis_client: redis.Redis, settings: Settings) -> None:
        self._redis = redis_client
        self._settings = settings

    async def enforce_login_ip(self, ip_address: str) -> None:
        key = f"rl:auth:login:ip:{ip_address}"
        try:
            await increment_sliding_window(
                self._redis,
                key=key,
                limit=self._settings.auth_login_max_per_ip_per_minute,
                window_seconds=60,
            )
        except RateLimiterExhausted as exc:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "rate_limited",
                    "message": "Too many authentication attempts from this network.",
                    "retry_after": exc.retry_after_seconds,
                },
                headers={"Retry-After": str(exc.retry_after_seconds)},
            ) from exc

    async def enforce_login_email(self, email: str) -> None:
        digest = _hash_identifier(email.lower())
        key = f"rl:auth:login:email:{digest}"
        try:
            await increment_sliding_window(
                self._redis,
                key=key,
                limit=self._settings.auth_login_max_per_email_per_minute,
                window_seconds=60,
            )
        except RateLimiterExhausted as exc:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "rate_limited",
                    "message": "Too many attempts for this identifier.",
                    "retry_after": exc.retry_after_seconds,
                },
                headers={"Retry-After": str(exc.retry_after_seconds)},
            ) from exc

    async def enforce_register_ip(self, ip_address: str) -> None:
        key = f"rl:auth:register:ip:{ip_address}"
        try:
            await increment_sliding_window(
                self._redis,
                key=key,
                limit=self._settings.auth_register_max_per_ip_per_hour,
                window_seconds=3600,
            )
        except RateLimiterExhausted as exc:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "rate_limited",
                    "message": "Registration attempts exceeded for this network.",
                    "retry_after": exc.retry_after_seconds,
                },
                headers={"Retry-After": str(exc.retry_after_seconds)},
            ) from exc

    async def enforce_refresh_session(self, session_id: str) -> None:
        key = f"rl:auth:refresh:sid:{session_id}"
        try:
            await increment_sliding_window(
                self._redis,
                key=key,
                limit=self._settings.auth_refresh_max_per_session_per_minute,
                window_seconds=60,
            )
        except RateLimiterExhausted as exc:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "rate_limited",
                    "message": "Too many refresh attempts for this session.",
                    "retry_after": exc.retry_after_seconds,
                },
                headers={"Retry-After": str(exc.retry_after_seconds)},
            ) from exc
