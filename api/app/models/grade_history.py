from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class GradeHistory(Base):
    __tablename__ = "grade_histories"
    __table_args__ = (Index("ix_grade_histories_grade_id", "grade_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    grade_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("grades.id", ondelete="CASCADE"),
        nullable=False,
    )
    previous_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    new_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    actor_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
    )
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    grade: Mapped["Grade"] = relationship("Grade", back_populates="history_entries")
