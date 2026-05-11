from __future__ import annotations

from starlette.requests import Request


def get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def get_user_agent(request: Request) -> str | None:
    return request.headers.get("user-agent")
