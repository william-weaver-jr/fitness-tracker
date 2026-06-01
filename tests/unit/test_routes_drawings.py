"""Unit tests for /v1/drawings routes."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client() -> TestClient:
    from fittrack.main import create_app

    return TestClient(create_app(), raise_server_exceptions=False)


REPO = "fittrack.database.repositories.drawings_repo"


def _sample_drawing(**overrides) -> dict:
    data = {
        "_id": str(uuid.uuid4()),
        "drawingType": "daily",
        "name": "Daily Drawing #1",
        "ticketCostPoints": 100,
        "status": "open",
        "totalTickets": 42,
    }
    data.update(overrides)
    return data


@pytest.mark.unit
class TestListDrawings:
    def test_returns_200(self, client: TestClient) -> None:
        with patch(f"{REPO}.list_drawings", new=AsyncMock(return_value=([_sample_drawing()], 1))):
            resp = client.get("/v1/drawings")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1

    def test_status_filter_passed(self, client: TestClient) -> None:
        with patch(f"{REPO}.list_drawings", new=AsyncMock(return_value=([], 0))) as mock:
            client.get("/v1/drawings?status=open")
        mock.assert_called_once()
        assert mock.call_args.args[0] == "open"

    def test_limit_above_100_rejected(self, client: TestClient) -> None:
        resp = client.get("/v1/drawings?limit=200")
        assert resp.status_code == 422


@pytest.mark.unit
class TestGetDrawing:
    def test_found(self, client: TestClient) -> None:
        d = _sample_drawing()
        uid = str(uuid.uuid4())
        with patch(f"{REPO}.get_drawing", new=AsyncMock(return_value=d)):
            resp = client.get(f"/v1/drawings/{uid}")
        assert resp.status_code == 200

    def test_not_found(self, client: TestClient) -> None:
        uid = str(uuid.uuid4())
        with patch(f"{REPO}.get_drawing", new=AsyncMock(return_value=None)):
            resp = client.get(f"/v1/drawings/{uid}")
        assert resp.status_code == 404


@pytest.mark.unit
class TestCreateDrawing:
    def test_returns_201(self, client: TestClient) -> None:
        d = _sample_drawing()
        with patch(f"{REPO}.create_drawing", new=AsyncMock(return_value=d)):
            resp = client.post("/v1/drawings", json={
                "drawingType": "daily",
                "name": "Test Drawing",
                "ticketCostPoints": 100,
                "drawingTime": "2026-07-01T12:00:00",
                "ticketSalesClose": "2026-07-01T11:00:00",
            })
        assert resp.status_code == 201
