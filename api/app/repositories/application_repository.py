from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.enums import ApplicationStatus
from app.models.enrollment_application import EnrollmentApplication


class ApplicationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, application_id: uuid.UUID) -> EnrollmentApplication | None:
        stmt = (
            select(EnrollmentApplication)
            .options(
                selectinload(EnrollmentApplication.applicant),
                selectinload(EnrollmentApplication.reviewer),
            )
            .where(
                EnrollmentApplication.id == application_id,
                EnrollmentApplication.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_applicant(self, applicant_user_id: uuid.UUID) -> list[EnrollmentApplication]:
        stmt = (
            select(EnrollmentApplication)
            .where(
                EnrollmentApplication.applicant_user_id == applicant_user_id,
                EnrollmentApplication.deleted_at.is_(None),
            )
            .order_by(EnrollmentApplication.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(self, *, skip: int, limit: int) -> list[EnrollmentApplication]:
        stmt = (
            select(EnrollmentApplication)
            .options(
                selectinload(EnrollmentApplication.applicant),
                selectinload(EnrollmentApplication.reviewer),
            )
            .where(EnrollmentApplication.deleted_at.is_(None))
            .order_by(EnrollmentApplication.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_open_application(
        self,
        *,
        applicant_user_id: uuid.UUID,
        program_code: str,
        intake_term: str,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(EnrollmentApplication)
            .where(
                EnrollmentApplication.applicant_user_id == applicant_user_id,
                EnrollmentApplication.program_code == program_code,
                EnrollmentApplication.intake_term == intake_term,
                EnrollmentApplication.deleted_at.is_(None),
                EnrollmentApplication.status.in_(
                    [
                        ApplicationStatus.PENDING.value,
                        ApplicationStatus.UNDER_REVIEW.value,
                        ApplicationStatus.APPROVED.value,
                    ],
                ),
            )
        )
        result = await self._session.execute(stmt)
        return int(result.scalar_one())
