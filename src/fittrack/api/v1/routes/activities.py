"""Activity routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, Response

from fittrack.api.errors import problem_response
from fittrack.api.pagination import Page, Paginated
from fittrack.database.repositories import activities_repo

router = APIRouter(prefix="/v1", tags=["activities"])


@router.get("/activities", response_model=None)
async def list_activities(
    user_id: uuid.UUID | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> JSONResponse:
    pagination = Page(page=page, limit=limit)
    items, total = await activities_repo.list_activities(
        str(user_id) if user_id else None,
        offset=pagination.offset,
        limit=pagination.limit,
    )
    result = Paginated(items=items, total=total, page=page, limit=limit)
    import orjson

    return Response(content=orjson.dumps(result.model_dump()), media_type="application/json")  # type: ignore[return-value]


@router.get("/activities/{activity_id}", response_model=None)
async def get_activity(activity_id: uuid.UUID) -> Response:
    activity = await activities_repo.get_activity(str(activity_id))
    if activity is None:
        return problem_response(status_code=404, title="Activity Not Found")
    import orjson

    return Response(content=orjson.dumps(activity), media_type="application/json")
