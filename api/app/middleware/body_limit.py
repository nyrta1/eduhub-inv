from __future__ import annotations

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class MaxRequestBodySizeMiddleware(BaseHTTPMiddleware):
    """Reject oversized payloads early based on the Content-Length header."""

    def __init__(
        self,
        app: object,
        *,
        max_body_bytes: int,
    ) -> None:
        super().__init__(app)
        self._max_body_bytes = max_body_bytes

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        content_length_header = request.headers.get("content-length")
        if content_length_header is None:
            return await call_next(request)
        try:
            content_length = int(content_length_header)
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={"detail": "Invalid Content-Length header"},
            )
        if content_length > self._max_body_bytes:
            return JSONResponse(
                status_code=413,
                content={"detail": "Payload exceeds configured maximum size"},
            )
        return await call_next(request)
