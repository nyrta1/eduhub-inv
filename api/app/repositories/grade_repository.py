from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.grade import Grade


class GradeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, grade_id: uuid.UUID) -> Grade | None:
        stmt = (
            select(Grade)
            .options(selectinload(Grade.student), selectinload(Grade.course))
            .where(Grade.id == grade_id, Grade.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_for_student_course(
        self,
        student_id: uuid.UUID,
        course_id: uuid.UUID,
    ) -> Grade | None:
        stmt = (
            select(Grade)
            .where(
                Grade.student_id == student_id,
                Grade.course_id == course_id,
                Grade.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_student(self, student_id: uuid.UUID) -> list[Grade]:
        stmt = (
            select(Grade)
            .options(selectinload(Grade.course))
            .where(Grade.student_id == student_id, Grade.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_for_course(self, course_id: uuid.UUID) -> list[Grade]:
        stmt = (
            select(Grade)
            .options(selectinload(Grade.student))
            .where(Grade.course_id == course_id, Grade.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create_grade(
        self,
        *,
        student_id: uuid.UUID,
        course_id: uuid.UUID,
        score: Decimal,
        letter_grade: str | None,
    ) -> Grade:
        grade = Grade(
            student_id=student_id,
            course_id=course_id,
            score=score,
            letter_grade=letter_grade,
        )
        self._session.add(grade)
        await self._session.flush()
        return grade
