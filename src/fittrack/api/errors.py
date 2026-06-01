"""RFC 7807 Problem Details for HTTP APIs (application/problem+json)."""

from __future__ import annotations

from typing import Any

from fastapi import Request
from pydantic import BaseModel, Field, field_validator
from starlette.responses import Response


class Problem(BaseModel):
    """RFC 7807 problem detail object."""

    type: str = Field(default="about:blank")
    title: str
    status: int
    detail: str | None = None
    instance: str | None = None

    @field_validator("status")
    @classmethod
    def must_be_error_status(cls, v: int) -> int:
        if v < 400:
            raise ValueError(f"Problem status must be 4xx or 5xx; got {v}")
        return v


def problem_response(
    status_code: int,
    title: str,
    detail: str | None = None,
    type_url: str = "about:blank",
    instance: str | None = None,
    extra: dict[str, Any] | None = None,
) -> Response:
    """Build an RFC 7807-compliant JSON response."""
    problem = Problem(
        type=type_url,
        title=title,
        status=status_code,
        detail=detail,
        instance=instance,
    )
    body = problem.model_dump(exclude_none=True)
    if extra:
        body.update(extra)
    return Response(
        content=__import__("orjson").dumps(body),
        status_code=status_code,
        media_type="application/problem+json",
    )


async def validation_exception_handler(request: Request, exc: Exception) -> Response:
    from fastapi.exceptions import RequestValidationError

    errors = exc.errors() if isinstance(exc, RequestValidationError) else [{"msg": str(exc)}]  # type: ignore[union-attr]
    return problem_response(
        status_code=422,
        title="Validation Error",
        detail="Request body or parameters failed validation.",
        instance=str(request.url.path),
        extra={"errors": errors},
    )


async def http_exception_handler(request: Request, exc: Exception) -> Response:
    from fastapi.exceptions import HTTPException

    if isinstance(exc, HTTPException):
        return problem_response(
            status_code=exc.status_code,
            title=exc.detail if isinstance(exc.detail, str) else "HTTP Error",
            instance=str(request.url.path),
        )
    return problem_response(status_code=500, title="Internal Server Error")
