"""Prize routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query
from fastapi.responses import Response

from fittrack.api.errors import problem_response
from fittrack.api.pagination import Page, Paginated
from fittrack.database.repositories import prizes_repo

router = APIRouter(prefix="/v1", tags=["prizes"])


@router.get("/drawings/{drawing_id}/prizes", response_model=None)
async def list_prizes(
    drawing_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> Response:
    pagination = Page(page=page, limit=limit)
    items, total = await prizes_repo.list_prizes(
        str(drawing_id), offset=pagination.offset, limit=pagination.limit
    )
    result = Paginated(items=items, total=total, page=page, limit=limit)
    import orjson

    return Response(content=orjson.dumps(result.model_dump()), media_type="application/json")


@router.get("/prizes/{prize_id}", response_model=None)
async def get_prize(prize_id: uuid.UUID) -> Response:
    prize = await prizes_repo.get_prize(str(prize_id))
    if prize is None:
        return problem_response(status_code=404, title="Prize Not Found")
    import orjson

    return Response(content=orjson.dumps(prize), media_type="application/json")
