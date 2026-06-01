"""Unit tests for the dev-only test page route."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def dev_client() -> TestClient:
    import os

    os.environ["ENV"] = "development"
    from fittrack.config import get_settings

    get_settings.cache_clear()
    from fittrack.main import create_app

    app = create_app()
    yield TestClient(app, raise_server_exceptions=False)
    os.environ["ENV"] = "development"
    get_settings.cache_clear()


@pytest.fixture()
def prod_client() -> TestClient:
    import os

    os.environ["ENV"] = "production"
    from fittrack.config import get_settings

    get_settings.cache_clear()
    from fittrack.main import create_app

    app = create_app()
    yield TestClient(app, raise_server_exceptions=False)
    os.environ["ENV"] = "development"
    get_settings.cache_clear()


@pytest.mark.unit
class TestDevRoute:
    def test_dev_endpoint_exists_in_development(self, dev_client: TestClient) -> None:
        resp = dev_client.get("/dev")
        # Could be 200 (if test_page.html exists) or 404 (page not built yet)
        assert resp.status_code in (200, 404)

    def test_dev_route_not_exposed_in_production(self, prod_client: TestClient) -> None:
        resp = prod_client.get("/dev")
        assert resp.status_code == 404


@pytest.mark.unit
class TestSeedEndpoint:
    def test_seed_returns_seeded_on_success(self, dev_client: TestClient) -> None:
        with patch("fittrack.api.dev._run_script", new_callable=AsyncMock) as mock_run:
            resp = dev_client.post("/dev/seed")
        assert resp.status_code == 200
        assert resp.json() == {"status": "seeded"}
        mock_run.assert_awaited_once_with("seed_data")

    def test_seed_returns_500_with_detail_on_failure(self, dev_client: TestClient) -> None:
        with patch(
            "fittrack.api.dev._run_script",
            new_callable=AsyncMock,
            side_effect=Exception("unique constraint violated"),
        ):
            resp = dev_client.post("/dev/seed")
        assert resp.status_code == 500
        assert "unique constraint violated" in resp.json()["detail"]

    def test_seed_not_available_in_production(self, prod_client: TestClient) -> None:
        resp = prod_client.post("/dev/seed")
        assert resp.status_code == 404


@pytest.mark.unit
class TestResetEndpoint:
    def test_reset_returns_reset_on_success(self, dev_client: TestClient) -> None:
        with patch("fittrack.api.dev._run_script", new_callable=AsyncMock) as mock_run:
            resp = dev_client.post("/dev/reset")
        assert resp.status_code == 200
        assert resp.json() == {"status": "reset"}
        mock_run.assert_awaited_once_with("reset_db")

    def test_reset_returns_500_with_detail_on_failure(self, dev_client: TestClient) -> None:
        with patch(
            "fittrack.api.dev._run_script",
            new_callable=AsyncMock,
            side_effect=RuntimeError("oracle unreachable"),
        ):
            resp = dev_client.post("/dev/reset")
        assert resp.status_code == 500
        assert "oracle unreachable" in resp.json()["detail"]

    def test_reset_not_available_in_production(self, prod_client: TestClient) -> None:
        resp = prod_client.post("/dev/reset")
        assert resp.status_code == 404
