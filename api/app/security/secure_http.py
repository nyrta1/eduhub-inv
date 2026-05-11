from __future__ import annotations

import ipaddress
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import Settings, get_settings


class SecureHttpError(Exception):
    """Blocked or unsafe outbound HTTP configuration."""


@dataclass(frozen=True)
class SecureHttpResponse:
    status_code: int
    headers: Mapping[str, str]
    content: bytes


def _parse_host(hostname: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        return ipaddress.ip_address(hostname)
    except ValueError:
        return None


def assert_url_allowed(url: str, *, allowed_hosts: frozenset[str] | None = None) -> None:
    """
    Prevent SSRF against loopback, RFC1918, CGNAT, metadata endpoints, and link-local.

    `allowed_hosts` optional explicit hostname allow-list (lowercased hostnames).
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise SecureHttpError(f"Unsupported URL scheme: {parsed.scheme!r}")

    host = parsed.hostname
    if not host:
        raise SecureHttpError("URL missing hostname.")

    if allowed_hosts is not None and host.lower() not in allowed_hosts:
        raise SecureHttpError("Host not in outbound allow-list.")

    addr = _parse_host(host)
    if addr is None:
        lowered = host.lower()
        if lowered in {"localhost"} or lowered.endswith(".localhost"):
            raise SecureHttpError("Localhost targets are denied.")
        return

    if addr.is_loopback or addr.is_link_local or addr.is_multicast or addr.is_reserved:
        raise SecureHttpError("Blocked address class for outbound request.")

    if addr.version == 4:
        if addr in ipaddress.ip_network("10.0.0.0/8"):
            raise SecureHttpError("RFC1918 addresses are denied.")
        if addr in ipaddress.ip_network("172.16.0.0/12"):
            raise SecureHttpError("RFC1918 addresses are denied.")
        if addr in ipaddress.ip_network("192.168.0.0/16"):
            raise SecureHttpError("RFC1918 addresses are denied.")
        if addr in ipaddress.ip_network("169.254.0.0/16"):
            raise SecureHttpError("Link-local IPv4 range denied.")
        if addr in ipaddress.ip_network("100.64.0.0/10"):
            raise SecureHttpError("CGNAT range denied.")
        if addr in ipaddress.ip_network("127.0.0.0/8"):
            raise SecureHttpError("Loopback range denied.")
    elif addr.version == 6:
        if addr in ipaddress.ip_network("fc00::/7"):
            raise SecureHttpError("Unique local IPv6 denied.")
        if addr in ipaddress.ip_network("fe80::/10"):
            raise SecureHttpError("IPv6 link-local denied.")
        if addr == ipaddress.IPv6Address("::1"):
            raise SecureHttpError("IPv6 loopback denied.")


async def secure_get(
    url: str,
    *,
    settings: Settings | None = None,
    allowed_hosts: frozenset[str] | None = None,
    headers: Mapping[str, str] | None = None,
    follow_redirects: bool = False,
) -> SecureHttpResponse:
    """
    Minimal GET helper with DNS rebinding-safe assumptions: blocks redirects by default.
    """
    cfg = settings or get_settings()
    assert_url_allowed(url, allowed_hosts=allowed_hosts)

    timeout = httpx.Timeout(cfg.secure_http_default_timeout_seconds)
    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=follow_redirects,
        trust_env=False,
    ) as client:
        resp = await client.get(url, headers=headers)
        return SecureHttpResponse(
            status_code=resp.status_code,
            headers=dict(resp.headers),
            content=resp.content,
        )


async def secure_request(
    method: str,
    url: str,
    *,
    settings: Settings | None = None,
    allowed_hosts: frozenset[str] | None = None,
    headers: Mapping[str, str] | None = None,
    json: Any | None = None,
    follow_redirects: bool = False,
) -> SecureHttpResponse:
    cfg = settings or get_settings()
    assert_url_allowed(url, allowed_hosts=allowed_hosts)
    timeout = httpx.Timeout(cfg.secure_http_default_timeout_seconds)
    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=follow_redirects,
        trust_env=False,
    ) as client:
        resp = await client.request(method.upper(), url, headers=headers, json=json)
        return SecureHttpResponse(
            status_code=resp.status_code,
            headers=dict(resp.headers),
            content=resp.content,
        )
