from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.academic.access import (
    student_enrolled_in_course,
    teacher_has_student_in_roster,
    teacher_teaches_course,
)
from app.auth.permissions import Permission, user_has_permission
from app.domain.enums import AcademicAuditAction
from app.models.grade import Grade
from app.models.grade_history import GradeHistory
from app.models.user import User
from app.repositories.course_repository import CourseRepository
from app.repositories.grade_repository import GradeRepository
from app.repositories.student_repository import StudentRepository
from app.security.domain_audit import record_domain_event


class GradeService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._grades = GradeRepository(session)
        self._courses = CourseRepository(session)
        self._students = StudentRepository(session)

    async def create_grade(
        self,
        *,
        actor: User,
        student_id: uuid.UUID,
        course_id: uuid.UUID,
        score: Decimal,
        letter_grade: str | None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> Grade:
        await self._ensure_grade_authorization(actor, course_id=course_id)

        enrolled = await student_enrolled_in_course(self._session, student_id=student_id, course_id=course_id)
        if not enrolled:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Student is not actively enrolled.")

        existing = await self._grades.find_for_student_course(student_id, course_id)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Grade already exists.")

        grade = await self._grades.create_grade(
            student_id=student_id,
            course_id=course_id,
            score=score,
            letter_grade=letter_grade,
        )

        history = GradeHistory(
            grade_id=grade.id,
            previous_score=None,
            new_score=score,
            actor_user_id=actor.id,
            reason="initial_record",
        )
        self._session.add(history)

        await record_domain_event(
            self._session,
            action=AcademicAuditAction.GRADE_CREATED.value,
            resource_type="grade",
            resource_id=grade.id,
            actor_user_id=actor.id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={
                "student_id": str(student_id),
                "course_id": str(course_id),
                "score": str(score),
            },
        )
        await self._session.commit()
        refreshed = await self._grades.get_by_id(grade.id)
        assert refreshed is not None
        return refreshed

    async def update_grade(
        self,
        *,
        actor: User,
        grade_id: uuid.UUID,
        score: Decimal,
        letter_grade: str | None,
        reason: str | None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> Grade:
        grade = await self._grades.get_by_id(grade_id)
        if grade is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grade not found.")

        await self._ensure_grade_authorization(actor, course_id=grade.course_id)

        previous = grade.score
        grade.score = score
        grade.letter_grade = letter_grade

        history = GradeHistory(
            grade_id=grade.id,
            previous_score=previous,
            new_score=score,
            actor_user_id=actor.id,
            reason=reason,
        )
        self._session.add(history)

        await record_domain_event(
            self._session,
            action=AcademicAuditAction.GRADE_UPDATED.value,
            resource_type="grade",
            resource_id=grade.id,
            actor_user_id=actor.id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={
                "previous_score": str(previous),
                "new_score": str(score),
            },
        )
        await self._session.commit()
        refreshed = await self._grades.get_by_id(grade.id)
        assert refreshed is not None
        return refreshed

    async def list_my_grades(self, viewer: User) -> list[Grade]:
        student = await self._students.get_by_user_id(viewer.id)
        if student is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found.")
        return await self._grades.list_for_student(student.id)

    async def list_student_grades(self, viewer: User, student_id: uuid.UUID) -> list[Grade]:
        student = await self._students.get_by_id(student_id)
        if student is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found.")

        if student.user_id == viewer.id and user_has_permission(viewer, Permission.ACADEMIC_GRADE_READ_SELF):
            return await self._grades.list_for_student(student.id)

        if user_has_permission(viewer, Permission.ACADEMIC_GRADE_READ_ANY):
            return await self._grades.list_for_student(student.id)

        if user_has_permission(viewer, Permission.ACADEMIC_STUDENT_READ_ROSTER):
            allowed = await teacher_has_student_in_roster(self._session, teacher_user_id=viewer.id, student_id=student.id)
            if allowed:
                return await self._grades.list_for_student(student.id)

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

    async def list_course_grades(self, viewer: User, course_id: uuid.UUID) -> list[Grade]:
        course = await self._courses.get_by_id(course_id)
        if course is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found.")

        if user_has_permission(viewer, Permission.ACADEMIC_GRADE_READ_ANY):
            return await self._grades.list_for_course(course_id)

        owns_course = await teacher_teaches_course(self._session, teacher_user_id=viewer.id, course_id=course_id)
        if owns_course and user_has_permission(viewer, Permission.ACADEMIC_COURSE_READ):
            return await self._grades.list_for_course(course_id)

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

    async def _ensure_grade_authorization(self, actor: User, *, course_id: uuid.UUID) -> None:
        if user_has_permission(actor, Permission.ACADEMIC_GRADE_MANAGE_ALL):
            return
        if user_has_permission(actor, Permission.ACADEMIC_GRADE_WRITE_ASSIGNED):
            owns = await teacher_teaches_course(self._session, teacher_user_id=actor.id, course_id=course_id)
            if owns:
                return
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

