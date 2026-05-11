from __future__ import annotations

import pytest
from app.api.v1.applications.schemas import ApplicationCreate
from pydantic import ValidationError


def test_application_create_rejects_invalid_program_code_pattern() -> None:
    with pytest.raises(ValidationError):
        ApplicationCreate(program_code="bad;drop", intake_term="2025-A", statement=None)


def test_application_create_accepts_safe_codes() -> None:
    m = ApplicationCreate(program_code="CS101", intake_term="2025-F1", statement="Hi")
    assert m.program_code == "CS101"
