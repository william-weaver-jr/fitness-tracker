"""Unit tests for /v1/sponsors routes."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client() -> TestClient:
    from fittrack.main import create_app

    return TestClient(create_app(), raise_server_exceptions=False)


def _sample_sponsor(**overrides) -> dict:
    data = {
        "_id": str(uuid.uuid4()),
        "name": "FitGear Pro",
        "contactEmail": "contact@fitgear.com",
        "websiteUrl": "https://fitgear.com",
        "status": "active",
    }
    data.update(overrides)
    return data


REPO = "fittrack.database.repositories.sponsors_repo"


@pytest.mark.unit
class TestListSponsors:
    def test_returns_200_with_items(self, client: TestClient) -> None:
        with patch(f"{REPO}.list_sponsors", new=AsyncMock(return_value=([_sample_sponsor()], 1))):
            resp = client.get("/v1/sponsors")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_limit_above_100_rejected(self, client: TestClient) -> None:
        resp = client.get("/v1/sponsors?limit=101")
        assert resp.status_code == 422


@pytest.mark.unit
class TestGetSponsor:
    def test_found(self, client: TestClient) -> None:
        s = _sample_sponsor()
        uid = str(uuid.uuid4())
        with patch(f"{REPO}.get_sponsor", new=AsyncMock(return_value=s)):
            resp = client.get(f"/v1/sponsors/{uid}")
        assert resp.status_code == 200

    def test_not_found(self, client: TestClient) -> None:
        uid = str(uuid.uuid4())
        with patch(f"{REPO}.get_sponsor", new=AsyncMock(return_value=None)):
            resp = client.get(f"/v1/sponsors/{uid}")
        assert resp.status_code == 404
        assert "problem+json" in resp.headers.get("content-type", "")


@pytest.mark.unit
class TestCreateSponsor:
    def test_returns_201(self, client: TestClient) -> None:
        s = _sample_sponsor()
        with patch(f"{REPO}.create_sponsor", new=AsyncMock(return_value=s)):
            resp = client.post("/v1/sponsors", json={"name": "NewCo"})
        assert resp.status_code == 201


@pytest.mark.unit
class TestDeleteSponsor:
    def test_returns_204(self, client: TestClient) -> None:
        uid = str(uuid.uuid4())
        with patch(f"{REPO}.delete_sponsor", new=AsyncMock(return_value=True)):
            resp = client.delete(f"/v1/sponsors/{uid}")
        assert resp.status_code == 204

    def test_returns_404(self, client: TestClient) -> None:
        uid = str(uuid.uuid4())
        with patch(f"{REPO}.delete_sponsor", new=AsyncMock(return_value=False)):
            resp = client.delete(f"/v1/sponsors/{uid}")
        assert resp.status_code == 404
