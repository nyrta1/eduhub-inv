from __future__ import annotations

import uuid

from sqlalchemy import distinct, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.course import Course
from app.models.course_enrollment import CourseEnrollment
from app.models.student import Student
from app.models.teacher import Teacher
class StudentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, student_id: uuid.UUID) -> Student | None:
        stmt = (
            select(Student)
            .options(selectinload(Student.user), selectinload(Student.course_enrollments))
            .where(Student.id == student_id, Student.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: uuid.UUID) -> Student | None:
        stmt = (
            select(Student)
            .options(selectinload(Student.user))
            .where(Student.user_id == user_id, Student.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, *, skip: int, limit: int) -> list[Student]:
        stmt = (
            select(Student)
            .options(selectinload(Student.user))
            .where(Student.deleted_at.is_(None))
            .order_by(Student.student_number.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_ids_for_teacher(self, teacher_user_id: uuid.UUID) -> list[uuid.UUID]:
        stmt = (
            select(distinct(CourseEnrollment.student_id))
            .join(Course, Course.id == CourseEnrollment.course_id)
            .join(Teacher, Teacher.id == Course.teacher_id)
            .where(
                Teacher.user_id == teacher_user_id,
                CourseEnrollment.deleted_at.is_(None),
                Course.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_for_teacher(self, teacher_user_id: uuid.UUID, *, skip: int, limit: int) -> list[Student]:
        stmt = (
            select(Student)
            .distinct()
            .options(selectinload(Student.user))
            .join(CourseEnrollment, CourseEnrollment.student_id == Student.id)
            .join(Course, Course.id == CourseEnrollment.course_id)
            .join(Teacher, Teacher.id == Course.teacher_id)
            .where(
                Teacher.user_id == teacher_user_id,
                CourseEnrollment.deleted_at.is_(None),
                Course.deleted_at.is_(None),
                Student.deleted_at.is_(None),
            )
            .order_by(Student.student_number.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
