"""Drawing repository."""

from __future__ import annotations

from typing import Any


def _pool() -> Any:
    from fittrack.database.connection import get_pool

    return get_pool()


_SELECT_DRAWING = """
    SELECT JSON_OBJECT(
        '_id'              VALUE RAWTOHEX(drawing_id),
        'drawingType'      VALUE drawing_type,
        'name'             VALUE name,
        'ticketCostPoints' VALUE ticket_cost_points,
        'drawingTime'      VALUE TO_CHAR(drawing_time, 'YYYY-MM-DD"T"HH24:MI:SS'),
        'ticketSalesClose' VALUE TO_CHAR(ticket_sales_close, 'YYYY-MM-DD"T"HH24:MI:SS'),
        'status'           VALUE status,
        'totalTickets'     VALUE total_tickets,
        'createdAt'        VALUE TO_CHAR(created_at, 'YYYY-MM-DD"T"HH24:MI:SS'),
        'updatedAt'        VALUE TO_CHAR(updated_at, 'YYYY-MM-DD"T"HH24:MI:SS'),
        'completedAt'      VALUE TO_CHAR(completed_at, 'YYYY-MM-DD"T"HH24:MI:SS')
        ABSENT ON NULL
    ) FROM drawings
"""


async def list_drawings(
    status: str | None = None,
    *,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    pool = _pool()
    where = "WHERE status = :3" if status else ""
    params: list[Any] = [offset, limit]
    if status:
        params.append(status)
    async with pool.acquire() as conn:
        cursor = await conn.cursor()
        await cursor.execute(f"SELECT COUNT(*) FROM drawings {where}", params[2:] if status else [])
        row = await cursor.fetchone()
        total: int = row[0] if row else 0
        await cursor.execute(
            _SELECT_DRAWING
            + f" {where} ORDER BY drawing_time DESC OFFSET :1 ROWS FETCH NEXT :2 ROWS ONLY",
            params,
        )
        rows = await cursor.fetchall()
    import orjson

    return [orjson.loads(r[0]) for r in rows], total


async def get_drawing(drawing_id: str) -> dict[str, Any] | None:
    pool = _pool()
    async with pool.acquire() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            _SELECT_DRAWING + " WHERE RAWTOHEX(drawing_id) = :1",
            [drawing_id.replace("-", "").upper()],
        )
        row = await cursor.fetchone()
    if row is None:
        return None
    import orjson

    return orjson.loads(row[0])  # type: ignore[no-any-return]


async def create_drawing(data: dict[str, Any]) -> dict[str, Any]:
    pool = _pool()
    async with pool.acquire() as conn:
        cursor = await conn.cursor()
        out_id = cursor.var(str)
        await cursor.execute(
            """
            INSERT INTO drawings (drawing_type, name, description, ticket_cost_points,
                                  drawing_time, ticket_sales_close, status)
            VALUES (:1, :2, :3, :4,
                    TO_TIMESTAMP(:5, 'YYYY-MM-DD"T"HH24:MI:SS'),
                    TO_TIMESTAMP(:6, 'YYYY-MM-DD"T"HH24:MI:SS'),
                    :7)
            RETURNING RAWTOHEX(drawing_id) INTO :8
            """,
            [
                data["drawingType"],
                data["name"],
                data.get("description"),
                data["ticketCostPoints"],
                data["drawingTime"],
                data["ticketSalesClose"],
                data.get("status", "draft"),
                out_id,
            ],
        )
        drawing_id: str = out_id.getvalue()
        await conn.commit()
    result = await get_drawing(drawing_id)
    return result or {}


async def update_drawing_status(drawing_id: str, status: str) -> dict[str, Any] | None:
    pool = _pool()
    async with pool.acquire() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            "UPDATE drawings SET status = :1, updated_at = SYSTIMESTAMP"
            " WHERE RAWTOHEX(drawing_id) = :2",
            [status, drawing_id.replace("-", "").upper()],
        )
        if cursor.rowcount == 0:
            return None
        await conn.commit()
    return await get_drawing(drawing_id)
