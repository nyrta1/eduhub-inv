from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EnrollmentApplication(Base):
    __tablename__ = "enrollment_applications"
    __table_args__ = (
        Index("ix_enrollment_applications_applicant_status", "applicant_user_id", "status"),
        Index("ix_enrollment_applications_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    applicant_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    program_code: Mapped[str] = mapped_column(String(64), nullable=False)
    intake_term: Mapped[str] = mapped_column(String(32), nullable=False)
    statement: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resulting_student_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("students.id", ondelete="SET NULL"),
        nullable=True,
    )
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

    applicant: Mapped["User"] = relationship(
        "User",
        foreign_keys=[applicant_user_id],
        lazy="selectin",
    )
    reviewer: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[reviewed_by_user_id],
        lazy="selectin",
    )
