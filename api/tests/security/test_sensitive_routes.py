from __future__ import annotations

from app.core.config import Settings
from app.security.sensitive_routes import classify_sensitive_route


def _settings() -> Settings:
    return Settings(
        app_secret_key="x" * 32,
        database_url="postgresql+asyncpg://u:p@localhost/db",
        redis_url="redis://localhost:6379/0",
    )


def test_classify_application_submit() -> None:
    s = _settings()
    r = classify_sensitive_route("POST", "/api/v1/applications", s)
    assert r is not None
    assert r.bucket == "application_submit"


def test_classify_grade_patch() -> None:
    s = _settings()
    rid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    r = classify_sensitive_route("PATCH", f"/api/v1/grades/{rid}", s)
    assert r is not None
    assert r.bucket == "grade_update"


def test_classify_no_match_health() -> None:
    s = _settings()
    assert classify_sensitive_route("GET", "/api/v1/health/live", s) is None
