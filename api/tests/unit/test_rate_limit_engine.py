from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from app.security.rate_limit import RateLimiterExhausted, increment_sliding_window


@pytest.mark.asyncio
async def test_increment_sliding_window_respects_limit() -> None:
    redis = AsyncMock()
    redis.incr = AsyncMock(side_effect=[1, 2, 3])
    redis.expire = AsyncMock()
    redis.ttl = AsyncMock(return_value=55)

    with pytest.raises(RateLimiterExhausted):
        await increment_sliding_window(redis, key="k", limit=2, window_seconds=60)
        await increment_sliding_window(redis, key="k", limit=2, window_seconds=60)
        await increment_sliding_window(redis, key="k", limit=2, window_seconds=60)


@pytest.mark.asyncio
async def test_increment_first_call_sets_ttl() -> None:
    redis = AsyncMock()
    redis.incr = AsyncMock(return_value=1)
    redis.expire = AsyncMock()
    redis.ttl = AsyncMock(return_value=60)

    await increment_sliding_window(redis, key="k2", limit=10, window_seconds=120)
    redis.expire.assert_awaited_once()
