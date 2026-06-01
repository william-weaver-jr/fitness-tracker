"""Sponsor routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query
from fastapi.responses import Response

from fittrack.api.errors import problem_response
from fittrack.api.pagination import Page, Paginated
from fittrack.database.repositories import sponsors_repo

router = APIRouter(prefix="/v1/sponsors", tags=["sponsors"])


@router.get("", response_model=None)
async def list_sponsors(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> Response:
    pagination = Page(page=page, limit=limit)
    items, total = await sponsors_repo.list_sponsors(
        offset=pagination.offset, limit=pagination.limit
    )
    result = Paginated(items=items, total=total, page=page, limit=limit)
    import orjson

    return Response(content=orjson.dumps(result.model_dump()), media_type="application/json")


@router.get("/{sponsor_id}", response_model=None)
async def get_sponsor(sponsor_id: uuid.UUID) -> Response:
    sponsor = await sponsors_repo.get_sponsor(str(sponsor_id))
    if sponsor is None:
        return problem_response(status_code=404, title="Sponsor Not Found")
    import orjson

    return Response(content=orjson.dumps(sponsor), media_type="application/json")


@router.post("", status_code=201, response_model=None)
async def create_sponsor(body: dict) -> Response:
    sponsor = await sponsors_repo.create_sponsor(body)
    import orjson

    return Response(content=orjson.dumps(sponsor), status_code=201, media_type="application/json")


@router.delete("/{sponsor_id}", status_code=204, response_model=None)
async def delete_sponsor(sponsor_id: uuid.UUID) -> Response:
    deleted = await sponsors_repo.delete_sponsor(str(sponsor_id))
    if not deleted:
        return problem_response(status_code=404, title="Sponsor Not Found")
    return Response(status_code=204)
