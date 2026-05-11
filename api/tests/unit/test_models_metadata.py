from __future__ import annotations

import app.models  # noqa: F401 — register all tables on Base.metadata
from app.db.base import Base
from app.models import (
    AuditLog,
    Course,
    Grade,
    Role,
    Student,
    Teacher,
    User,
)


def test_models_registered_on_metadata() -> None:
    tables = Base.metadata.tables
    expected = {
        "users",
        "roles",
        "user_roles",
        "students",
        "teachers",
        "courses",
        "grades",
        "audit_logs",
        "enrollment_applications",
        "course_enrollments",
        "grade_histories",
    }
    assert expected.issubset(set(tables.keys()))


def test_declarative_types() -> None:
    assert issubclass(User, Base)
    assert issubclass(Role, Base)
    assert issubclass(Student, Base)
    assert issubclass(Teacher, Base)
    assert issubclass(Course, Base)
    assert issubclass(Grade, Base)
    assert issubclass(AuditLog, Base)


def test_table_names() -> None:
    assert User.__tablename__ == "users"
    assert AuditLog.__tablename__ == "audit_logs"
