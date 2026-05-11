from __future__ import annotations

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

from app.security.audit import _scrub_metadata

DOMAIN_RESOURCE_PREFIX = "academic"


async def record_domain_event(
    session: AsyncSession,
    *,
    action: str,
    resource_type: str,
    resource_id: uuid.UUID | None,
    actor_user_id: uuid.UUID | None,
    ip_address: str | None,
    user_agent: str | None,
    metadata: dict[str, Any] | None = None,
    severity: str | None = None,
    event_category: str | None = None,
) -> None:
    """Persist domain audit rows and emit structured business telemetry."""
    logger = structlog.get_logger("business.audit")
    context = structlog.contextvars.get_contextvars()
    request_id = context.get("request_id")
    enriched: dict[str, Any] = dict(metadata or {})
    if severity:
        enriched["severity"] = severity
    if event_category:
        enriched["event_category"] = event_category
    enriched.setdefault("request_id", request_id)
    safe_metadata = _scrub_metadata(enriched)

    logger.info(
        "business.event",
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else None,
        actor_user_id=str(actor_user_id) if actor_user_id else None,
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id,
        severity=severity,
        event_category=event_category,
        metadata=safe_metadata,
        result="success",
    )

    audit_row = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        resource_type=f"{DOMAIN_RESOURCE_PREFIX}.{resource_type}",
        resource_id=resource_id,
        details=safe_metadata,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    session.add(audit_row)
