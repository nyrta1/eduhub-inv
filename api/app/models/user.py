from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.associations import UserRole


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_email_active", "email", "deleted_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    failed_login_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary=UserRole.__table__,
        back_populates="users",
        lazy="selectin",
    )
    student_profile: Mapped["Student | None"] = relationship(
        "Student",
        back_populates="user",
        uselist=False,
    )
    teacher_profile: Mapped["Teacher | None"] = relationship(
        "Teacher",
        back_populates="user",
        uselist=False,
    )
    refresh_sessions: Mapped[list["RefreshSession"]] = relationship(
        "RefreshSession",
        back_populates="user",
        lazy="selectin",
    )
