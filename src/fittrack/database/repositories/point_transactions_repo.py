"""Point transaction repository."""

from __future__ import annotations

from typing import Any


def _pool() -> Any:
    from fittrack.database.connection import get_pool

    return get_pool()


async def list_transactions(
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
        await cursor.execute(f"SELECT COUNT(*) FROM point_transactions {where}", count_params)
        row = await cursor.fetchone()
        total: int = row[0] if row else 0
        await cursor.execute(
            f"""
            SELECT JSON_OBJECT(
                '_id'             VALUE RAWTOHEX(transaction_id),
                'userId'          VALUE RAWTOHEX(user_id),
                'transactionType' VALUE transaction_type,
                'amount'          VALUE amount,
                'balanceAfter'    VALUE balance_after,
                'referenceType'   VALUE reference_type,
                'description'     VALUE description,
                'createdAt'       VALUE TO_CHAR(created_at, 'YYYY-MM-DD"T"HH24:MI:SS')
                ABSENT ON NULL
            ) FROM point_transactions {where}
            ORDER BY created_at DESC
            OFFSET :1 ROWS FETCH NEXT :2 ROWS ONLY
            """,
            params,
        )
        rows = await cursor.fetchall()
    import orjson

    return [orjson.loads(r[0]) for r in rows], total


async def get_transaction(transaction_id: str) -> dict[str, Any] | None:
    pool = _pool()
    async with pool.acquire() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            """
            SELECT JSON_OBJECT(
                '_id'             VALUE RAWTOHEX(transaction_id),
                'userId'          VALUE RAWTOHEX(user_id),
                'transactionType' VALUE transaction_type,
                'amount'          VALUE amount,
                'balanceAfter'    VALUE balance_after,
                'referenceType'   VALUE reference_type,
                'description'     VALUE description,
                'createdAt'       VALUE TO_CHAR(created_at, 'YYYY-MM-DD"T"HH24:MI:SS')
                ABSENT ON NULL
            ) FROM point_transactions WHERE RAWTOHEX(transaction_id) = :1
            """,
            [transaction_id.replace("-", "").upper()],
        )
        row = await cursor.fetchone()
    if row is None:
        return None
    import orjson

    return orjson.loads(row[0])  # type: ignore[no-any-return]
