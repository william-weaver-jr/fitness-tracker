"""Ticket repository."""

from __future__ import annotations

from typing import Any


def _pool() -> Any:
    from fittrack.database.connection import get_pool

    return get_pool()


async def list_tickets(
    drawing_id: str | None = None,
    user_id: str | None = None,
    *,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    pool = _pool()
    conditions = []
    params: list[Any] = [offset, limit]
    if drawing_id:
        conditions.append(f"RAWTOHEX(drawing_id) = :{len(params) + 1}")
        params.append(drawing_id.replace("-", "").upper())
    if user_id:
        conditions.append(f"RAWTOHEX(user_id) = :{len(params) + 1}")
        params.append(user_id.replace("-", "").upper())
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    async with pool.acquire() as conn:
        cursor = conn.cursor()
        await cursor.execute(f"SELECT COUNT(*) FROM tickets {where}", params[2:])
        row = await cursor.fetchone()
        total: int = row[0] if row else 0
        await cursor.execute(
            f"""
            SELECT JSON_OBJECT(
                '_id'          VALUE RAWTOHEX(ticket_id),
                'drawingId'    VALUE RAWTOHEX(drawing_id),
                'userId'       VALUE RAWTOHEX(user_id),
                'ticketNumber' VALUE ticket_number,
                'isWinner'     VALUE is_winner,
                'createdAt'    VALUE TO_CHAR(created_at, 'YYYY-MM-DD"T"HH24:MI:SS')
                ABSENT ON NULL
            ) FROM tickets {where}
            ORDER BY created_at DESC
            OFFSET :1 ROWS FETCH NEXT :2 ROWS ONLY
            """,
            params,
        )
        rows = await cursor.fetchall()
    import orjson

    return [orjson.loads(r[0]) for r in rows], total


async def get_ticket(ticket_id: str) -> dict[str, Any] | None:
    pool = _pool()
    async with pool.acquire() as conn:
        cursor = conn.cursor()
        await cursor.execute(
            """
            SELECT JSON_OBJECT(
                '_id'          VALUE RAWTOHEX(ticket_id),
                'drawingId'    VALUE RAWTOHEX(drawing_id),
                'userId'       VALUE RAWTOHEX(user_id),
                'ticketNumber' VALUE ticket_number,
                'isWinner'     VALUE is_winner,
                'prizeId'      VALUE RAWTOHEX(prize_id),
                'createdAt'    VALUE TO_CHAR(created_at, 'YYYY-MM-DD"T"HH24:MI:SS')
                ABSENT ON NULL
            ) FROM tickets WHERE RAWTOHEX(ticket_id) = :1
            """,
            [ticket_id.replace("-", "").upper()],
        )
        row = await cursor.fetchone()
    if row is None:
        return None
    import orjson

    return orjson.loads(row[0])  # type: ignore[no-any-return]
