"""Profile repository."""

from __future__ import annotations

from typing import Any


def _pool() -> Any:
    from fittrack.database.connection import get_pool

    return get_pool()


async def get_profile(user_id: str) -> dict[str, Any] | None:
    pool = _pool()
    async with pool.acquire() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            """
            SELECT JSON_OBJECT(
                '_id'              VALUE RAWTOHEX(profile_id),
                'userId'           VALUE RAWTOHEX(user_id),
                'displayName'      VALUE display_name,
                'dateOfBirth'      VALUE TO_CHAR(date_of_birth, 'YYYY-MM-DD'),
                'stateOfResidence' VALUE state_of_residence,
                'biologicalSex'    VALUE biological_sex,
                'ageBracket'       VALUE age_bracket,
                'fitnessLevel'     VALUE fitness_level,
                'tierCode'         VALUE tier_code,
                'heightInches'     VALUE height_inches,
                'weightPounds'     VALUE weight_pounds,
                'createdAt'        VALUE TO_CHAR(created_at, 'YYYY-MM-DD"T"HH24:MI:SS'),
                'updatedAt'        VALUE TO_CHAR(updated_at, 'YYYY-MM-DD"T"HH24:MI:SS')
                ABSENT ON NULL
            ) FROM profiles WHERE RAWTOHEX(user_id) = :1
            """,
            [user_id.replace("-", "").upper()],
        )
        row = await cursor.fetchone()
    if row is None:
        return None
    import orjson

    return orjson.loads(row[0])  # type: ignore[no-any-return]


async def upsert_profile(user_id: str, data: dict[str, Any]) -> dict[str, Any]:
    pool = _pool()
    async with pool.acquire() as conn:
        cursor = await conn.cursor()
        await cursor.execute(
            """
            MERGE INTO profiles p
            USING (SELECT HEXTORAW(:1) AS uid FROM dual) src ON (p.user_id = src.uid)
            WHEN MATCHED THEN UPDATE SET
                display_name = :2, biological_sex = :3, age_bracket = :4,
                fitness_level = :5, tier_code = :6,
                height_inches = :7, weight_pounds = :8,
                updated_at = SYSTIMESTAMP
            WHEN NOT MATCHED THEN INSERT (
                user_id, display_name, date_of_birth, state_of_residence,
                biological_sex, age_bracket, fitness_level, tier_code,
                height_inches, weight_pounds
            ) VALUES (
                HEXTORAW(:1), :2, TO_DATE(:9, 'YYYY-MM-DD'), :10,
                :3, :4, :5, :6, :7, :8
            )
            """,
            [
                user_id.replace("-", "").upper(),
                data.get("displayName"),
                data.get("biologicalSex"),
                data.get("ageBracket"),
                data.get("fitnessLevel"),
                data.get("tierCode"),
                data.get("heightInches"),
                data.get("weightPounds"),
                data.get("dateOfBirth"),
                data.get("stateOfResidence"),
            ],
        )
        await conn.commit()
    result = await get_profile(user_id)
    return result or {}
