from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class StudentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    student_number: str
    enrollment_status: str
    academic_group: str | None
    specialty: str | None
    enrollment_date: date | None
    academic_status: str | None
    created_at: datetime
    updated_at: datetime


class StudentProfileResponse(BaseModel):
    student: StudentRead
    gpa: Decimal = Field(
        description="Weighted GPA computed from graded courses.", examples=["3.67"]
    )


class StudentPatch(BaseModel):
    academic_group: str | None = Field(default=None, max_length=64, examples=["CS-24M"])
    specialty: str | None = Field(default=None, max_length=255, examples=["Cybersecurity"])
    enrollment_date: date | None = None
    academic_status: str | None = Field(default=None, max_length=32, examples=["GOOD_STANDING"])
    enrollment_status: str | None = Field(default=None, max_length=32, examples=["ACTIVE"])
