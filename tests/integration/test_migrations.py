"""Integration tests: migration runner against live Oracle Free container."""

from __future__ import annotations

from typing import Any

import pytest

from fittrack.database.migrations import apply_migrations, discover_migrations


@pytest.mark.integration
async def test_schema_migrations_table_exists(db_conn: Any) -> None:
    cursor = await db_conn.cursor()
    await cursor.execute("SELECT COUNT(*) FROM schema_migrations")
    row = await cursor.fetchone()
    assert row is not None and row[0] >= 0


@pytest.mark.integration
async def test_all_migration_files_applied(db_conn: Any) -> None:
    """Every .sql file in migrations/ has a corresponding row in schema_migrations."""
    cursor = await db_conn.cursor()
    await cursor.execute("SELECT COUNT(*) FROM schema_migrations")
    row = await cursor.fetchone()
    assert row is not None
    assert row[0] == len(discover_migrations())


@pytest.mark.integration
async def test_applying_again_is_idempotent(migrated_db: Any) -> None:
    """Re-running apply_migrations on an already-migrated schema returns 0."""
    async with migrated_db.acquire() as conn:
        n = await apply_migrations(conn)
    assert n == 0


@pytest.mark.integration
async def test_core_tables_exist(db_conn: Any) -> None:
    cursor = await db_conn.cursor()
    await cursor.execute("SELECT table_name FROM user_tables ORDER BY table_name")
    rows = await cursor.fetchall()
    tables = {r[0].lower() for r in rows}
    expected = {
        "users",
        "profiles",
        "tracker_connections",
        "activities",
        "point_transactions",
        "sponsors",
        "drawings",
        "tickets",
        "prizes",
        "prize_fulfillments",
        "schema_migrations",
    }
    assert expected <= tables


@pytest.mark.integration
async def test_json_duality_views_exist(db_conn: Any) -> None:
    cursor = await db_conn.cursor()
    await cursor.execute("SELECT view_name FROM user_views ORDER BY view_name")
    rows = await cursor.fetchall()
    views = {r[0].lower() for r in rows}
    assert {"user_profile_dv", "drawing_dv", "activity_dv"} <= views


@pytest.mark.integration
async def test_key_indexes_exist(db_conn: Any) -> None:
    cursor = await db_conn.cursor()
    await cursor.execute("SELECT index_name FROM user_indexes ORDER BY index_name")
    rows = await cursor.fetchall()
    indexes = {r[0].lower() for r in rows}
    spot_checks = {
        "idx_users_email",
        "idx_users_status",
        "idx_drawings_status",
        "idx_tickets_drawing",
        "idx_activities_user_date",
    }
    assert spot_checks <= indexes
