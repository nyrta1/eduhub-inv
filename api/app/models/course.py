from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Course(Base):
    __tablename__ = "courses"
    __table_args__ = (
        Index("ix_courses_teacher_id", "teacher_id"),
        Index("ix_courses_code", "code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    credits: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("teachers.id", ondelete="RESTRICT"),
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

    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="courses")
    grades: Mapped[list["Grade"]] = relationship(
        "Grade",
        back_populates="course",
        lazy="selectin",
    )
    enrollments: Mapped[list["CourseEnrollment"]] = relationship(
        "CourseEnrollment",
        back_populates="course",
        lazy="selectin",
    )
