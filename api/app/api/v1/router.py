from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import health
from app.api.v1.applications import router as applications_router
from app.api.v1.auth import router as auth_router
from app.api.v1.courses import router as courses_router
from app.api.v1.grades import router as grades_router
from app.api.v1.students import router as students_router
from app.api.v1.users import router as users_router

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(applications_router)
api_router.include_router(students_router)
api_router.include_router(courses_router)
api_router.include_router(grades_router)
