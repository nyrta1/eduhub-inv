from __future__ import annotations

from enum import Enum
from typing import Callable, Iterable

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.models.role import Role
from app.models.user import User


class RoleName(str, Enum):
    STUDENT = "STUDENT"
    TEACHER = "TEACHER"
    DEAN = "DEAN"
    ADMIN = "ADMIN"


class Permission(str, Enum):
    AUTH_SELF_READ = "auth:self:read"
    AUTH_SELF_MANAGE = "auth:self:manage"
    USERS_READ_ANY = "users:read:any"
    USERS_ROLE_ASSIGN = "users:role:assign"

    ACADEMIC_APPLICATION_SUBMIT = "academic:application:submit"
    ACADEMIC_APPLICATION_REVIEW = "academic:application:review"
    ACADEMIC_APPLICATION_READ_ANY = "academic:application:read:any"

    ACADEMIC_STUDENT_READ_SELF = "academic:student:read:self"
    ACADEMIC_STUDENT_UPDATE_SELF = "academic:student:update:self"
    ACADEMIC_STUDENT_READ_ANY = "academic:student:read:any"
    ACADEMIC_STUDENT_UPDATE_ANY = "academic:student:update:any"
    ACADEMIC_STUDENT_READ_ROSTER = "academic:student:read:roster"

    ACADEMIC_COURSE_READ = "academic:course:read"
    ACADEMIC_COURSE_MANAGE = "academic:course:manage"

    ACADEMIC_ENROLLMENT_MANAGE = "academic:enrollment:manage"

    ACADEMIC_GRADE_READ_SELF = "academic:grade:read:self"
    ACADEMIC_GRADE_READ_ANY = "academic:grade:read:any"
    ACADEMIC_GRADE_WRITE_ASSIGNED = "academic:grade:write:assigned"
    ACADEMIC_GRADE_MANAGE_ALL = "academic:grade:manage:all"


_ROLE_PERMISSIONS: dict[RoleName, frozenset[Permission]] = {
    RoleName.STUDENT: frozenset(
        {
            Permission.AUTH_SELF_READ,
            Permission.AUTH_SELF_MANAGE,
            Permission.ACADEMIC_APPLICATION_SUBMIT,
            Permission.ACADEMIC_STUDENT_READ_SELF,
            Permission.ACADEMIC_STUDENT_UPDATE_SELF,
            Permission.ACADEMIC_COURSE_READ,
            Permission.ACADEMIC_GRADE_READ_SELF,
        },
    ),
    RoleName.TEACHER: frozenset(
        {
            Permission.AUTH_SELF_READ,
            Permission.AUTH_SELF_MANAGE,
            Permission.ACADEMIC_COURSE_READ,
            Permission.ACADEMIC_STUDENT_READ_ROSTER,
            Permission.ACADEMIC_ENROLLMENT_MANAGE,
            Permission.ACADEMIC_GRADE_WRITE_ASSIGNED,
        },
    ),
    RoleName.DEAN: frozenset(
        {
            Permission.AUTH_SELF_READ,
            Permission.AUTH_SELF_MANAGE,
            Permission.USERS_READ_ANY,
            Permission.ACADEMIC_APPLICATION_REVIEW,
            Permission.ACADEMIC_APPLICATION_READ_ANY,
            Permission.ACADEMIC_STUDENT_READ_ANY,
            Permission.ACADEMIC_STUDENT_UPDATE_ANY,
            Permission.ACADEMIC_COURSE_READ,
            Permission.ACADEMIC_COURSE_MANAGE,
            Permission.ACADEMIC_ENROLLMENT_MANAGE,
            Permission.ACADEMIC_GRADE_READ_ANY,
            Permission.ACADEMIC_GRADE_MANAGE_ALL,
        },
    ),
    RoleName.ADMIN: frozenset(
        {
            permission for permission in Permission
        },
    ),
}


def permissions_for_roles(role_names: Iterable[str]) -> set[Permission]:
    resolved: set[Permission] = set()
    for name in role_names:
        try:
            role_enum = RoleName(name)
        except ValueError:
            continue
        resolved.update(_ROLE_PERMISSIONS.get(role_enum, frozenset()))
    return resolved


def user_permissions(user: User) -> set[Permission]:
    names = {role.name for role in user.roles}
    return permissions_for_roles(names)


def user_has_permission(user: User, permission: Permission) -> bool:
    return permission in user_permissions(user)


def require_permissions(*required: Permission) -> Callable[..., User]:
    async def dependency(current_user: User = Depends(get_current_active_user)) -> User:
        granted = user_permissions(current_user)
        missing = [perm for perm in required if perm not in granted]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "forbidden", "message": "Insufficient permissions."},
            )
        return current_user

    return dependency


def require_any_permission(*choices: Permission) -> Callable[..., User]:
    """Grant access when the user holds at least one of the listed permissions."""

    async def dependency(current_user: User = Depends(get_current_active_user)) -> User:
        granted = user_permissions(current_user)
        if any(perm in granted for perm in choices):
            return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "forbidden", "message": "Insufficient permissions."},
        )

    return dependency


def require_roles_dep(*roles: RoleName) -> Callable[..., User]:
    allowed = {role.value for role in roles}

    async def dependency(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        names = {role.name for role in current_user.roles}
        if not names.intersection(allowed):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "forbidden", "message": "Insufficient role membership."},
            )
        return current_user

    return dependency


async def load_role_by_name(session: AsyncSession, name: RoleName) -> Role | None:
    stmt = select(Role).where(Role.name == name.value)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
