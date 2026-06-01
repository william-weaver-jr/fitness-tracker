"""Tracker connection routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response

from fittrack.api.errors import problem_response
from fittrack.database.repositories import connections_repo

router = APIRouter(prefix="/v1/users", tags=["connections"])


@router.get("/{user_id}/connections", response_model=None)
async def list_connections(user_id: uuid.UUID) -> JSONResponse:
    items = await connections_repo.list_connections(str(user_id))
    import orjson

    return Response(content=orjson.dumps(items), media_type="application/json")  # type: ignore[return-value]


@router.delete("/connections/{connection_id}", status_code=204, response_model=None)
async def delete_connection(connection_id: uuid.UUID) -> Response:
    deleted = await connections_repo.delete_connection(str(connection_id))
    if not deleted:
        return problem_response(
            status_code=404,
            title="Connection Not Found",
            detail=f"No tracker connection with id '{connection_id}' was found.",
        )
    return Response(status_code=204)
