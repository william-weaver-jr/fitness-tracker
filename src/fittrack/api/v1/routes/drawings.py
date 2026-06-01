"""Drawing routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query
from fastapi.responses import Response

from fittrack.api.errors import problem_response
from fittrack.api.pagination import Page, Paginated
from fittrack.database.repositories import drawings_repo

router = APIRouter(prefix="/v1/drawings", tags=["drawings"])


@router.get("", response_model=None)
async def list_drawings(
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> Response:
    pagination = Page(page=page, limit=limit)
    items, total = await drawings_repo.list_drawings(
        status, offset=pagination.offset, limit=pagination.limit
    )
    result = Paginated(items=items, total=total, page=page, limit=limit)
    import orjson

    return Response(content=orjson.dumps(result.model_dump()), media_type="application/json")


@router.get("/{drawing_id}", response_model=None)
async def get_drawing(drawing_id: uuid.UUID) -> Response:
    drawing = await drawings_repo.get_drawing(str(drawing_id))
    if drawing is None:
        return problem_response(status_code=404, title="Drawing Not Found")
    import orjson

    return Response(content=orjson.dumps(drawing), media_type="application/json")


@router.post("", status_code=201, response_model=None)
async def create_drawing(body: dict) -> Response:
    drawing = await drawings_repo.create_drawing(body)
    import orjson

    return Response(content=orjson.dumps(drawing), status_code=201, media_type="application/json")
