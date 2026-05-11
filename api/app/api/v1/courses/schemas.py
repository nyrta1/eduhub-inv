from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CourseCreate(BaseModel):
    code: str = Field(min_length=1, max_length=32, examples=["CS601"])
    title: str = Field(min_length=1, max_length=255, examples=["Secure Software Engineering"])
    description: str | None = Field(default=None, max_length=8000)
    credits: Decimal = Field(gt=0, le=100, examples=["5.0"])
    teacher_id: uuid.UUID

    @field_validator("code", "title")
    @classmethod
    def strip_nonempty(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Must not be blank.")
        return s


class CoursePatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=8000)
    credits: Decimal | None = Field(default=None, gt=0, le=100)
    teacher_id: uuid.UUID | None = None


class TeacherBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_id: str
    department: str | None


class CourseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    title: str
    description: str | None
    credits: Decimal
    teacher_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    teacher: TeacherBrief | None = None


class CourseStudentEnroll(BaseModel):
    student_id: uuid.UUID
