"""Ticket routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query
from fastapi.responses import Response

from fittrack.api.errors import problem_response
from fittrack.api.pagination import Page, Paginated
from fittrack.database.repositories import tickets_repo

router = APIRouter(prefix="/v1/tickets", tags=["tickets"])


@router.get("", response_model=None)
async def list_tickets(
    drawing_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> Response:
    pagination = Page(page=page, limit=limit)
    items, total = await tickets_repo.list_tickets(
        str(drawing_id) if drawing_id else None,
        str(user_id) if user_id else None,
        offset=pagination.offset,
        limit=pagination.limit,
    )
    result = Paginated(items=items, total=total, page=page, limit=limit)
    import orjson

    return Response(content=orjson.dumps(result.model_dump()), media_type="application/json")


@router.get("/{ticket_id}", response_model=None)
async def get_ticket(ticket_id: uuid.UUID) -> Response:
    ticket = await tickets_repo.get_ticket(str(ticket_id))
    if ticket is None:
        return problem_response(status_code=404, title="Ticket Not Found")
    import orjson

    return Response(content=orjson.dumps(ticket), media_type="application/json")
