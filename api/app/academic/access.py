from __future__ import annotations

import uuid

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import Permission, RoleName, user_has_permission
from app.models.course import Course
from app.models.course_enrollment import CourseEnrollment
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.user import User


async def get_teacher_record(session: AsyncSession, user_id: uuid.UUID) -> Teacher | None:
    stmt = select(Teacher).where(Teacher.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def teacher_teaches_course(
    session: AsyncSession,
    *,
    teacher_user_id: uuid.UUID,
    course_id: uuid.UUID,
) -> bool:
    stmt = (
        select(Course.id)
        .join(Teacher, Teacher.id == Course.teacher_id)
        .where(Teacher.user_id == teacher_user_id, Course.id == course_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


async def teacher_has_student_in_roster(
    session: AsyncSession,
    *,
    teacher_user_id: uuid.UUID,
    student_id: uuid.UUID,
) -> bool:
    stmt = (
        select(CourseEnrollment.id)
        .join(Course, Course.id == CourseEnrollment.course_id)
        .join(Teacher, Teacher.id == Course.teacher_id)
        .where(
            Teacher.user_id == teacher_user_id,
            CourseEnrollment.student_id == student_id,
            CourseEnrollment.deleted_at.is_(None),
            Course.deleted_at.is_(None),
        )
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


async def student_enrolled_in_course(
    session: AsyncSession,
    *,
    student_id: uuid.UUID,
    course_id: uuid.UUID,
) -> bool:
    stmt = (
        select(CourseEnrollment.id)
        .where(
            CourseEnrollment.student_id == student_id,
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.status == "ACTIVE",
            CourseEnrollment.deleted_at.is_(None),
        )
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


def viewer_is_dean_or_admin(user: User) -> bool:
    names = {role.name for role in user.roles}
    return RoleName.DEAN.value in names or RoleName.ADMIN.value in names


async def can_view_student_profile(session: AsyncSession, viewer: User, student_id: uuid.UUID) -> bool:
    if viewer_is_dean_or_admin(viewer):
        return True
    stmt = select(Student).where(Student.id == student_id)
    student = (await session.execute(stmt)).scalar_one_or_none()
    if student is None:
        return False
    if student.user_id == viewer.id:
        return True
    if user_has_permission(viewer, Permission.ACADEMIC_STUDENT_READ_ROSTER):
        teacher_row = await get_teacher_record(session, viewer.id)
        if teacher_row is None:
            return False
        return await teacher_has_student_in_roster(session, teacher_user_id=viewer.id, student_id=student_id)
    return False


async def can_manage_course(session: AsyncSession, viewer: User, course_id: uuid.UUID) -> bool:
    if user_has_permission(viewer, Permission.ACADEMIC_COURSE_MANAGE):
        return True
    if user_has_permission(viewer, Permission.ACADEMIC_GRADE_WRITE_ASSIGNED):
        return await teacher_teaches_course(session, teacher_user_id=viewer.id, course_id=course_id)
    return False


def accessible_student_query_for_viewer(viewer: User) -> Select | None:
    """Return filter clause for Student queries or None when restricted empty."""
    if viewer_is_dean_or_admin(viewer):
        return select(Student.id)
    if user_has_permission(viewer, Permission.ACADEMIC_STUDENT_READ_SELF):
        # caller must still intersect with viewer's student profile id
        return select(Student.id).where(Student.user_id == viewer.id)
    if user_has_permission(viewer, Permission.ACADEMIC_STUDENT_READ_ROSTER):
        return (
            select(Student.id)
            .join(CourseEnrollment, CourseEnrollment.student_id == Student.id)
            .join(Course, Course.id == CourseEnrollment.course_id)
            .join(Teacher, Teacher.id == Course.teacher_id)
            .where(
                Teacher.user_id == viewer.id,
                CourseEnrollment.deleted_at.is_(None),
                Student.deleted_at.is_(None),
            )
            .distinct()
        )
    return None
