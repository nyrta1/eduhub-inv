from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class AccessLoggingMiddleware(BaseHTTPMiddleware):
    """Emit structured access logs without storing credential headers."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        logger = structlog.get_logger("http.access")
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000.0, 3)
        logger.info(
            "request.completed",
            http_method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            client_host=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        return response
