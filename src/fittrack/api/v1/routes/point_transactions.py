"""Point transaction routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query
from fastapi.responses import Response

from fittrack.api.errors import problem_response
from fittrack.api.pagination import Page, Paginated
from fittrack.database.repositories import point_transactions_repo

router = APIRouter(prefix="/v1", tags=["point_transactions"])


@router.get("/point-transactions", response_model=None)
async def list_transactions(
    user_id: uuid.UUID | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> Response:
    pagination = Page(page=page, limit=limit)
    items, total = await point_transactions_repo.list_transactions(
        str(user_id) if user_id else None,
        offset=pagination.offset,
        limit=pagination.limit,
    )
    result = Paginated(items=items, total=total, page=page, limit=limit)
    import orjson

    return Response(content=orjson.dumps(result.model_dump()), media_type="application/json")


@router.get("/point-transactions/{transaction_id}", response_model=None)
async def get_transaction(transaction_id: uuid.UUID) -> Response:
    txn = await point_transactions_repo.get_transaction(str(transaction_id))
    if txn is None:
        return problem_response(status_code=404, title="Transaction Not Found")
    import orjson

    return Response(content=orjson.dumps(txn), media_type="application/json")
