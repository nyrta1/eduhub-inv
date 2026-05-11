from __future__ import annotations

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.core.config import Settings

OPENAPI_TAGS: list[dict[str, str]] = [
    {
        "name": "Authentication",
        "description": "JWT access/refresh lifecycle. Rate limited and audit logged. Roles: public for register/login, authenticated for profile/session actions.",
    },
    {
        "name": "Users",
        "description": "Administrative user-role management. Roles: ADMIN. Security: RBAC + audit trails for privileged changes.",
    },
    {
        "name": "Applications",
        "description": "Enrollment application workflows. Roles: STUDENT submit, DEAN/ADMIN review/read-any. Ownership checks enforced.",
    },
    {
        "name": "Students",
        "description": "Student profile and roster operations. Roles vary by endpoint; self-read/update is separated from broad read/update privileges.",
    },
    {
        "name": "Courses",
        "description": "Course lifecycle and enrollment operations. Roles: DEAN/ADMIN for course management; TEACHER/DEAN/ADMIN based on permissions.",
    },
    {
        "name": "Grades",
        "description": "Grade write/read with strict ownership rules. Teachers may modify grades only for assigned courses; DEAN/ADMIN can manage globally.",
    },
    {
        "name": "Security",
        "description": "Platform-level controls: JWT validation, refresh rotation, RBAC, anti-abuse rate limits, and audit logging (cross-cutting).",
    },
    {
        "name": "Monitoring",
        "description": "Operational observability via Prometheus metrics, Grafana dashboards, and ELK log pipelines.",
    },
    {
        "name": "Health",
        "description": "Liveness/readiness probes for orchestrators and runtime checks.",
    },
]


def install_openapi(app: FastAPI, settings: Settings) -> None:
    def custom_openapi() -> dict[str, object]:
        if app.openapi_schema:
            return app.openapi_schema

        schema = get_openapi(
            title="Student Platform API Portal",
            version="1.0.0",
            description=(
                "Secure university academic platform API.\n\n"
                "Includes JWT auth with refresh rotation, RBAC, audit logging, security middleware, "
                "OWASP-oriented protections, and observability integration.\n\n"
                "Secure SDLC notes:\n"
                "- Access control enforced at dependency + service layers.\n"
                "- Sensitive endpoints are rate-limited and security-audited.\n"
                "- Error payloads are sanitized and include request correlation IDs.\n"
            ),
            routes=app.routes,
            tags=OPENAPI_TAGS,
            servers=[
                {"url": "http://localhost:8000", "description": "Local Docker environment"},
                {"url": "/", "description": f"Current environment ({settings.app_env})"},
            ],
        )

        schema["info"]["contact"] = {
            "name": "Platform Engineering",
            "email": "platform@example.edu",
        }
        schema["info"]["license"] = {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        }
        schema["info"]["x-logo"] = {
            "url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png",
            "altText": "Student Platform API",
        }

        components = schema.setdefault("components", {})
        security_schemes = components.setdefault("securitySchemes", {})
        security_schemes["BearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Paste access token from `/api/v1/auth/login` response.",
        }

        for path, path_item in schema.get("paths", {}).items():
            for method, operation in path_item.items():
                if method not in {"get", "post", "put", "patch", "delete"}:
                    continue
                if path == settings.metrics_path:
                    operation.setdefault("tags", ["Monitoring"])
                    operation.setdefault("summary", "Prometheus metrics scrape endpoint")
                    operation.setdefault(
                        "description",
                        "Machine-oriented metrics endpoint for Prometheus. Intended for internal monitoring networks.",
                    )
                if path.startswith("/api/v1/health") or path in {
                    "/api/v1/auth/login",
                    "/api/v1/auth/register",
                    "/api/v1/auth/refresh",
                }:
                    continue
                operation.setdefault("security", [{"BearerAuth": []}])

        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi
