from __future__ import annotations

import uuid

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.course import Course
from app.models.teacher import Teacher


class CourseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, course_id: uuid.UUID) -> Course | None:
        stmt = (
            select(Course)
            .options(selectinload(Course.teacher).selectinload(Teacher.user))
            .where(Course.id == course_id, Course.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_visible(self, *, skip: int, limit: int) -> list[Course]:
        stmt = (
            select(Course)
            .options(selectinload(Course.teacher))
            .where(Course.deleted_at.is_(None))
            .order_by(Course.code.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        *,
        code: str,
        title: str,
        description: str | None,
        credits: Decimal,
        teacher_id: uuid.UUID,
    ) -> Course:
        course = Course(
            code=code,
            title=title,
            description=description,
            credits=credits,
            teacher_id=teacher_id,
        )
        self._session.add(course)
        await self._session.flush()
        return course

    async def persist_teacher_assignment(self, course: Course, teacher_id: uuid.UUID) -> None:
        course.teacher_id = teacher_id
        await self._session.flush()

    async def apply_updates(
        self,
        course: Course,
        *,
        title: str | None,
        description: str | None,
        credits: Decimal | None,
        teacher_id: uuid.UUID | None,
    ) -> None:
        if title is not None:
            course.title = title
        if description is not None:
            course.description = description
        if credits is not None:
            course.credits = credits
        if teacher_id is not None:
            course.teacher_id = teacher_id
        await self._session.flush()
