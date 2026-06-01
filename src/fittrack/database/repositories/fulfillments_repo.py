"""Prize fulfillment repository."""

from __future__ import annotations

from typing import Any


def _pool() -> Any:
    from fittrack.database.connection import get_pool

    return get_pool()


async def list_fulfillments(
    user_id: str | None = None,
    *,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    pool = _pool()
    where = "WHERE RAWTOHEX(user_id) = :3" if user_id else ""
    params: list[Any] = [offset, limit]
    if user_id:
        params.append(user_id.replace("-", "").upper())
    async with pool.acquire() as conn:
        cursor = await conn.cursor()
        count_params = params[2:] if user_id else []
        await cursor.execute(f"SELECT COUNT(*) FROM prize_fulfillments {where}", count_params)
        row = await cursor.fetchone()
        total: int = row[0] if row else 0
        await cursor.execute(
            f"""
            SELECT JSON_OBJECT(
                '_id'                VALUE RAWTOHEX(fulfillment_id),
                'ticketId'           VALUE RAWTOHEX(ticket_id),
                'prizeId'            VALUE RAWTOHEX(prize_id),
                'userId'             VALUE RAWTOHEX(user_id),
                'status'             VALUE status,
                'trackingNumber'     VALUE tracking_number,
                'carrier'            VALUE carrier,
                'notifiedAt'         VALUE TO_CHAR(notified_at, 'YYYY-MM-DD"T"HH24:MI:SS'),
                'addressConfirmedAt' VALUE TO_CHAR(address_confirmed_at, 'YYYY-MM-DD"T"HH24:MI:SS'),
                'shippedAt'          VALUE TO_CHAR(shipped_at, 'YYYY-MM-DD"T"HH24:MI:SS'),
                'deliveredAt'        VALUE TO_CHAR(delivered_at, 'YYYY-MM-DD"T"HH24:MI:SS'),
                'createdAt'          VALUE TO_CHAR(created_at, 'YYYY-MM-DD"T"HH24:MI:SS'),
                'updatedAt'          VALUE TO_CHAR(updated_at, 'YYYY-MM-DD"T"HH24:MI:SS')
                ABSENT ON NULL
            ) FROM prize_fulfillments {where}
            ORDER BY created_at DESC
            OFFSET :1 ROWS FETCH NEXT :2 ROWS ONLY
            """,
            params,
        )
        rows = await cursor.fetchall()
    import orjson

    return [orjson.loads(r[0]) for r in rows], total


async def get_fulfillment(fulfillment_id: str) -> dict[str, Any] | None:
    pool = _pool()
    async with pool.acquire() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            """
            SELECT JSON_OBJECT(
                '_id'                VALUE RAWTOHEX(fulfillment_id),
                'ticketId'           VALUE RAWTOHEX(ticket_id),
                'prizeId'            VALUE RAWTOHEX(prize_id),
                'userId'             VALUE RAWTOHEX(user_id),
                'status'             VALUE status,
                'shippingAddress'    VALUE shipping_address FORMAT JSON,
                'trackingNumber'     VALUE tracking_number,
                'carrier'            VALUE carrier,
                'notifiedAt'         VALUE TO_CHAR(notified_at, 'YYYY-MM-DD"T"HH24:MI:SS'),
                'addressConfirmedAt' VALUE TO_CHAR(address_confirmed_at, 'YYYY-MM-DD"T"HH24:MI:SS'),
                'shippedAt'          VALUE TO_CHAR(shipped_at, 'YYYY-MM-DD"T"HH24:MI:SS'),
                'deliveredAt'        VALUE TO_CHAR(delivered_at, 'YYYY-MM-DD"T"HH24:MI:SS'),
                'createdAt'          VALUE TO_CHAR(created_at, 'YYYY-MM-DD"T"HH24:MI:SS'),
                'updatedAt'          VALUE TO_CHAR(updated_at, 'YYYY-MM-DD"T"HH24:MI:SS')
                ABSENT ON NULL
            ) FROM prize_fulfillments WHERE RAWTOHEX(fulfillment_id) = :1
            """,
            [fulfillment_id.replace("-", "").upper()],
        )
        row = await cursor.fetchone()
    if row is None:
        return None
    import orjson

    return orjson.loads(row[0])  # type: ignore[no-any-return]


async def update_fulfillment_status(fulfillment_id: str, status: str) -> dict[str, Any] | None:
    pool = _pool()
    async with pool.acquire() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            "UPDATE prize_fulfillments SET status = :1, updated_at = SYSTIMESTAMP"
            " WHERE RAWTOHEX(fulfillment_id) = :2",
            [status, fulfillment_id.replace("-", "").upper()],
        )
        if cursor.rowcount == 0:
            return None
        await conn.commit()
    return await get_fulfillment(fulfillment_id)
