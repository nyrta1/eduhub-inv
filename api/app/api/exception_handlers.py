from __future__ import annotations

import uuid
from typing import Any

import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import Settings, get_settings


def _request_id() -> str | None:
    ctx = structlog.contextvars.get_contextvars()
    rid = ctx.get("request_id")
    return str(rid) if rid else None


def register_exception_handlers(app: FastAPI) -> None:
    """Attach global exception handlers to the FastAPI application."""
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    settings: Settings = get_settings()
    logger = structlog.get_logger("api.validation")
    rid = _request_id()
    logger.warning(
        "validation.failed",
        error_count=len(exc.errors()),
        path=request.url.path,
        request_id=rid,
    )

    if settings.app_debug:
        body: dict[str, Any] = {
            "error": {
                "code": "validation_error",
                "message": "Request validation failed",
                "request_id": rid,
                "fields": exc.errors(),
            }
        }
    else:
        body = {
            "error": {
                "code": "validation_error",
                "message": "Request validation failed",
                "request_id": rid,
            }
        }

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=body,
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    rid = _request_id()
    if isinstance(exc.detail, dict):
        payload: dict[str, Any] = {"detail": exc.detail}
    else:
        payload = {"detail": str(exc.detail)}
    payload["request_id"] = rid
    return JSONResponse(status_code=exc.status_code, content=payload)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    settings: Settings = get_settings()
    logger = structlog.get_logger("api.errors")
    reference_id = str(uuid.uuid4())
    rid = _request_id()
    logger.exception(
        "unhandled.exception",
        reference_id=reference_id,
        request_id=rid,
        path=request.url.path,
        method=request.method,
        exc_type=type(exc).__name__,
    )
    if settings.app_debug:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "Unexpected server error",
                    "reference_id": reference_id,
                    "request_id": rid,
                    "debug_type": type(exc).__name__,
                }
            },
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "internal_error",
                "message": "Unexpected server error",
                "reference_id": reference_id,
                "request_id": rid,
            }
        },
    )
