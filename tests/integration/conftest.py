"""Integration-test fixtures — require a running Oracle Free container.

All tests in this directory are automatically skipped if python-oracledb is not
installed or if the Oracle container is unreachable. Start Oracle with:

    make docker-up && make db-migrate
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio

from fittrack.config import Settings
from fittrack.database.connection import close_pool, get_pool, init_pool
from fittrack.database.migrations import apply_migrations

# Delete order respects FK constraints: children must be deleted before parents.
_DELETE_ORDER = [
    "prize_fulfillments",
    "tickets",
    "point_transactions",
    "activities",
    "prizes",
    "tracker_connections",
    "drawings",
    "profiles",
    "users",
    "sponsors",
]


@pytest.fixture(scope="session", autouse=True)
def require_oracledb() -> None:
    """Skip the entire integration suite if python-oracledb is not installed."""
    pytest.importorskip("oracledb")


@pytest_asyncio.fixture(scope="session")
async def db_pool(require_oracledb: None) -> AsyncGenerator[Any, None]:
    """Session-scoped Oracle connection pool. Skips if the DB is unreachable."""
    settings = Settings()
    try:
        await init_pool(settings)
    except Exception as exc:
        pytest.skip(f"Oracle unreachable: {exc}")
    yield get_pool()
    await close_pool()


@pytest_asyncio.fixture(scope="session")
async def migrated_db(db_pool: Any) -> AsyncGenerator[Any, None]:
    """Apply all pending migrations once per session; yield the pool."""
    async with db_pool.acquire() as conn:
        await apply_migrations(conn)
    yield db_pool


@pytest_asyncio.fixture
async def db_conn(migrated_db: Any) -> AsyncGenerator[Any, None]:
    """One pooled connection per test. Caller is responsible for data cleanup."""
    async with migrated_db.acquire() as conn:
        yield conn


@pytest_asyncio.fixture
async def clean_db(migrated_db: Any) -> AsyncGenerator[Any, None]:
    """Truncate all data tables before and after each test; yield a connection."""
    async with migrated_db.acquire() as conn:
        await _delete_all_rows(conn)
    async with migrated_db.acquire() as conn:
        yield conn
    async with migrated_db.acquire() as conn:
        await _delete_all_rows(conn)


async def _delete_all_rows(conn: Any) -> None:
    cursor = await conn.cursor()
    for table in _DELETE_ORDER:
        await cursor.execute(f"DELETE FROM {table}")  # noqa: S608
    await conn.commit()
