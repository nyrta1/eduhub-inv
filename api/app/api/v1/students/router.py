from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import StudentServiceDep
from app.api.docs import ERROR_RESPONSES
from app.api.v1.students.schemas import StudentPatch, StudentProfileResponse, StudentRead
from app.auth.dependencies import CurrentUser
from app.auth.permissions import Permission, require_any_permission, require_permissions
from app.models.user import User
from app.utils.http import get_client_ip, get_user_agent

router = APIRouter(prefix="/students", tags=["Students"])


@router.get(
    "/me",
    response_model=StudentProfileResponse,
    summary="Get my student profile",
    description="Returns student profile and computed GPA for the authenticated student account.",
    responses=ERROR_RESPONSES,
)
async def get_my_student_profile(
    current_user: Annotated[
        User, Depends(require_permissions(Permission.ACADEMIC_STUDENT_READ_SELF))
    ],
    student_service: StudentServiceDep,
) -> StudentProfileResponse:
    student, gpa = await student_service.get_my_profile(current_user)
    return StudentProfileResponse(student=StudentRead.model_validate(student), gpa=gpa)


@router.get(
    "",
    response_model=list[StudentRead],
    dependencies=[
        Depends(
            require_any_permission(
                Permission.ACADEMIC_STUDENT_READ_ANY,
                Permission.ACADEMIC_STUDENT_READ_ROSTER,
            ),
        ),
    ],
    summary="List students",
    description="Dean/Admin can query all students; teachers are limited to roster-eligible scopes.",
    responses=ERROR_RESPONSES,
)
async def list_students(
    current_user: CurrentUser,
    student_service: StudentServiceDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> list[StudentRead]:
    rows = await student_service.list_students(current_user, skip=skip, limit=limit)
    return [StudentRead.model_validate(r) for r in rows]


@router.get(
    "/{student_id}",
    response_model=StudentProfileResponse,
    summary="Get student profile by ID",
    description="Access is governed by ownership and RBAC scope rules.",
    responses=ERROR_RESPONSES,
)
async def get_student(
    student_id: uuid.UUID,
    current_user: CurrentUser,
    student_service: StudentServiceDep,
) -> StudentProfileResponse:
    student, gpa = await student_service.get_student_profile(current_user, student_id)
    return StudentProfileResponse(student=StudentRead.model_validate(student), gpa=gpa)


@router.patch(
    "/{student_id}",
    response_model=StudentRead,
    summary="Update student profile fields",
    description="Allows controlled updates to academic profile attributes with audit logging.",
    responses={**ERROR_RESPONSES, 200: {"description": "Student profile updated."}},
)
async def patch_student(
    student_id: uuid.UUID,
    payload: StudentPatch,
    request: Request,
    current_user: CurrentUser,
    student_service: StudentServiceDep,
) -> StudentRead:
    student = await student_service.update_student_profile(
        viewer=current_user,
        student_id=student_id,
        academic_group=payload.academic_group,
        specialty=payload.specialty,
        enrollment_date=payload.enrollment_date,
        academic_status=payload.academic_status,
        enrollment_status=payload.enrollment_status,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    return StudentRead.model_validate(student)
