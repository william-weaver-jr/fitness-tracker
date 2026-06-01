"""Unit tests for /v1/users routes (no DB — repositories are mocked)."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client() -> TestClient:
    from fittrack.main import create_app

    return TestClient(create_app(), raise_server_exceptions=False)


def _sample_user(overrides: dict | None = None) -> dict:
    # Keys match what the DB JSON_OBJECT returns (camelCase)
    data: dict = {
        "_id": str(uuid.uuid4()),
        "email": "alice@example.com",
        "status": "active",
        "role": "user",
        "pointBalance": 250,
        "emailVerified": 1,
        "createdAt": "2026-01-01T00:00:00",
        "updatedAt": "2026-01-01T00:00:00",
    }
    if overrides:
        data.update(overrides)
    return data


@pytest.mark.unit
class TestListUsers:
    def test_returns_200_with_paginated_shape(self, client: TestClient) -> None:
        with patch(
            "fittrack.database.repositories.users_repo.list_users",
            new=AsyncMock(return_value=([], 0)),
        ):
            resp = client.get("/v1/users")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body

    def test_pagination_defaults(self, client: TestClient) -> None:
        with patch(
            "fittrack.database.repositories.users_repo.list_users",
            new=AsyncMock(return_value=([_sample_user()], 1)),
        ):
            resp = client.get("/v1/users")
        body = resp.json()
        assert body["page"] == 1
        assert body["limit"] == 20

    def test_custom_pagination(self, client: TestClient) -> None:
        with patch(
            "fittrack.database.repositories.users_repo.list_users",
            new=AsyncMock(return_value=([], 0)),
        ):
            resp = client.get("/v1/users?page=2&limit=10")
        assert resp.status_code == 200

    def test_limit_above_100_returns_422(self, client: TestClient) -> None:
        resp = client.get("/v1/users?limit=101")
        assert resp.status_code == 422


@pytest.mark.unit
class TestGetUser:
    def test_returns_404_for_unknown_user(self, client: TestClient) -> None:
        uid = str(uuid.uuid4())
        with patch(
            "fittrack.database.repositories.users_repo.get_user",
            new=AsyncMock(return_value=None),
        ):
            resp = client.get(f"/v1/users/{uid}")
        assert resp.status_code == 404
        assert "problem+json" in resp.headers.get("content-type", "")

    def test_returns_user_when_found(self, client: TestClient) -> None:
        user = _sample_user()
        uid = str(uuid.uuid4())
        with patch(
            "fittrack.database.repositories.users_repo.get_user",
            new=AsyncMock(return_value=user),
        ):
            resp = client.get(f"/v1/users/{uid}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == "alice@example.com"

    def test_returns_camel_case_keys(self, client: TestClient) -> None:
        user = _sample_user()
        uid = str(uuid.uuid4())
        with patch(
            "fittrack.database.repositories.users_repo.get_user",
            new=AsyncMock(return_value=user),
        ):
            resp = client.get(f"/v1/users/{uid}")
        body = resp.json()
        assert "pointBalance" in body
        assert "emailVerified" in body
        assert "point_balance" not in body


@pytest.mark.unit
class TestDeleteUser:
    def test_returns_204_on_success(self, client: TestClient) -> None:
        uid = str(uuid.uuid4())
        with patch(
            "fittrack.database.repositories.users_repo.delete_user",
            new=AsyncMock(return_value=True),
        ):
            resp = client.delete(f"/v1/users/{uid}")
        assert resp.status_code == 204

    def test_returns_404_when_not_found(self, client: TestClient) -> None:
        uid = str(uuid.uuid4())
        with patch(
            "fittrack.database.repositories.users_repo.delete_user",
            new=AsyncMock(return_value=False),
        ):
            resp = client.delete(f"/v1/users/{uid}")
        assert resp.status_code == 404
