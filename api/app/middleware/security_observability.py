from __future__ import annotations

from collections.abc import Awaitable, Callable

import redis.asyncio as redis
import structlog
from redis.exceptions import RedisError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import get_settings
from app.core.redis_client import get_redis_dependency
from app.metrics.security_metrics import security_denied_burst_alerts_total, security_http_denied_total
from app.utils.http import get_client_ip


class SecurityObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Correlate authorization failures and spikes for SOC-style monitoring.

    Does not block traffic; emits structured warnings when thresholds are exceeded.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        status_code = response.status_code

        if status_code in (401, 403):
            security_http_denied_total.labels(status_code=str(status_code)).inc()

        if status_code not in (401, 403):
            return response

        settings = get_settings()
        redis_client: redis.Redis = await get_redis_dependency()
        ip = get_client_ip(request) or "unknown"
        burst_key = f"sec:denied:{ip}"

        try:
            current = await redis_client.incr(burst_key)
            if current == 1:
                await redis_client.expire(burst_key, settings.security_denied_burst_window_seconds)
        except RedisError:
            structlog.get_logger("security.observability").warning(
                "denied.counter.redis_error",
                client_host=ip,
            )
            return response

        if current >= settings.security_denied_burst_threshold_per_ip:
            security_denied_burst_alerts_total.inc()
            structlog.get_logger("security.observability").warning(
                "security.denied_burst",
                client_host=ip,
                path=request.url.path,
                method=request.method,
                status_code=status_code,
                denied_window_count=current,
                threshold=settings.security_denied_burst_threshold_per_ip,
            )

        return response
