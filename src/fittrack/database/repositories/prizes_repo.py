"""Prize repository."""

from __future__ import annotations

from typing import Any


def _pool() -> Any:
    from fittrack.database.connection import get_pool

    return get_pool()


async def list_prizes(
    drawing_id: str, *, offset: int = 0, limit: int = 20
) -> tuple[list[dict[str, Any]], int]:
    pool = _pool()
    async with pool.acquire() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            "SELECT COUNT(*) FROM prizes WHERE RAWTOHEX(drawing_id) = :1",
            [drawing_id.replace("-", "").upper()],
        )
        row = await cursor.fetchone()
        total: int = row[0] if row else 0
        await cursor.execute(
            """
            SELECT JSON_OBJECT(
                '_id'             VALUE RAWTOHEX(prize_id),
                'drawingId'       VALUE RAWTOHEX(drawing_id),
                'sponsorId'       VALUE RAWTOHEX(sponsor_id),
                'rank'            VALUE rank,
                'name'            VALUE name,
                'description'     VALUE description,
                'valueUsd'        VALUE value_usd,
                'quantity'        VALUE quantity,
                'fulfillmentType' VALUE fulfillment_type,
                'imageUrl'        VALUE image_url,
                'createdAt'       VALUE TO_CHAR(created_at, 'YYYY-MM-DD"T"HH24:MI:SS')
                ABSENT ON NULL
            ) FROM prizes
            WHERE RAWTOHEX(drawing_id) = :3
            ORDER BY rank
            OFFSET :1 ROWS FETCH NEXT :2 ROWS ONLY
            """,
            [offset, limit, drawing_id.replace("-", "").upper()],
        )
        rows = await cursor.fetchall()
    import orjson

    return [orjson.loads(r[0]) for r in rows], total


async def get_prize(prize_id: str) -> dict[str, Any] | None:
    pool = _pool()
    async with pool.acquire() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            """
            SELECT JSON_OBJECT(
                '_id'             VALUE RAWTOHEX(prize_id),
                'drawingId'       VALUE RAWTOHEX(drawing_id),
                'sponsorId'       VALUE RAWTOHEX(sponsor_id),
                'rank'            VALUE rank,
                'name'            VALUE name,
                'description'     VALUE description,
                'valueUsd'        VALUE value_usd,
                'quantity'        VALUE quantity,
                'fulfillmentType' VALUE fulfillment_type,
                'imageUrl'        VALUE image_url,
                'createdAt'       VALUE TO_CHAR(created_at, 'YYYY-MM-DD"T"HH24:MI:SS')
                ABSENT ON NULL
            ) FROM prizes WHERE RAWTOHEX(prize_id) = :1
            """,
            [prize_id.replace("-", "").upper()],
        )
        row = await cursor.fetchone()
    if row is None:
        return None
    import orjson

    return orjson.loads(row[0])  # type: ignore[no-any-return]
