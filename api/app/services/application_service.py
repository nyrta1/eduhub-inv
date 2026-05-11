from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.permissions import Permission, user_has_permission
from app.domain.enums import AcademicAuditAction, AcademicStatus, ApplicationStatus
from app.models.enrollment_application import EnrollmentApplication
from app.models.student import Student
from app.models.user import User
from app.repositories.application_repository import ApplicationRepository
from app.repositories.student_repository import StudentRepository
from app.security.domain_audit import record_domain_event


class ApplicationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._applications = ApplicationRepository(session)
        self._students = StudentRepository(session)

    async def submit_application(
        self,
        *,
        applicant: User,
        program_code: str,
        intake_term: str,
        statement: str | None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> EnrollmentApplication:
        normalized_program = program_code.strip()
        normalized_term = intake_term.strip()
        open_count = await self._applications.count_open_application(
            applicant_user_id=applicant.id,
            program_code=normalized_program,
            intake_term=normalized_term,
        )
        if open_count > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "duplicate_application", "message": "An open application already exists."},
            )

        application = EnrollmentApplication(
            applicant_user_id=applicant.id,
            status=ApplicationStatus.PENDING.value,
            program_code=normalized_program,
            intake_term=normalized_term,
            statement=statement,
        )
        self._session.add(application)
        await self._session.flush()

        await record_domain_event(
            self._session,
            action=AcademicAuditAction.APPLICATION_SUBMITTED.value,
            resource_type="enrollment_application",
            resource_id=application.id,
            actor_user_id=applicant.id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={
                "program_code": normalized_program,
                "intake_term": normalized_term,
            },
        )
        await self._session.commit()
        await self._session.refresh(application)
        return application

    async def list_my_applications(self, applicant: User) -> list[EnrollmentApplication]:
        rows = await self._applications.list_for_applicant(applicant.id)
        return rows

    async def get_application(self, viewer: User, application_id: uuid.UUID) -> EnrollmentApplication:
        application = await self._applications.get_by_id(application_id)
        if application is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")
        if application.applicant_user_id != viewer.id and not user_has_permission(
            viewer,
            Permission.ACADEMIC_APPLICATION_READ_ANY,
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")
        return application

    async def list_all_applications(self, viewer: User, *, skip: int, limit: int) -> list[EnrollmentApplication]:
        if not user_has_permission(viewer, Permission.ACADEMIC_APPLICATION_READ_ANY):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")
        return await self._applications.list_all(skip=skip, limit=limit)

    async def update_status(
        self,
        *,
        reviewer: User,
        application_id: uuid.UUID,
        new_status: ApplicationStatus,
        notes: str | None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> EnrollmentApplication:
        if not user_has_permission(reviewer, Permission.ACADEMIC_APPLICATION_REVIEW):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

        application = await self._applications.get_by_id(application_id)
        if application is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")

        if application.applicant_user_id == reviewer.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Reviewers cannot modify their own applications.",
            )

        current = ApplicationStatus(application.status)
        if current in {ApplicationStatus.REJECTED, ApplicationStatus.ENROLLED}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Application is closed.")

        if new_status == ApplicationStatus.UNDER_REVIEW:
            if current != ApplicationStatus.PENDING:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invalid transition.")
            application.status = ApplicationStatus.UNDER_REVIEW.value
            application.reviewed_by_user_id = reviewer.id
            application.reviewed_at = datetime.now(timezone.utc)
            application.decision_notes = notes

        elif new_status == ApplicationStatus.REJECTED:
            if current != ApplicationStatus.UNDER_REVIEW:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invalid transition.")
            application.status = ApplicationStatus.REJECTED.value
            application.reviewed_by_user_id = reviewer.id
            application.reviewed_at = datetime.now(timezone.utc)
            application.decision_notes = notes

        elif new_status == ApplicationStatus.APPROVED:
            if current != ApplicationStatus.UNDER_REVIEW:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invalid transition.")
            application.status = ApplicationStatus.APPROVED.value
            application.reviewed_by_user_id = reviewer.id
            application.reviewed_at = datetime.now(timezone.utc)
            application.decision_notes = notes
            await self._session.flush()

            student_record = await self._students.get_by_user_id(application.applicant_user_id)
            if student_record is None:
                student_record = Student(
                    user_id=application.applicant_user_id,
                    student_number=_generate_student_number(),
                    enrollment_status="ENROLLED",
                    specialty=application.program_code,
                    enrollment_date=date.today(),
                    academic_status=AcademicStatus.ACTIVE.value,
                    academic_group="GENERAL",
                )
                self._session.add(student_record)
                await self._session.flush()
            else:
                student_record.enrollment_status = "ENROLLED"
                student_record.specialty = application.program_code
                if student_record.enrollment_date is None:
                    student_record.enrollment_date = date.today()

            application.resulting_student_id = student_record.id
            application.status = ApplicationStatus.ENROLLED.value

        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported status.")

        await record_domain_event(
            self._session,
            action=AcademicAuditAction.APPLICATION_STATUS_CHANGED.value,
            resource_type="enrollment_application",
            resource_id=application.id,
            actor_user_id=reviewer.id,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={
                "previous_status": current.value,
                "new_status": application.status,
                "notes_present": bool(notes),
            },
        )

        await self._session.commit()
        refreshed = await self._applications.get_by_id(application.id)
        assert refreshed is not None
        return refreshed


def _generate_student_number() -> str:
    return f"STU-{uuid.uuid4().hex[:10].upper()}"
