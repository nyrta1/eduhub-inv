from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from starlette.responses import Response

from app.api.deps import CourseServiceDep
from app.api.docs import ERROR_RESPONSES
from app.api.v1.courses.schemas import CourseCreate, CoursePatch, CourseRead, CourseStudentEnroll
from app.auth.dependencies import CurrentUser
from app.auth.permissions import Permission, require_permissions
from app.models.course import Course
from app.models.user import User
from app.utils.http import get_client_ip, get_user_agent

router = APIRouter(prefix="/courses", tags=["Courses"])


def _course_read(course: Course) -> CourseRead:
    return CourseRead.model_validate(course)


@router.post(
    "",
    response_model=CourseRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create course",
    description="Creates a course and assigns a teacher. Requires `academic:course:manage`.",
    responses={**ERROR_RESPONSES, 201: {"description": "Course created."}},
)
async def create_course(
    payload: CourseCreate,
    request: Request,
    course_service: CourseServiceDep,
    actor: Annotated[User, Depends(require_permissions(Permission.ACADEMIC_COURSE_MANAGE))],
) -> CourseRead:
    course = await course_service.create_course(
        actor=actor,
        code=payload.code,
        title=payload.title,
        description=payload.description,
        credits=payload.credits,
        teacher_id=payload.teacher_id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    return _course_read(course)


@router.get(
    "",
    response_model=list[CourseRead],
    dependencies=[Depends(require_permissions(Permission.ACADEMIC_COURSE_READ))],
    summary="List courses",
    description="Paginated course listing for authorized academic users.",
    responses=ERROR_RESPONSES,
)
async def list_courses(
    course_service: CourseServiceDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> list[CourseRead]:
    rows = await course_service.list_courses(skip=skip, limit=limit)
    return [_course_read(c) for c in rows]


@router.get(
    "/{course_id}",
    response_model=CourseRead,
    dependencies=[Depends(require_permissions(Permission.ACADEMIC_COURSE_READ))],
    summary="Get course by ID",
    description="Returns full course details including assigned teacher summary.",
    responses=ERROR_RESPONSES,
)
async def get_course(
    course_id: uuid.UUID,
    course_service: CourseServiceDep,
) -> CourseRead:
    course = await course_service.get_course(course_id)
    return _course_read(course)


@router.patch(
    "/{course_id}",
    response_model=CourseRead,
    summary="Update course",
    description="Updates editable course attributes. Requires `academic:course:manage`.",
    responses={**ERROR_RESPONSES, 200: {"description": "Course updated."}},
)
async def patch_course(
    course_id: uuid.UUID,
    payload: CoursePatch,
    request: Request,
    course_service: CourseServiceDep,
    actor: Annotated[User, Depends(require_permissions(Permission.ACADEMIC_COURSE_MANAGE))],
) -> CourseRead:
    course = await course_service.update_course(
        actor=actor,
        course_id=course_id,
        title=payload.title,
        description=payload.description,
        credits=payload.credits,
        teacher_id=payload.teacher_id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    return _course_read(course)


@router.post(
    "/{course_id}/students",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    dependencies=[Depends(require_permissions(Permission.ACADEMIC_ENROLLMENT_MANAGE))],
    summary="Enroll student into course",
    description="Enrollment operation with anti-duplication checks and audit logging.",
    responses={**ERROR_RESPONSES, 204: {"description": "Enrollment created."}},
)
async def enroll_student_in_course(
    course_id: uuid.UUID,
    payload: CourseStudentEnroll,
    request: Request,
    course_service: CourseServiceDep,
    actor: CurrentUser,
) -> Response:
    await course_service.enroll_student(
        actor=actor,
        course_id=course_id,
        student_id=payload.student_id,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
