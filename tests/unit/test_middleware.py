"""Unit tests for custom ASGI middleware."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client() -> TestClient:
    from fittrack.main import create_app

    app = create_app()
    return TestClient(app, raise_server_exceptions=True)


@pytest.mark.unit
class TestRequestIdMiddleware:
    def test_response_has_x_request_id(self, client: TestClient) -> None:
        resp = client.get("/healthz")
        assert "x-request-id" in resp.headers

    def test_request_id_is_uuid_like(self, client: TestClient) -> None:
        import re

        resp = client.get("/healthz")
        rid = resp.headers["x-request-id"]
        assert re.match(r"[0-9a-f-]{32,36}", rid), f"Not a UUID: {rid}"

    def test_client_supplied_request_id_echoed(self, client: TestClient) -> None:
        custom_id = "my-trace-id-1234"
        resp = client.get("/healthz", headers={"X-Request-Id": custom_id})
        assert resp.headers["x-request-id"] == custom_id


@pytest.mark.unit
class TestSecurityHeaders:
    def test_x_content_type_options(self, client: TestClient) -> None:
        resp = client.get("/healthz")
        assert resp.headers.get("x-content-type-options") == "nosniff"

    def test_x_frame_options(self, client: TestClient) -> None:
        resp = client.get("/healthz")
        assert resp.headers.get("x-frame-options") == "DENY"

    def test_referrer_policy(self, client: TestClient) -> None:
        resp = client.get("/healthz")
        assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
