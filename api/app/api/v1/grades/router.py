from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.api.deps import GradeServiceDep
from app.api.docs import ERROR_RESPONSES
from app.api.v1.grades.schemas import GradeCreate, GradePatch, GradeRead
from app.auth.dependencies import CurrentUser
from app.auth.permissions import Permission, require_any_permission, require_permissions
from app.models.user import User
from app.utils.http import get_client_ip, get_user_agent

router = APIRouter(prefix="/grades", tags=["Grades"])


@router.post(
    "",
    response_model=GradeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create grade entry",
    description="Teacher/Dean/Admin grade write endpoint. Teachers are restricted to assigned courses.",
    responses={**ERROR_RESPONSES, 201: {"description": "Grade recorded."}},
)
async def create_grade(
    payload: GradeCreate,
    request: Request,
    grade_service: GradeServiceDep,
    actor: Annotated[
        User,
        Depends(
            require_any_permission(
                Permission.ACADEMIC_GRADE_MANAGE_ALL,
                Permission.ACADEMIC_GRADE_WRITE_ASSIGNED,
            ),
        ),
    ],
) -> GradeRead:
    grade = await grade_service.create_grade(
        actor=actor,
        student_id=payload.student_id,
        course_id=payload.course_id,
        score=payload.score,
        letter_grade=payload.letter_grade,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    return GradeRead.model_validate(grade)


@router.patch(
    "/{grade_id}",
    response_model=GradeRead,
    summary="Update grade entry",
    description="Updates score/letter and records reason for change. Action is audit logged.",
    responses={**ERROR_RESPONSES, 200: {"description": "Grade updated."}},
)
async def patch_grade(
    grade_id: uuid.UUID,
    payload: GradePatch,
    request: Request,
    grade_service: GradeServiceDep,
    actor: Annotated[
        User,
        Depends(
            require_any_permission(
                Permission.ACADEMIC_GRADE_MANAGE_ALL,
                Permission.ACADEMIC_GRADE_WRITE_ASSIGNED,
            ),
        ),
    ],
) -> GradeRead:
    grade = await grade_service.update_grade(
        actor=actor,
        grade_id=grade_id,
        score=payload.score,
        letter_grade=payload.letter_grade,
        reason=payload.reason,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    return GradeRead.model_validate(grade)


@router.get(
    "/my",
    response_model=list[GradeRead],
    summary="List my grades",
    description="Student-facing endpoint for own academic results only.",
    responses=ERROR_RESPONSES,
)
async def list_my_grades(
    current_user: Annotated[
        User, Depends(require_permissions(Permission.ACADEMIC_GRADE_READ_SELF))
    ],
    grade_service: GradeServiceDep,
) -> list[GradeRead]:
    rows = await grade_service.list_my_grades(current_user)
    return [GradeRead.model_validate(r) for r in rows]


@router.get(
    "/student/{student_id}",
    response_model=list[GradeRead],
    summary="List grades for a student",
    description="Requires authorized scope; enforces RBAC and ownership constraints.",
    responses=ERROR_RESPONSES,
)
async def list_grades_for_student(
    student_id: uuid.UUID,
    current_user: CurrentUser,
    grade_service: GradeServiceDep,
) -> list[GradeRead]:
    rows = await grade_service.list_student_grades(current_user, student_id)
    return [GradeRead.model_validate(r) for r in rows]


@router.get(
    "/course/{course_id}",
    response_model=list[GradeRead],
    summary="List grades for a course",
    description="Course-level grade access with permission and teacher-assignment checks.",
    responses=ERROR_RESPONSES,
)
async def list_grades_for_course(
    course_id: uuid.UUID,
    current_user: CurrentUser,
    grade_service: GradeServiceDep,
) -> list[GradeRead]:
    rows = await grade_service.list_course_grades(current_user, course_id)
    return [GradeRead.model_validate(r) for r in rows]
