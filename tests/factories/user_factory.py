"""Factory for User entities."""

from __future__ import annotations

import uuid
from typing import Any

from tests.factories.base import get_faker


def make_user(**overrides: Any) -> dict[str, Any]:
    fake = get_faker()
    data: dict[str, Any] = {
        "user_id": str(uuid.uuid4()),
        "email": fake.unique.email(),
        "password_hash": "$argon2id$v=19$m=65536,t=3,p=4$fakehash",
        "email_verified": 1,
        "status": "active",
        "role": "user",
        "point_balance": fake.random_int(min=0, max=10000),
        "version": 1,
    }
    data.update(overrides)
    return data


def make_admin_user(**overrides: Any) -> dict[str, Any]:
    return make_user(role="admin", **overrides)


def make_premium_user(**overrides: Any) -> dict[str, Any]:
    return make_user(role="premium", **overrides)
