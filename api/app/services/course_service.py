from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.academic.access import teacher_teaches_course, viewer_is_dean_or_admin
from app.auth.permissions import Permission, user_has_permission
from app.domain.enums import AcademicAuditAction
from app.models.course import Course
from app.models.user import User
from app.repositories.course_repository import CourseRepository
from app.repositories.enrollment_repository import EnrollmentRepository
from app.repositories.student_repository import StudentRepository
from app.security.domain_audit import record_domain_event


class CourseService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._courses = CourseRepository(session)
        self._enrollments = EnrollmentRepository(session)
        self._students = StudentRepository(session)

    async def create_course(
        self,
        *,
        actor: User,
        code: str,
        title: str,
        description: str | None,
        credits: Decimal,
        teacher_id: uuid.UUID,
        ip_address: str | None,
        user_agent: str | None,
    ) -> Course:
        if not user_has_permission(actor, Permission.ACADEMIC_COURSE_MANAGE):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

        course = await self._courses.create(
            code=code.strip(),
            title=title.strip(),
            description=description,
            credits=credits,
            teacher_id=teacher_id,
        )

        await record_domain_event(
            self._session,
            action=AcademicAuditAction.COURSE_CREATED.value,
            resource_type="course",
            resource_id=course.id,
            actor_user_id=actor.id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"code": course.code},
        )
        await self._session.commit()
        refreshed = await self._courses.get_by_id(course.id)
        assert refreshed is not None
        return refreshed

    async def list_courses(self, *, skip: int, limit: int) -> list[Course]:
        return await self._courses.list_visible(skip=skip, limit=limit)

    async def get_course(self, course_id: uuid.UUID) -> Course:
        course = await self._courses.get_by_id(course_id)
        if course is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")
        return course

    async def update_course(
        self,
        *,
        actor: User,
        course_id: uuid.UUID,
        title: str | None,
        description: str | None,
        credits: Decimal | None,
        teacher_id: uuid.UUID | None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> Course:
        course = await self._courses.get_by_id(course_id)
        if course is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")

        if not user_has_permission(actor, Permission.ACADEMIC_COURSE_MANAGE):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

        previous_teacher = course.teacher_id
        await self._courses.apply_updates(
            course,
            title=title,
            description=description,
            credits=credits,
            teacher_id=teacher_id,
        )

        await record_domain_event(
            self._session,
            action=AcademicAuditAction.COURSE_UPDATED.value,
            resource_type="course",
            resource_id=course.id,
            actor_user_id=actor.id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={
                "teacher_changed": bool(teacher_id),
                "previous_teacher_id": str(previous_teacher),
            },
        )

        if teacher_id is not None and teacher_id != previous_teacher:
            await record_domain_event(
                self._session,
                action=AcademicAuditAction.TEACHER_ASSIGNMENT.value,
                resource_type="course",
                resource_id=course.id,
                actor_user_id=actor.id,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={
                    "previous_teacher_id": str(previous_teacher),
                    "new_teacher_id": str(teacher_id),
                },
            )

        await self._session.commit()
        refreshed = await self._courses.get_by_id(course.id)
        assert refreshed is not None
        return refreshed

    async def enroll_student(
        self,
        *,
        actor: User,
        course_id: uuid.UUID,
        student_id: uuid.UUID,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        course = await self._courses.get_by_id(course_id)
        if course is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")

        student = await self._students.get_by_id(student_id)
        if student is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found.")

        if viewer_is_dean_or_admin(actor):
            allowed = True
        elif user_has_permission(actor, Permission.ACADEMIC_ENROLLMENT_MANAGE) and await teacher_teaches_course(
            self._session,
            teacher_user_id=actor.id,
            course_id=course_id,
        ):
            allowed = True
        else:
            allowed = False

        if not allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

        exists = await self._enrollments.has_active_enrollment(student_id, course_id)
        if exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already enrolled.")

        await self._enrollments.create_enrollment(student_id, course_id)

        await record_domain_event(
            self._session,
            action=AcademicAuditAction.COURSE_ENROLLMENT_CREATED.value,
            resource_type="course_enrollment",
            resource_id=course_id,
            actor_user_id=actor.id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={
                "student_id": str(student_id),
                "course_id": str(course_id),
            },
        )
        await self._session.commit()
