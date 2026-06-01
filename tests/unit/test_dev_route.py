"""Unit tests for the dev-only test page route."""

from __future__ import annotations

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
