from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

_sensitive_keys = frozenset(
    {
        "password",
        "new_password",
        "current_password",
        "refresh_token",
        "access_token",
        "authorization",
        "cookie",
    },
)

SECURITY_RESOURCE_TYPE = "security"


def _scrub_metadata(metadata: dict[str, Any] | None) -> dict[str, Any] | None:
    if not metadata:
        return None
    cleaned: dict[str, Any] = {}
    for key, value in metadata.items():
        lowered = key.lower()
        if lowered in _sensitive_keys:
            continue
        cleaned[key] = value
    return cleaned or None


async def record_security_event(
    session: AsyncSession,
    *,
    event_type: str,
    actor_user_id: uuid.UUID | None,
    subject_user_id: uuid.UUID | None,
    ip_address: str | None,
    user_agent: str | None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Persist an immutable audit entry and emit structured telemetry without secrets."""
    logger = structlog.get_logger("security.audit")
    context = structlog.contextvars.get_contextvars()
    request_id = context.get("request_id")
    safe_metadata = _scrub_metadata(metadata)

    logger.info(
        "security.event",
        event_type=event_type,
        actor_user_id=str(actor_user_id) if actor_user_id else None,
        subject_user_id=str(subject_user_id) if subject_user_id else None,
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id,
        metadata=safe_metadata,
    )

    audit_row = AuditLog(
        actor_user_id=actor_user_id,
        action=event_type,
        resource_type=SECURITY_RESOURCE_TYPE,
        resource_id=subject_user_id,
        details=safe_metadata,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    session.add(audit_row)
