"""Unit tests for activities, tickets, prizes, fulfillments, point_transactions, profiles, connections routes."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client() -> TestClient:
    from fittrack.main import create_app

    return TestClient(create_app(), raise_server_exceptions=False)


# ── Activities ─────────────────────────────────────────────────────────────────
ACT_REPO = "fittrack.database.repositories.activities_repo"


@pytest.mark.unit
class TestActivitiesRoutes:
    def test_list_returns_200(self, client: TestClient) -> None:
        with patch(f"{ACT_REPO}.list_activities", new=AsyncMock(return_value=([], 0))):
            resp = client.get("/v1/activities")
        assert resp.status_code == 200

    def test_get_not_found(self, client: TestClient) -> None:
        with patch(f"{ACT_REPO}.get_activity", new=AsyncMock(return_value=None)):
            resp = client.get(f"/v1/activities/{uuid.uuid4()}")
        assert resp.status_code == 404

    def test_get_found(self, client: TestClient) -> None:
        data = {"_id": str(uuid.uuid4()), "activityType": "running"}
        with patch(f"{ACT_REPO}.get_activity", new=AsyncMock(return_value=data)):
            resp = client.get(f"/v1/activities/{uuid.uuid4()}")
        assert resp.status_code == 200


# ── Tickets ───────────────────────────────────────────────────────────────────
TKT_REPO = "fittrack.database.repositories.tickets_repo"


@pytest.mark.unit
class TestTicketsRoutes:
    def test_list_returns_200(self, client: TestClient) -> None:
        with patch(f"{TKT_REPO}.list_tickets", new=AsyncMock(return_value=([], 0))):
            resp = client.get("/v1/tickets")
        assert resp.status_code == 200

    def test_get_not_found(self, client: TestClient) -> None:
        with patch(f"{TKT_REPO}.get_ticket", new=AsyncMock(return_value=None)):
            resp = client.get(f"/v1/tickets/{uuid.uuid4()}")
        assert resp.status_code == 404


# ── Prizes ────────────────────────────────────────────────────────────────────
PRZ_REPO = "fittrack.database.repositories.prizes_repo"


@pytest.mark.unit
class TestPrizesRoutes:
    def test_list_by_drawing(self, client: TestClient) -> None:
        did = uuid.uuid4()
        with patch(f"{PRZ_REPO}.list_prizes", new=AsyncMock(return_value=([], 0))):
            resp = client.get(f"/v1/drawings/{did}/prizes")
        assert resp.status_code == 200

    def test_get_not_found(self, client: TestClient) -> None:
        with patch(f"{PRZ_REPO}.get_prize", new=AsyncMock(return_value=None)):
            resp = client.get(f"/v1/prizes/{uuid.uuid4()}")
        assert resp.status_code == 404


# ── Fulfillments ──────────────────────────────────────────────────────────────
FUL_REPO = "fittrack.database.repositories.fulfillments_repo"


@pytest.mark.unit
class TestFulfillmentsRoutes:
    def test_list_returns_200(self, client: TestClient) -> None:
        with patch(f"{FUL_REPO}.list_fulfillments", new=AsyncMock(return_value=([], 0))):
            resp = client.get("/v1/fulfillments")
        assert resp.status_code == 200

    def test_get_not_found(self, client: TestClient) -> None:
        with patch(f"{FUL_REPO}.get_fulfillment", new=AsyncMock(return_value=None)):
            resp = client.get(f"/v1/fulfillments/{uuid.uuid4()}")
        assert resp.status_code == 404


# ── Point Transactions ────────────────────────────────────────────────────────
TXN_REPO = "fittrack.database.repositories.point_transactions_repo"


@pytest.mark.unit
class TestTransactionRoutes:
    def test_list_returns_200(self, client: TestClient) -> None:
        with patch(f"{TXN_REPO}.list_transactions", new=AsyncMock(return_value=([], 0))):
            resp = client.get("/v1/point-transactions")
        assert resp.status_code == 200

    def test_get_not_found(self, client: TestClient) -> None:
        with patch(f"{TXN_REPO}.get_transaction", new=AsyncMock(return_value=None)):
            resp = client.get(f"/v1/point-transactions/{uuid.uuid4()}")
        assert resp.status_code == 404


# ── Profiles ──────────────────────────────────────────────────────────────────
PRF_REPO = "fittrack.database.repositories.profiles_repo"


@pytest.mark.unit
class TestProfileRoutes:
    def test_get_not_found(self, client: TestClient) -> None:
        with patch(f"{PRF_REPO}.get_profile", new=AsyncMock(return_value=None)):
            resp = client.get(f"/v1/users/{uuid.uuid4()}/profile")
        assert resp.status_code == 404

    def test_get_found(self, client: TestClient) -> None:
        data = {"_id": str(uuid.uuid4()), "displayName": "Alice", "tierCode": "F-30-39-INT"}
        with patch(f"{PRF_REPO}.get_profile", new=AsyncMock(return_value=data)):
            resp = client.get(f"/v1/users/{uuid.uuid4()}/profile")
        assert resp.status_code == 200


# ── Connections ───────────────────────────────────────────────────────────────
CON_REPO = "fittrack.database.repositories.connections_repo"


@pytest.mark.unit
class TestConnectionRoutes:
    def test_list_returns_200(self, client: TestClient) -> None:
        with patch(f"{CON_REPO}.list_connections", new=AsyncMock(return_value=[])):
            resp = client.get(f"/v1/users/{uuid.uuid4()}/connections")
        assert resp.status_code == 200

    def test_delete_not_found(self, client: TestClient) -> None:
        with patch(f"{CON_REPO}.delete_connection", new=AsyncMock(return_value=False)):
            resp = client.delete(f"/v1/connections/{uuid.uuid4()}")
        assert resp.status_code == 404
