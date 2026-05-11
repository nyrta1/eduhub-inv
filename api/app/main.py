from __future__ import annotations

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

import app.metrics.security_metrics  # noqa: F401 — register Prometheus counters
from app.api.exception_handlers import register_exception_handlers
from app.api.openapi import OPENAPI_TAGS, install_openapi
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.lifespan import lifespan
from app.metrics.prometheus import configure_metrics
from app.middleware.api_route_rate_limit import SensitiveRouteRateLimitMiddleware
from app.middleware.body_limit import MaxRequestBodySizeMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.request_logging import AccessLoggingMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.security_observability import SecurityObservabilityMiddleware


def create_application() -> FastAPI:
    settings = get_settings()

    expose_docs = settings.expose_api_documentation()
    application = FastAPI(
        title="Student Platform API Portal",
        version="1.0.0",
        summary="Secure academic platform API",
        swagger_ui_parameters={
            "persistAuthorization": True,
            "displayRequestDuration": True,
            "docExpansion": "list",
            "filter": True,
            "tryItOutEnabled": True,
            "syntaxHighlight.theme": "obsidian",
        },
        swagger_ui_init_oauth={"usePkceWithAuthorizationCodeGrant": False},
        openapi_url="/api/v1/openapi.json" if expose_docs else None,
        docs_url="/api/v1/docs" if expose_docs else None,
        redoc_url="/api/v1/redoc" if expose_docs else None,
        openapi_tags=OPENAPI_TAGS,
        lifespan=lifespan,
    )

    register_exception_handlers(application)

    configure_metrics(
        application,
        metrics_path=settings.metrics_path,
        enabled=settings.metrics_enabled,
    )
    install_openapi(application, settings)

    application.include_router(api_router, prefix="/api/v1")

    application.add_middleware(RequestIdMiddleware)
    application.add_middleware(
        MaxRequestBodySizeMiddleware,
        max_body_bytes=settings.request_max_body_bytes,
    )
    application.add_middleware(SensitiveRouteRateLimitMiddleware)
    application.add_middleware(AccessLoggingMiddleware)
    application.add_middleware(SecurityObservabilityMiddleware)

    if settings.parsed_cors_origins():
        application.add_middleware(
            CORSMiddleware,
            allow_origins=settings.parsed_cors_origins(),
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
            expose_headers=["X-Request-ID"],
        )

    application.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.parsed_allowed_hosts(),
    )

    application.add_middleware(SecurityHeadersMiddleware)

    return application


app = create_application()
