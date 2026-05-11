from __future__ import annotations

import re
from dataclasses import dataclass

from app.core.config import Settings


@dataclass(frozen=True)
class RateRouteRule:
    bucket: str
    limit: int
    window_seconds: int


_UUID_SEGMENT = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def path_segments(path: str) -> list[str]:
    return [p for p in path.split("/") if p]


def classify_sensitive_route(method: str, path: str, settings: Settings) -> RateRouteRule | None:
    """
    Map HTTP requests to Redis sliding-window rate limits for abuse-prone endpoints.

    Uses structured path parsing only (no user-controlled SQL); UUID segments validated loosely.
    """
    parts = path_segments(path)
    if len(parts) < 3 or parts[0] != "api" or parts[1] != "v1":
        return None

    tail = parts[2:]

    if method == "POST" and tail == ["applications"]:
        return RateRouteRule(
            bucket="application_submit",
            limit=settings.api_academic_application_submit_per_ip_per_hour,
            window_seconds=3600,
        )

    if (
        method == "PATCH"
        and len(tail) == 3
        and tail[0] == "applications"
        and tail[2] == "status"
        and _UUID_SEGMENT.match(tail[1])
    ):
        return RateRouteRule(
            bucket="application_review",
            limit=settings.api_application_review_per_ip_per_minute,
            window_seconds=60,
        )

    if method == "POST" and tail == ["grades"]:
        return RateRouteRule(
            bucket="grade_create",
            limit=settings.api_academic_grade_write_per_ip_per_minute,
            window_seconds=60,
        )

    if (
        method == "PATCH"
        and len(tail) == 2
        and tail[0] == "grades"
        and _UUID_SEGMENT.match(tail[1])
    ):
        return RateRouteRule(
            bucket="grade_update",
            limit=settings.api_academic_grade_write_per_ip_per_minute,
            window_seconds=60,
        )

    if (
        method == "PATCH"
        and len(tail) == 3
        and tail[0] == "users"
        and tail[2] == "role"
        and _UUID_SEGMENT.match(tail[1])
    ):
        return RateRouteRule(
            bucket="admin_role_change",
            limit=settings.api_admin_role_change_per_ip_per_hour,
            window_seconds=3600,
        )

    return None
