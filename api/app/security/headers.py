from __future__ import annotations

from app.core.config import Settings


def build_security_header_map(settings: Settings) -> dict[str, str]:
    """Conservative browser security headers for API responses."""
    if not settings.security_headers_enabled:
        return {}

    hsts = f"max-age={settings.security_hsts_max_age}"
    if settings.security_hsts_include_subdomains:
        hsts += "; includeSubDomains"
    hsts += "; preload"

    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": settings.security_referrer_policy,
        "Permissions-Policy": settings.security_permissions_policy,
        "Strict-Transport-Security": hsts,
        "Content-Security-Policy": settings.security_csp,
        "Cross-Origin-Opener-Policy": "same-origin",
        "Cross-Origin-Resource-Policy": "same-site",
    }


def cache_control_for_path(settings: Settings, path: str) -> str | None:
    """Apply stronger cache inhibition on authentication and administration routes."""
    if path.startswith("/api/v1/auth") or path.startswith("/api/v1/users/"):
        return settings.security_cache_control_sensitive
    return None
