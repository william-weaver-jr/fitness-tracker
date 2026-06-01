"""User repository — CRUD operations."""

from __future__ import annotations

from typing import Any


def _pool() -> Any:
    from fittrack.database.connection import get_pool

    return get_pool()


async def list_users(
    *,
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    """Return (items, total_count) of users."""
    pool = _pool()
    async with pool.acquire() as conn:
        cursor = conn.cursor()
        await cursor.execute("SELECT COUNT(*) FROM users")
        row = await cursor.fetchone()
        total: int = row[0] if row else 0
        await cursor.execute(
            """
            SELECT JSON_OBJECT(
                '_id'           VALUE RAWTOHEX(user_id),
                'email'         VALUE email,
                'status'        VALUE status,
                'role'          VALUE role,
                'pointBalance'  VALUE point_balance,
                'emailVerified' VALUE email_verified,
                'createdAt'     VALUE TO_CHAR(created_at, 'YYYY-MM-DD"T"HH24:MI:SS'),
                'updatedAt'     VALUE TO_CHAR(updated_at, 'YYYY-MM-DD"T"HH24:MI:SS'),
                'lastLoginAt'   VALUE TO_CHAR(last_login_at, 'YYYY-MM-DD"T"HH24:MI:SS')
                ABSENT ON NULL
            ) FROM users
            ORDER BY created_at DESC
            OFFSET :1 ROWS FETCH NEXT :2 ROWS ONLY
            """,
            [offset, limit],
        )
        rows = await cursor.fetchall()
    import orjson

    items = [orjson.loads(r[0]) for r in rows]
    return items, total


async def get_user(user_id: str) -> dict[str, Any] | None:
    pool = _pool()
    async with pool.acquire() as conn:
        cursor = conn.cursor()
        await cursor.execute(
            """
            SELECT JSON_OBJECT(
                '_id'           VALUE RAWTOHEX(user_id),
                'email'         VALUE email,
                'status'        VALUE status,
                'role'          VALUE role,
                'pointBalance'  VALUE point_balance,
                'emailVerified' VALUE email_verified,
                'version'       VALUE version,
                'createdAt'     VALUE TO_CHAR(created_at, 'YYYY-MM-DD"T"HH24:MI:SS'),
                'updatedAt'     VALUE TO_CHAR(updated_at, 'YYYY-MM-DD"T"HH24:MI:SS'),
                'lastLoginAt'   VALUE TO_CHAR(last_login_at, 'YYYY-MM-DD"T"HH24:MI:SS')
                ABSENT ON NULL
            ) FROM users
            WHERE RAWTOHEX(user_id) = :1
            """,
            [user_id.replace("-", "").upper()],
        )
        row = await cursor.fetchone()
    if row is None:
        return None
    import orjson

    return orjson.loads(row[0])  # type: ignore[no-any-return]


async def delete_user(user_id: str) -> bool:
    pool = _pool()
    async with pool.acquire() as conn:
        cursor = conn.cursor()
        await cursor.execute(
            "DELETE FROM users WHERE RAWTOHEX(user_id) = :1",
            [user_id.replace("-", "").upper()],
        )
        deleted = cursor.rowcount > 0
        await conn.commit()
    return deleted
