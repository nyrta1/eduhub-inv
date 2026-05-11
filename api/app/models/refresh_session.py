from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RefreshSession(Base):
    """Server-side refresh token session with rotation and replay detection."""

    __tablename__ = "refresh_sessions"
    __table_args__ = (
        Index("ix_refresh_sessions_user_expires", "user_id", "expires_at"),
        Index("ix_refresh_sessions_family_id", "family_id"),
        Index("ix_refresh_sessions_revoked_at", "revoked_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    family_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    refresh_jti: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), unique=True, nullable=False)
    refresh_token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    replaced_by_session_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("refresh_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )

    user: Mapped["User"] = relationship("User", back_populates="refresh_sessions")
