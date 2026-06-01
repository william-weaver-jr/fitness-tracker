"""Profile routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter
from fastapi.responses import Response

from fittrack.api.errors import problem_response
from fittrack.database.repositories import profiles_repo

router = APIRouter(prefix="/v1/users", tags=["profiles"])


@router.get("/{user_id}/profile", response_model=None)
async def get_profile(user_id: uuid.UUID) -> Response:
    profile = await profiles_repo.get_profile(str(user_id))
    if profile is None:
        return problem_response(
            status_code=404,
            title="Profile Not Found",
            detail=f"No profile found for user '{user_id}'.",
        )
    import orjson

    return Response(content=orjson.dumps(profile), media_type="application/json")


@router.put("/{user_id}/profile", response_model=None)
async def upsert_profile(user_id: uuid.UUID, body: dict) -> Response:
    profile = await profiles_repo.upsert_profile(str(user_id), body)
    import orjson

    return Response(content=orjson.dumps(profile), media_type="application/json")
