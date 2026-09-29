"""Pydantic request/response models for auth & users."""
from __future__ import annotations

import re
import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

ROLE_PATTERN = r"^(ADMIN|ENGINEER|REVIEWER|VIEWER)$"


def _password_policy(v: str) -> str:
    if not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
        raise ValueError("Password must contain at least one letter and one digit")
    return v


# ------------------------------------------------------------------- responses
class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    full_name: str
    email: str
    role: str
    is_active: bool
    must_change_password: bool


class TokenResponse(BaseModel):
    """Login response: access token + user + forced-password-change flag."""
    access_token: str
    token_type: str = "bearer"
    must_change_password: bool
    user: UserOut


class AccessTokenResponse(BaseModel):
    """Refresh response: only a new access token (refresh stays in the cookie)."""
    access_token: str
    token_type: str = "bearer"


# -------------------------------------------------------------------- requests
class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=8, max_length=128)

    _policy = field_validator("new_password")(_password_policy)


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$")
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(pattern=ROLE_PATTERN)

    _policy = field_validator("password")(_password_policy)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    role: str | None = Field(default=None, pattern=ROLE_PATTERN)
    is_active: bool | None = None
    new_password: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def policy(cls, v: str | None) -> str | None:
        return None if v is None else _password_policy(v)