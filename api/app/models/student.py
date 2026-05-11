from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Index, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Student(Base):
    __tablename__ = "students"
    __table_args__ = (
        Index("ix_students_user_id", "user_id"),
        Index("ix_students_student_number", "student_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
    )
    student_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    enrollment_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    academic_group: Mapped[str | None] = mapped_column(String(64), nullable=True)
    specialty: Mapped[str | None] = mapped_column(String(255), nullable=True)
    enrollment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    academic_status: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
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

    user: Mapped["User"] = relationship("User", back_populates="student_profile")
    grades: Mapped[list["Grade"]] = relationship(
        "Grade",
        back_populates="student",
        lazy="selectin",
    )
    course_enrollments: Mapped[list["CourseEnrollment"]] = relationship(
        "CourseEnrollment",
        back_populates="student",
        lazy="selectin",
    )
