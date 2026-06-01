"""User CRUD routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, Response

from fittrack.api.errors import problem_response
from fittrack.api.pagination import Page, Paginated
from fittrack.database.repositories import users_repo

router = APIRouter(prefix="/v1/users", tags=["users"])


@router.get("", response_model=None)
async def list_users(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> JSONResponse:
    pagination = Page(page=page, limit=limit)
    items, total = await users_repo.list_users(offset=pagination.offset, limit=pagination.limit)
    result = Paginated(items=items, total=total, page=page, limit=limit)
    import orjson

    return JSONResponse(content=orjson.loads(orjson.dumps(result.model_dump())))


@router.get("/{user_id}", response_model=None)
async def get_user(user_id: uuid.UUID) -> Response:
    user = await users_repo.get_user(str(user_id))
    if user is None:
        return problem_response(
            status_code=404,
            title="User Not Found",
            detail=f"No user with id '{user_id}' was found.",
            instance=f"/v1/users/{user_id}",
        )
    import orjson

    return Response(content=orjson.dumps(user), media_type="application/json")


@router.delete("/{user_id}", status_code=204, response_model=None)
async def delete_user(user_id: uuid.UUID) -> Response:
    deleted = await users_repo.delete_user(str(user_id))
    if not deleted:
        return problem_response(
            status_code=404,
            title="User Not Found",
            detail=f"No user with id '{user_id}' was found.",
            instance=f"/v1/users/{user_id}",
        )
    return Response(status_code=204)
