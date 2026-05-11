from __future__ import annotations

import redis.asyncio as redis

from app.core.config import Settings, get_settings

_redis_client: redis.Redis | None = None


def create_redis_client(settings: Settings) -> redis.Redis:
    return redis.from_url(
        settings.redis_url,
        decode_responses=True,
        health_check_interval=30,
    )


async def get_redis_dependency() -> redis.Redis:
    """FastAPI dependency resolving the shared Redis connection."""
    global _redis_client
    if _redis_client is None:
        _redis_client = create_redis_client(get_settings())
    return _redis_client


async def close_redis_client() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
