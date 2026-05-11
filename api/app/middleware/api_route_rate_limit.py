from __future__ import annotations

import hashlib
from collections.abc import Awaitable, Callable

import redis.asyncio as redis
import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.core.redis_client import get_redis_dependency
from app.metrics.security_metrics import security_sensitive_route_limited_total
from app.security.rate_limit import RateLimiterExhausted, increment_sliding_window
from app.security.sensitive_routes import classify_sensitive_route
from app.utils.http import get_client_ip


def _auth_fingerprint(request: Request) -> str:
    raw = request.headers.get("authorization") or ""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


class SensitiveRouteRateLimitMiddleware(BaseHTTPMiddleware):
    """Redis-backed secondary limits for academic/admin mutations beyond authentication flows."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        settings = get_settings()
        rule = classify_sensitive_route(request.method, request.url.path, settings)
        if rule is None:
            return await call_next(request)

        redis_client: redis.Redis = await get_redis_dependency()
        ip = get_client_ip(request) or "unknown"
        ip_key = f"rl:sensitive:{rule.bucket}:ip:{ip}"

        try:
            await increment_sliding_window(
                redis_client,
                key=ip_key,
                limit=rule.limit,
                window_seconds=rule.window_seconds,
            )
        except RateLimiterExhausted as exc:
            security_sensitive_route_limited_total.labels(bucket=rule.bucket).inc()
            structlog.get_logger("security.rate_limit").warning(
                "sensitive_route.limited",
                bucket=rule.bucket,
                client_host=ip,
                path=request.url.path,
                method=request.method,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": {
                        "code": "rate_limited",
                        "message": "Too many sensitive operations from this network.",
                        "retry_after": exc.retry_after_seconds,
                    }
                },
                headers={"Retry-After": str(exc.retry_after_seconds)},
            )

        if rule.bucket in {"grade_create", "grade_update"}:
            fp = _auth_fingerprint(request)
            tok_key = f"rl:sensitive:{rule.bucket}:tok:{fp}"
            try:
                await increment_sliding_window(
                    redis_client,
                    key=tok_key,
                    limit=settings.api_academic_grade_write_per_token_per_minute,
                    window_seconds=60,
                )
            except RateLimiterExhausted as exc:
                security_sensitive_route_limited_total.labels(bucket=f"{rule.bucket}_token").inc()
                structlog.get_logger("security.rate_limit").warning(
                    "sensitive_route.token_limited",
                    bucket=rule.bucket,
                    client_host=ip,
                    path=request.url.path,
                )
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": {
                            "code": "rate_limited",
                            "message": "Grade mutation rate exceeded for this credential.",
                            "retry_after": exc.retry_after_seconds,
                        }
                    },
                    headers={"Retry-After": str(exc.retry_after_seconds)},
                )

        return await call_next(request)
