"""Unit tests for Pydantic schemas."""

from __future__ import annotations

import datetime
import uuid

import pytest

from fittrack.api.v1.schemas.common import ApiModel, _to_camel
from fittrack.api.v1.schemas.users import UserCreate, UserResponse, UserUpdate
from fittrack.domain.enums import Role, UserStatus


@pytest.mark.unit
class TestToCamel:
    def test_single_word_unchanged(self) -> None:
        assert _to_camel("email") == "email"

    def test_two_words(self) -> None:
        assert _to_camel("point_balance") == "pointBalance"

    def test_three_words(self) -> None:
        assert _to_camel("email_verified_at") == "emailVerifiedAt"

    def test_already_camel_passthrough(self) -> None:
        assert _to_camel("id") == "id"


@pytest.mark.unit
class TestApiModel:
    def test_camel_alias_on_serialise(self) -> None:
        class MyModel(ApiModel):
            point_balance: int

        m = MyModel(point_balance=100)
        d = m.model_dump(by_alias=True)
        assert "pointBalance" in d
        assert "point_balance" not in d

    def test_snake_case_init_still_works(self) -> None:
        class MyModel(ApiModel):
            point_balance: int

        m = MyModel(point_balance=42)
        assert m.point_balance == 42


@pytest.mark.unit
class TestUserCreate:
    def test_valid_creation(self) -> None:
        u = UserCreate(email="user@example.com", password="SecurePass1!")
        assert u.email == "user@example.com"

    def test_password_min_length(self) -> None:
        with pytest.raises(Exception):
            UserCreate(email="x@example.com", password="short")

    def test_invalid_email_rejected(self) -> None:
        with pytest.raises(Exception):
            UserCreate(email="not-an-email", password="ValidPass123!")


@pytest.mark.unit
class TestUserUpdate:
    def test_partial_update_role_only(self) -> None:
        u = UserUpdate(role=Role.ADMIN)
        assert u.role == Role.ADMIN
        assert u.status is None

    def test_partial_update_status_only(self) -> None:
        u = UserUpdate(status=UserStatus.SUSPENDED)
        assert u.status == UserStatus.SUSPENDED
        assert u.role is None


@pytest.mark.unit
class TestUserResponse:
    def test_serialises_to_camel(self) -> None:
        now = datetime.datetime.now(datetime.UTC)
        u = UserResponse(
            user_id=uuid.uuid4(),
            email="x@example.com",
            status=UserStatus.ACTIVE,
            role=Role.USER,
            point_balance=100,
            email_verified=True,
            created_at=now,
            updated_at=now,
        )
        d = u.model_dump(by_alias=True)
        assert "userId" in d
        assert "pointBalance" in d
        assert "emailVerified" in d
