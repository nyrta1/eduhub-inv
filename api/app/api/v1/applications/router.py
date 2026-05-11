from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.deps import ApplicationServiceDep
from app.api.docs import ERROR_RESPONSES
from app.api.v1.applications.schemas import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationStatusPatch,
)
from app.auth.dependencies import CurrentUser
from app.auth.permissions import Permission, require_permissions
from app.models.user import User
from app.utils.http import get_client_ip, get_user_agent

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post(
    "",
    response_model=ApplicationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Submit enrollment application",
    description="Student workflow endpoint. Requires `academic:application:submit`; rate-limited and audit logged.",
    responses={**ERROR_RESPONSES, 201: {"description": "Application submitted."}},
)
async def submit_application(
    payload: ApplicationCreate,
    request: Request,
    application_service: ApplicationServiceDep,
    current_user: Annotated[
        User, Depends(require_permissions(Permission.ACADEMIC_APPLICATION_SUBMIT))
    ],
) -> ApplicationRead:
    row = await application_service.submit_application(
        applicant=current_user,
        program_code=payload.program_code,
        intake_term=payload.intake_term,
        statement=payload.statement,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    return ApplicationRead.model_validate(row)


@router.get(
    "/my",
    response_model=list[ApplicationRead],
    summary="List current user's applications",
    description="Returns only applications owned by the authenticated user.",
    responses=ERROR_RESPONSES,
)
async def list_my_applications(
    current_user: CurrentUser,
    application_service: ApplicationServiceDep,
) -> list[ApplicationRead]:
    rows = await application_service.list_my_applications(current_user)
    return [ApplicationRead.model_validate(r) for r in rows]


@router.get(
    "",
    response_model=list[ApplicationRead],
    dependencies=[Depends(require_permissions(Permission.ACADEMIC_APPLICATION_READ_ANY))],
    summary="List applications (review queue)",
    description="Dean/Admin workflow endpoint with pagination. Requires `academic:application:read:any`.",
    responses=ERROR_RESPONSES,
)
async def list_applications(
    current_user: CurrentUser,
    application_service: ApplicationServiceDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> list[ApplicationRead]:
    rows = await application_service.list_all_applications(current_user, skip=skip, limit=limit)
    return [ApplicationRead.model_validate(r) for r in rows]


@router.get(
    "/{application_id}",
    response_model=ApplicationRead,
    summary="Get application by ID",
    description="Ownership and privilege checks are enforced; unauthorized access attempts are denied and logged.",
    responses=ERROR_RESPONSES,
)
async def get_application(
    application_id: uuid.UUID,
    current_user: CurrentUser,
    application_service: ApplicationServiceDep,
) -> ApplicationRead:
    row = await application_service.get_application(current_user, application_id)
    return ApplicationRead.model_validate(row)


@router.patch(
    "/{application_id}/status",
    response_model=ApplicationRead,
    summary="Review application status",
    description="Dean/Admin review action. Requires `academic:application:review`. Review notes are audit logged.",
    responses={**ERROR_RESPONSES, 200: {"description": "Application status updated."}},
)
async def patch_application_status(
    application_id: uuid.UUID,
    payload: ApplicationStatusPatch,
    request: Request,
    application_service: ApplicationServiceDep,
    reviewer: Annotated[User, Depends(require_permissions(Permission.ACADEMIC_APPLICATION_REVIEW))],
) -> ApplicationRead:
    row = await application_service.update_status(
        reviewer=reviewer,
        application_id=application_id,
        new_status=payload.status,
        notes=payload.notes,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    return ApplicationRead.model_validate(row)
