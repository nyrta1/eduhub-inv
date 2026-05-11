from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.enums import ApplicationStatus
from app.security.validators import SAFE_CODE_PATTERN


class ApplicationCreate(BaseModel):
    program_code: str = Field(
        min_length=1,
        max_length=64,
        pattern=SAFE_CODE_PATTERN.pattern,
        description="Program identifier (safe code format).",
        examples=["CS-MSC"],
    )
    intake_term: str = Field(
        min_length=1,
        max_length=32,
        pattern=SAFE_CODE_PATTERN.pattern,
        description="Academic intake term identifier.",
        examples=["2026-FALL"],
    )
    statement: str | None = Field(
        default=None, max_length=10_000, description="Applicant statement of purpose."
    )

    @field_validator("program_code", "intake_term")
    @classmethod
    def strip_nonempty(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Must not be blank.")
        return s


class ApplicationStatusPatch(BaseModel):
    status: ApplicationStatus = Field(description="Review outcome status.")
    notes: str | None = Field(
        default=None, max_length=4000, description="Reviewer notes for decision traceability."
    )


class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    applicant_user_id: uuid.UUID
    status: str
    program_code: str
    intake_term: str
    statement: str | None
    reviewed_by_user_id: uuid.UUID | None
    reviewed_at: datetime | None
    decision_notes: str | None
    resulting_student_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
