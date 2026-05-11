"""RBAC matrix checks (role → permission) without a database."""

from __future__ import annotations

import uuid
from types import SimpleNamespace

from app.auth.permissions import Permission, user_has_permission


def _user(*role_names: str) -> SimpleNamespace:
    return SimpleNamespace(id=uuid.uuid4(), roles=[SimpleNamespace(name=n) for n in role_names])


def test_student_can_read_own_grades_only_scope() -> None:
    u = _user("STUDENT")
    assert user_has_permission(u, Permission.ACADEMIC_GRADE_READ_SELF)
    assert not user_has_permission(u, Permission.ACADEMIC_GRADE_READ_ANY)
    assert not user_has_permission(u, Permission.ACADEMIC_GRADE_WRITE_ASSIGNED)


def test_teacher_can_write_assigned_but_not_read_all_grades() -> None:
    u = _user("TEACHER")
    assert user_has_permission(u, Permission.ACADEMIC_GRADE_WRITE_ASSIGNED)
    assert not user_has_permission(u, Permission.ACADEMIC_GRADE_READ_ANY)
    assert user_has_permission(u, Permission.ACADEMIC_STUDENT_READ_ROSTER)


def test_dean_can_review_applications_and_read_all_academic() -> None:
    u = _user("DEAN")
    assert user_has_permission(u, Permission.ACADEMIC_APPLICATION_REVIEW)
    assert user_has_permission(u, Permission.ACADEMIC_APPLICATION_READ_ANY)
    assert user_has_permission(u, Permission.ACADEMIC_GRADE_READ_ANY)


def test_admin_has_full_permission_union() -> None:
    u = _user("ADMIN")
    assert user_has_permission(u, Permission.USERS_ROLE_ASSIGN)
    assert user_has_permission(u, Permission.ACADEMIC_COURSE_MANAGE)
