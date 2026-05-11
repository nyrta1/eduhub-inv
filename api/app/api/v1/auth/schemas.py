from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr, Field

from app.auth.permissions import RoleName


class RegisterRequest(BaseModel):
    email: EmailStr = Field(
        description="Institutional email address.", examples=["student.nur@example.edu"]
    )
    password: str = Field(
        min_length=1, description="Plain password; policy is enforced server-side."
    )
    full_name: str = Field(min_length=1, max_length=255, examples=["Aruzhan Nurgaliyeva"])


class LoginRequest(BaseModel):
    email: EmailStr = Field(examples=["dean.seed@university.edu"])
    password: str = Field(min_length=1, examples=["SeedPassword123!"])


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=10, description="JWT refresh token from `/auth/login`.")


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(
        min_length=1, description="New password must satisfy policy and history constraints."
    )


class TokenResponse(BaseModel):
    access_token: str = Field(description="Use this value with `Bearer` auth in Swagger.")
    refresh_token: str = Field(
        description="Used only with `/auth/refresh`; rotate and store securely."
    )
    token_type: str = Field(default="bearer", examples=["bearer"])
    expires_in: int = Field(description="Access token validity in seconds.", examples=[900])


class UserPublic(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    roles: list[str]


class RegisterResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    roles: list[str]


class MessageResponse(BaseModel):
    status: str = Field(default="ok", examples=["ok"])


class AdminRoleUpdate(BaseModel):
    role: RoleName
