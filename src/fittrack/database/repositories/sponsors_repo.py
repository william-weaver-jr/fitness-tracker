"""Sponsor repository."""

from __future__ import annotations

from typing import Any


def _pool() -> Any:
    from fittrack.database.connection import get_pool

    return get_pool()


_SELECT_SPONSOR = """
    SELECT JSON_OBJECT(
        '_id'          VALUE RAWTOHEX(sponsor_id),
        'name'         VALUE name,
        'contactName'  VALUE contact_name,
        'contactEmail' VALUE contact_email,
        'contactPhone' VALUE contact_phone,
        'websiteUrl'   VALUE website_url,
        'logoUrl'      VALUE logo_url,
        'status'       VALUE status,
        'notes'        VALUE notes,
        'createdAt'    VALUE TO_CHAR(created_at, 'YYYY-MM-DD"T"HH24:MI:SS'),
        'updatedAt'    VALUE TO_CHAR(updated_at, 'YYYY-MM-DD"T"HH24:MI:SS')
        ABSENT ON NULL
    ) FROM sponsors
"""


async def list_sponsors(*, offset: int = 0, limit: int = 20) -> tuple[list[dict[str, Any]], int]:
    pool = _pool()
    async with pool.acquire() as conn:
        cursor = conn.cursor()
        await cursor.execute("SELECT COUNT(*) FROM sponsors")
        row = await cursor.fetchone()
        total: int = row[0] if row else 0
        await cursor.execute(
            _SELECT_SPONSOR + " ORDER BY name OFFSET :1 ROWS FETCH NEXT :2 ROWS ONLY",
            [offset, limit],
        )
        rows = await cursor.fetchall()
    import orjson

    return [orjson.loads(r[0]) for r in rows], total


async def get_sponsor(sponsor_id: str) -> dict[str, Any] | None:
    pool = _pool()
    async with pool.acquire() as conn:
        cursor = conn.cursor()
        await cursor.execute(
            _SELECT_SPONSOR + " WHERE RAWTOHEX(sponsor_id) = :1",
            [sponsor_id.replace("-", "").upper()],
        )
        row = await cursor.fetchone()
    if row is None:
        return None
    import orjson

    return orjson.loads(row[0])  # type: ignore[no-any-return]


async def create_sponsor(data: dict[str, Any]) -> dict[str, Any]:
    pool = _pool()
    async with pool.acquire() as conn:
        cursor = conn.cursor()
        await cursor.execute(
            """
            INSERT INTO sponsors (name, contact_name, contact_email, contact_phone,
                                  website_url, logo_url, status, notes)
            VALUES (:1, :2, :3, :4, :5, :6, :7, :8)
            RETURNING RAWTOHEX(sponsor_id) INTO :9
            """,
            [
                data["name"],
                data.get("contactName"),
                data.get("contactEmail"),
                data.get("contactPhone"),
                data.get("websiteUrl"),
                data.get("logoUrl"),
                data.get("status", "active"),
                data.get("notes"),
                cursor.var(str),
            ],
        )
        sponsor_id: str = cursor.bindvars[-1].getvalue()  # type: ignore[union-attr]
        await conn.commit()
    result = await get_sponsor(sponsor_id)
    return result or {}


async def update_sponsor(sponsor_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
    pool = _pool()
    async with pool.acquire() as conn:
        cursor = conn.cursor()
        set_clauses = ", ".join(
            f"{col} = :{i + 2}"
            for i, col in enumerate(
                ["name", "contact_name", "contact_email", "website_url", "logo_url", "status"]
            )
        )
        await cursor.execute(
            f"UPDATE sponsors SET {set_clauses}, updated_at = SYSTIMESTAMP"
            " WHERE RAWTOHEX(sponsor_id) = :1",
            [
                sponsor_id.replace("-", "").upper(),
                data.get("name"),
                data.get("contactName"),
                data.get("contactEmail"),
                data.get("websiteUrl"),
                data.get("logoUrl"),
                data.get("status"),
            ],
        )
        if cursor.rowcount == 0:
            return None
        await conn.commit()
    return await get_sponsor(sponsor_id)


async def delete_sponsor(sponsor_id: str) -> bool:
    pool = _pool()
    async with pool.acquire() as conn:
        cursor = conn.cursor()
        await cursor.execute(
            "DELETE FROM sponsors WHERE RAWTOHEX(sponsor_id) = :1",
            [sponsor_id.replace("-", "").upper()],
        )
        deleted = cursor.rowcount > 0
        await conn.commit()
    return deleted
