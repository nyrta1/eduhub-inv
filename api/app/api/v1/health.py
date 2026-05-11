from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import RedisDep, SessionDep, SettingsDep
from app.api.docs import ERROR_RESPONSES
from app.schemas.common import HealthStatus, ReadinessReport

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "/live",
    response_model=HealthStatus,
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
    description="Process-level check used by orchestrators. Does not validate external dependencies.",
    responses={**ERROR_RESPONSES, 200: {"description": "Service is alive."}},
)
async def liveness(settings: SettingsDep) -> HealthStatus:
    return HealthStatus(status="ok", service=settings.app_name)


@router.get(
    "/ready",
    response_model=ReadinessReport,
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
    description="Dependency-level readiness check for PostgreSQL and Redis connectivity.",
    responses={
        **ERROR_RESPONSES,
        200: {"description": "All required dependencies are ready."},
        503: {"description": "At least one dependency is unavailable."},
    },
)
async def readiness(
    session: SessionDep,
    redis_client: RedisDep,
    settings: SettingsDep,
) -> ReadinessReport:
    try:
        await session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc

    try:
        ping_value = await redis_client.ping()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis unavailable",
        ) from exc

    if ping_value is not True:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis unavailable",
        )

    return ReadinessReport(
        status="ready",
        service=settings.app_name,
        database="up",
        redis="up",
    )
