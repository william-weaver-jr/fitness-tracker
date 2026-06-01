"""Activity repository."""

from __future__ import annotations

from typing import Any


def _pool() -> Any:
    from fittrack.database.connection import get_pool

    return get_pool()


async def list_activities(
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
        cursor = conn.cursor()
        count_sql = f"SELECT COUNT(*) FROM activities {where}"
        await cursor.execute(count_sql, params[2:] if user_id else [])
        row = await cursor.fetchone()
        total: int = row[0] if row else 0
        await cursor.execute(
            f"""
            SELECT JSON_OBJECT(
                '_id'            VALUE RAWTOHEX(activity_id),
                'userId'         VALUE RAWTOHEX(user_id),
                'activityType'   VALUE activity_type,
                'startTime'      VALUE TO_CHAR(start_time, 'YYYY-MM-DD"T"HH24:MI:SS'),
                'endTime'        VALUE TO_CHAR(end_time, 'YYYY-MM-DD"T"HH24:MI:SS'),
                'durationMinutes' VALUE duration_minutes,
                'intensity'      VALUE intensity,
                'pointsEarned'   VALUE points_earned,
                'createdAt'      VALUE TO_CHAR(created_at, 'YYYY-MM-DD"T"HH24:MI:SS')
                ABSENT ON NULL
            ) FROM activities {where}
            ORDER BY start_time DESC
            OFFSET :1 ROWS FETCH NEXT :2 ROWS ONLY
            """,
            params,
        )
        rows = await cursor.fetchall()
    import orjson

    return [orjson.loads(r[0]) for r in rows], total


async def get_activity(activity_id: str) -> dict[str, Any] | None:
    pool = _pool()
    async with pool.acquire() as conn:
        cursor = conn.cursor()
        await cursor.execute(
            """
            SELECT JSON_OBJECT(
                '_id'            VALUE RAWTOHEX(activity_id),
                'userId'         VALUE RAWTOHEX(user_id),
                'activityType'   VALUE activity_type,
                'startTime'      VALUE TO_CHAR(start_time, 'YYYY-MM-DD"T"HH24:MI:SS'),
                'endTime'        VALUE TO_CHAR(end_time, 'YYYY-MM-DD"T"HH24:MI:SS'),
                'durationMinutes' VALUE duration_minutes,
                'intensity'      VALUE intensity,
                'metrics'        VALUE metrics FORMAT JSON,
                'pointsEarned'   VALUE points_earned,
                'createdAt'      VALUE TO_CHAR(created_at, 'YYYY-MM-DD"T"HH24:MI:SS')
                ABSENT ON NULL
            ) FROM activities WHERE RAWTOHEX(activity_id) = :1
            """,
            [activity_id.replace("-", "").upper()],
        )
        row = await cursor.fetchone()
    if row is None:
        return None
    import orjson

    return orjson.loads(row[0])  # type: ignore[no-any-return]
