from __future__ import annotations

from typing import Annotated

import redis.asyncio as redis
from fastapi import Depends

from app.auth.service import AuthService
from app.services.application_service import ApplicationService
from app.services.course_service import CourseService
from app.services.grade_service import GradeService
from app.services.student_service import StudentService
from app.core.config import Settings, get_settings
from app.core.redis_client import get_redis_dependency
from app.db.session import SessionDep

SettingsDep = Annotated[Settings, Depends(get_settings)]
RedisDep = Annotated[redis.Redis, Depends(get_redis_dependency)]


async def get_auth_service(
    session: SessionDep,
    redis_client: RedisDep,
    settings: SettingsDep,
) -> AuthService:
    return AuthService(session, redis_client, settings)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


async def get_application_service(session: SessionDep) -> ApplicationService:
    return ApplicationService(session)


async def get_student_service(session: SessionDep) -> StudentService:
    return StudentService(session)


async def get_course_service(session: SessionDep) -> CourseService:
    return CourseService(session)


async def get_grade_service(session: SessionDep) -> GradeService:
    return GradeService(session)


ApplicationServiceDep = Annotated[ApplicationService, Depends(get_application_service)]
StudentServiceDep = Annotated[StudentService, Depends(get_student_service)]
CourseServiceDep = Annotated[CourseService, Depends(get_course_service)]
GradeServiceDep = Annotated[GradeService, Depends(get_grade_service)]

__all__ = [
    "ApplicationServiceDep",
    "AuthServiceDep",
    "CourseServiceDep",
    "GradeServiceDep",
    "SessionDep",
    "SettingsDep",
    "RedisDep",
    "StudentServiceDep",
    "get_application_service",
    "get_auth_service",
    "get_course_service",
    "get_grade_service",
    "get_student_service",
    "get_settings",
]
