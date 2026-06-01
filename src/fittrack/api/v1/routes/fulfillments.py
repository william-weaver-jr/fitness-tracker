"""Prize fulfillment routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query
from fastapi.responses import Response

from fittrack.api.errors import problem_response
from fittrack.api.pagination import Page, Paginated
from fittrack.database.repositories import fulfillments_repo

router = APIRouter(prefix="/v1/fulfillments", tags=["fulfillments"])


@router.get("", response_model=None)
async def list_fulfillments(
    user_id: uuid.UUID | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> Response:
    pagination = Page(page=page, limit=limit)
    items, total = await fulfillments_repo.list_fulfillments(
        str(user_id) if user_id else None,
        offset=pagination.offset,
        limit=pagination.limit,
    )
    result = Paginated(items=items, total=total, page=page, limit=limit)
    import orjson

    return Response(content=orjson.dumps(result.model_dump()), media_type="application/json")


@router.get("/{fulfillment_id}", response_model=None)
async def get_fulfillment(fulfillment_id: uuid.UUID) -> Response:
    fulfillment = await fulfillments_repo.get_fulfillment(str(fulfillment_id))
    if fulfillment is None:
        return problem_response(status_code=404, title="Fulfillment Not Found")
    import orjson

    return Response(content=orjson.dumps(fulfillment), media_type="application/json")
