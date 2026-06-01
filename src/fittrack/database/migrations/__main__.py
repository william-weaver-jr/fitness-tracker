"""CLI entry: python -m fittrack.database.migrations apply"""

from __future__ import annotations

import asyncio
import sys


async def _main() -> None:
    from fittrack.config import get_settings
    from fittrack.database.connection import close_pool, get_pool, init_pool
    from fittrack.database.migrations import apply_migrations

    settings = get_settings()
    await init_pool(settings)
    pool = get_pool()
    async with pool.acquire() as conn:
        n = await apply_migrations(conn)
    await close_pool()
    print(f"Applied {n} migration(s).")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "apply":
        asyncio.run(_main())
    else:
        print("Usage: python -m fittrack.database.migrations apply")
