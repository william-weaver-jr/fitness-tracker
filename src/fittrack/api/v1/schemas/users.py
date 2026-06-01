"""Pydantic schemas for User endpoints."""

from __future__ import annotations

import datetime
import uuid

from pydantic import EmailStr, Field

from fittrack.api.v1.schemas.common import ApiModel
from fittrack.domain.enums import Role, UserStatus


class UserCreate(ApiModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserUpdate(ApiModel):
    role: Role | None = None
    status: UserStatus | None = None


class UserResponse(ApiModel):
    user_id: uuid.UUID
    email: str
    status: UserStatus
    role: Role
    point_balance: int
    email_verified: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
    last_login_at: datetime.datetime | None = None
