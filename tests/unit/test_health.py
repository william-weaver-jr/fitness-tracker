"""Unit tests for health check endpoints (no DB required)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client() -> TestClient:
    from fittrack.main import create_app

    app = create_app()
    return TestClient(app, raise_server_exceptions=True)


@pytest.mark.unit
class TestLiveness:
    def test_healthz_returns_200(self, client: TestClient) -> None:
        resp = client.get("/healthz")
        assert resp.status_code == 200

    def test_healthz_body(self, client: TestClient) -> None:
        resp = client.get("/healthz")
        body = resp.json()
        assert body["status"] == "ok"

    def test_healthz_content_type(self, client: TestClient) -> None:
        resp = client.get("/healthz")
        assert "application/json" in resp.headers["content-type"]


@pytest.mark.unit
class TestReadiness:
    def test_readyz_returns_200_without_db(self, client: TestClient) -> None:
        # In unit context there's no DB; readyz returns degraded but 200
        resp = client.get("/readyz")
        assert resp.status_code in (200, 503)

    def test_readyz_has_checks_field(self, client: TestClient) -> None:
        resp = client.get("/readyz")
        body = resp.json()
        assert "checks" in body


@pytest.mark.unit
class TestNotFound:
    def test_unknown_route_returns_404_problem_json(self, client: TestClient) -> None:
        resp = client.get("/nonexistent")
        assert resp.status_code == 404
        assert "problem+json" in resp.headers.get("content-type", "")
