from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request, status

from app.api.deps import AuthServiceDep
from app.api.docs import ERROR_RESPONSES
from app.api.v1.auth.schemas import AdminRoleUpdate, UserPublic
from app.auth.permissions import RoleName, require_roles_dep
from app.models.user import User
from app.utils.http import get_client_ip, get_user_agent

router = APIRouter(prefix="/users", tags=["Users"])


def _serialize_user(user: User) -> UserPublic:
    return UserPublic(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        roles=[role.name for role in user.roles],
    )


@router.patch(
    "/{user_id}/role",
    response_model=UserPublic,
    status_code=status.HTTP_200_OK,
    summary="Assign role to user (ADMIN only)",
    description="Administrative RBAC operation. Requires ADMIN role and emits audit events for security review.",
    responses={**ERROR_RESPONSES, 200: {"description": "Role updated."}},
)
async def update_user_role(
    user_id: uuid.UUID,
    payload: AdminRoleUpdate,
    request: Request,
    auth_service: AuthServiceDep,
    actor: User = Depends(require_roles_dep(RoleName.ADMIN)),
) -> UserPublic:
    target = await auth_service.admin_assign_role(
        actor=actor,
        target_user_id=user_id,
        new_role=payload.role,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )
    return _serialize_user(target)
