"""Drop all application data, re-run migrations, and re-seed.

WARNING: Destructive. Dev only.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

_DROP_TABLES = [
    "prize_fulfillments",
    "tickets",
    "prizes",
    "drawings",
    "point_transactions",
    "activities",
    "tracker_connections",
    "profiles",
    "users",
    "sponsors",
    "schema_migrations",
]


async def drop_tables(conn: object) -> None:
    for table in _DROP_TABLES:
        try:
            cursor = await conn.cursor()  # type: ignore[union-attr]
            await cursor.execute(f"DROP TABLE {table} CASCADE CONSTRAINTS")
            await conn.commit()  # type: ignore[union-attr]
            print(f"  Dropped {table}")
        except Exception as exc:
            print(f"  Skipped {table} ({exc})")


async def drop_views(conn: object) -> None:
    for view in ["user_profile_dv", "drawing_dv", "activity_dv"]:
        try:
            cursor = await conn.cursor()  # type: ignore[union-attr]
            await cursor.execute(f"DROP VIEW {view}")
            await conn.commit()  # type: ignore[union-attr]
            print(f"  Dropped view {view}")
        except Exception:
            pass


async def main() -> None:
    from fittrack.config import get_settings
    from fittrack.database.connection import close_pool, get_pool, init_pool
    from fittrack.database.migrations import apply_migrations

    settings = get_settings()

    if settings.is_production:
        print("ERROR: reset_db is not allowed in production.")
        sys.exit(1)

    await init_pool(settings)
    pool = get_pool()

    async with pool.acquire() as conn:
        print("Dropping views...")
        await drop_views(conn)
        print("Dropping tables...")
        await drop_tables(conn)
        print("Running migrations...")
        n = await apply_migrations(conn)
        print(f"  Applied {n} migration(s)")

    await close_pool()

    import importlib.util

    seed_path = Path(__file__).parent / "seed_data.py"
    spec = importlib.util.spec_from_file_location("seed_data", seed_path)
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        await mod.main()

    print("\n✓ Reset complete.")


if __name__ == "__main__":
    asyncio.run(main())
