"""Unit tests for RFC 7807 error responses."""

from __future__ import annotations

import pytest
from fastapi import status

from fittrack.api.errors import Problem, problem_response


@pytest.mark.unit
class TestProblem:
    def test_minimal_construction(self) -> None:
        p = Problem(title="Not Found", status=404)
        assert p.title == "Not Found"
        assert p.status == 404
        assert p.type == "about:blank"
        assert p.detail is None
        assert p.instance is None

    def test_full_construction(self) -> None:
        p = Problem(
            type="https://fittrack.example/errors/not-found",
            title="Resource Not Found",
            status=404,
            detail="User with id=abc not found",
            instance="/users/abc",
        )
        assert p.type == "https://fittrack.example/errors/not-found"
        assert p.detail == "User with id=abc not found"
        assert p.instance == "/users/abc"

    def test_status_must_be_4xx_or_5xx(self) -> None:
        with pytest.raises(Exception):
            Problem(title="Bad", status=200)

        with pytest.raises(Exception):
            Problem(title="Bad", status=301)

    def test_serializes_to_dict(self) -> None:
        p = Problem(title="Not Found", status=404, detail="Missing resource")
        d = p.model_dump(exclude_none=True)
        assert d["title"] == "Not Found"
        assert d["status"] == 404
        assert d["detail"] == "Missing resource"
        assert "type" in d


@pytest.mark.unit
class TestProblemResponse:
    def test_returns_json_response_with_correct_media_type(self) -> None:
        resp = problem_response(
            status_code=status.HTTP_404_NOT_FOUND,
            title="Not Found",
            detail="The requested resource was not found.",
        )
        assert resp.status_code == 404
        assert resp.media_type == "application/problem+json"

    def test_body_is_valid_problem(self) -> None:
        import json

        resp = problem_response(
            status_code=422,
            title="Validation Error",
            detail="Field 'email' is required.",
        )
        body = json.loads(resp.body)
        assert body["status"] == 422
        assert body["title"] == "Validation Error"
        assert body["detail"] == "Field 'email' is required."
