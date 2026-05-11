from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import CourseEnrollmentStatus
from app.models.course_enrollment import CourseEnrollment


class EnrollmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def has_active_enrollment(self, student_id: uuid.UUID, course_id: uuid.UUID) -> bool:
        stmt = (
            select(CourseEnrollment.id)
            .where(
                CourseEnrollment.student_id == student_id,
                CourseEnrollment.course_id == course_id,
                CourseEnrollment.status == CourseEnrollmentStatus.ACTIVE.value,
                CourseEnrollment.deleted_at.is_(None),
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create_enrollment(self, student_id: uuid.UUID, course_id: uuid.UUID) -> CourseEnrollment:
        row = CourseEnrollment(
            student_id=student_id,
            course_id=course_id,
            status=CourseEnrollmentStatus.ACTIVE.value,
        )
        self._session.add(row)
        await self._session.flush()
        return row
