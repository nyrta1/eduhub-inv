from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Grade(Base):
    __tablename__ = "grades"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_grades_student_course"),
        CheckConstraint("score >= 0 AND score <= 100", name="ck_grades_score_range"),
        Index("ix_grades_student_id", "student_id"),
        Index("ix_grades_course_id", "course_id"),
        Index("ix_grades_recorded_at", "recorded_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("courses.id", ondelete="RESTRICT"),
        nullable=False,
    )
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    letter_grade: Mapped[str | None] = mapped_column(String(8), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
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

    student: Mapped["Student"] = relationship("Student", back_populates="grades")
    course: Mapped["Course"] = relationship("Course", back_populates="grades")
    history_entries: Mapped[list["GradeHistory"]] = relationship(
        "GradeHistory",
        back_populates="grade",
        lazy="selectin",
    )
