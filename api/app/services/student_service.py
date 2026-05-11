from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.academic.access import can_view_student_profile
from app.academic.gpa import compute_weighted_gpa
from app.auth.permissions import Permission, user_has_permission
from app.models.student import Student
from app.models.user import User
from app.repositories.course_repository import CourseRepository
from app.repositories.grade_repository import GradeRepository
from app.repositories.student_repository import StudentRepository
from app.domain.enums import AcademicAuditAction
from app.security.domain_audit import record_domain_event


class StudentService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._students = StudentRepository(session)
        self._grades = GradeRepository(session)
        self._courses = CourseRepository(session)

    async def get_my_profile(self, viewer: User) -> tuple[Student, Decimal]:
        student = await self._students.get_by_user_id(viewer.id)
        if student is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found.")
        gpa = await self._compute_gpa(student.id)
        return student, gpa

    async def get_student_profile(self, viewer: User, student_id: uuid.UUID) -> tuple[Student, Decimal]:
        allowed = await can_view_student_profile(self._session, viewer, student_id)
        if not allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")
        student = await self._students.get_by_id(student_id)
        if student is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found.")
        gpa = await self._compute_gpa(student.id)
        return student, gpa

    async def list_students(
        self,
        viewer: User,
        *,
        skip: int,
        limit: int,
    ) -> list[Student]:
        if user_has_permission(viewer, Permission.ACADEMIC_STUDENT_READ_ANY):
            return await self._students.list_all(skip=skip, limit=limit)
        if user_has_permission(viewer, Permission.ACADEMIC_STUDENT_READ_ROSTER):
            return await self._students.list_for_teacher(viewer.id, skip=skip, limit=limit)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

    async def update_student_profile(
        self,
        *,
        viewer: User,
        student_id: uuid.UUID,
        academic_group: str | None,
        specialty: str | None,
        enrollment_date: date | None,
        academic_status: str | None,
        enrollment_status: str | None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> Student:
        student = await self._students.get_by_id(student_id)
        if student is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found.")

        if user_has_permission(viewer, Permission.ACADEMIC_STUDENT_UPDATE_ANY):
            if academic_group is not None:
                student.academic_group = academic_group
            if specialty is not None:
                student.specialty = specialty
            if enrollment_date is not None:
                student.enrollment_date = enrollment_date
            if academic_status is not None:
                student.academic_status = academic_status
            if enrollment_status is not None:
                student.enrollment_status = enrollment_status
        elif student.user_id == viewer.id and user_has_permission(viewer, Permission.ACADEMIC_STUDENT_UPDATE_SELF):
            if academic_group is not None:
                student.academic_group = academic_group
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

        await record_domain_event(
            self._session,
            action=AcademicAuditAction.STUDENT_UPDATED.value,
            resource_type="student",
            resource_id=student.id,
            actor_user_id=viewer.id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"fields": "partial_update"},
        )
        await self._session.commit()
        refreshed = await self._students.get_by_id(student.id)
        assert refreshed is not None
        return refreshed

    async def _compute_gpa(self, student_id: uuid.UUID) -> Decimal:
        grades = await self._grades.list_for_student(student_id)
        rows: list[tuple[Decimal, Decimal]] = []
        for grade in grades:
            course = await self._courses.get_by_id(grade.course_id)
            if course is None:
                continue
            rows.append((grade.score, course.credits))
        return compute_weighted_gpa(rows)
