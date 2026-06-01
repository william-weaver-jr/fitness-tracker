"""Tracker connection repository."""

from __future__ import annotations

from typing import Any


def _pool() -> Any:
    from fittrack.database.connection import get_pool

    return get_pool()


async def list_connections(user_id: str) -> list[dict[str, Any]]:
    pool = _pool()
    async with pool.acquire() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            """
            SELECT JSON_OBJECT(
                '_id'         VALUE RAWTOHEX(connection_id),
                'userId'      VALUE RAWTOHEX(user_id),
                'provider'    VALUE provider,
                'isPrimary'   VALUE is_primary,
                'lastSyncAt'  VALUE TO_CHAR(last_sync_at, 'YYYY-MM-DD"T"HH24:MI:SS'),
                'syncStatus'  VALUE sync_status,
                'errorMessage' VALUE error_message,
                'createdAt'   VALUE TO_CHAR(created_at, 'YYYY-MM-DD"T"HH24:MI:SS')
                ABSENT ON NULL
            ) FROM tracker_connections
            WHERE RAWTOHEX(user_id) = :1
            ORDER BY is_primary DESC, created_at
            """,
            [user_id.replace("-", "").upper()],
        )
        rows = await cursor.fetchall()
    import orjson

    return [orjson.loads(r[0]) for r in rows]


async def get_connection(connection_id: str) -> dict[str, Any] | None:
    pool = _pool()
    async with pool.acquire() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            """
            SELECT JSON_OBJECT(
                '_id'         VALUE RAWTOHEX(connection_id),
                'userId'      VALUE RAWTOHEX(user_id),
                'provider'    VALUE provider,
                'isPrimary'   VALUE is_primary,
                'lastSyncAt'  VALUE TO_CHAR(last_sync_at, 'YYYY-MM-DD"T"HH24:MI:SS'),
                'syncStatus'  VALUE sync_status,
                'errorMessage' VALUE error_message,
                'createdAt'   VALUE TO_CHAR(created_at, 'YYYY-MM-DD"T"HH24:MI:SS')
                ABSENT ON NULL
            ) FROM tracker_connections
            WHERE RAWTOHEX(connection_id) = :1
            """,
            [connection_id.replace("-", "").upper()],
        )
        row = await cursor.fetchone()
    if row is None:
        return None
    import orjson

    return orjson.loads(row[0])  # type: ignore[no-any-return]


async def delete_connection(connection_id: str) -> bool:
    pool = _pool()
    async with pool.acquire() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            "DELETE FROM tracker_connections WHERE RAWTOHEX(connection_id) = :1",
            [connection_id.replace("-", "").upper()],
        )
        deleted = cursor.rowcount > 0
        await conn.commit()
    return deleted
