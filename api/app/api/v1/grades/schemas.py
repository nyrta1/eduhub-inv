from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class GradeCreate(BaseModel):
    student_id: uuid.UUID
    course_id: uuid.UUID
    score: Decimal = Field(ge=0, le=100, description="Numeric score 0..100.", examples=["95"])
    letter_grade: str | None = Field(default=None, max_length=8, examples=["A"])


class GradePatch(BaseModel):
    score: Decimal = Field(ge=0, le=100, examples=["88"])
    letter_grade: str | None = Field(default=None, max_length=8, examples=["B+"])
    reason: str | None = Field(
        default=None, max_length=2000, description="Reason for grade correction."
    )


class GradeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_id: uuid.UUID
    course_id: uuid.UUID
    score: Decimal
    letter_grade: str | None
    recorded_at: datetime
    created_at: datetime
    updated_at: datetime
