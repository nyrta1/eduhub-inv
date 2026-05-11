from __future__ import annotations

from pydantic import BaseModel, Field


class HealthStatus(BaseModel):
    status: str = Field(min_length=1, examples=["ok"])
    service: str = Field(min_length=1)


class ReadinessReport(BaseModel):
    status: str = Field(min_length=1, examples=["ready"])
    service: str = Field(min_length=1)
    database: str = Field(min_length=1, examples=["up"])
    redis: str = Field(min_length=1, examples=["up"])
