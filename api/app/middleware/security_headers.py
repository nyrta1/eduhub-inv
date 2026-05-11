from __future__ import annotations

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import get_settings
from app.security.headers import build_security_header_map, cache_control_for_path


def _is_docs_path(path: str) -> bool:
    return path.startswith("/api/v1/docs") or path.startswith("/api/v1/redoc")


def _docs_csp() -> str:
    # Swagger/ReDoc need external JS/CSS plus inline bootstrap snippets.
    return (
        "default-src 'self'; "
        "base-uri 'self'; "
        "frame-ancestors 'none'; "
        "img-src 'self' data: https://fastapi.tiangolo.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "font-src 'self' data: https://cdn.jsdelivr.net; "
        "connect-src 'self'"
    )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach configurable security headers and selective Cache-Control on sensitive routes."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        settings = get_settings()
        response = await call_next(request)

        headers = build_security_header_map(settings)
        if _is_docs_path(request.url.path):
            headers["Content-Security-Policy"] = _docs_csp()

        for name, value in headers.items():
            response.headers.setdefault(name, value)

        cc = cache_control_for_path(settings, request.url.path)
        if cc:
            response.headers["Cache-Control"] = cc

        return response
