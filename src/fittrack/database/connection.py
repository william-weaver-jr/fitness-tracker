"""Oracle async connection pool management.

Uses python-oracledb in thin mode (no Oracle client install required).
In development/test environments where python-oracledb is unavailable,
all functions raise ImportError so callers can degrade gracefully.
"""

from __future__ import annotations

from typing import Any

from fittrack.config import Settings

_pool: Any = None


async def init_pool(settings: Settings) -> None:
    """Create the global async connection pool."""
    global _pool
    try:
        import oracledb  # type: ignore[import-untyped]
    except ImportError as exc:
        raise ImportError("python-oracledb is not installed") from exc

    _pool = await oracledb.create_pool_async(
        user=settings.oracle_user,
        password=settings.oracle_password,
        dsn=settings.oracle_dsn,
        min=settings.oracle_pool_min,
        max=settings.oracle_pool_max,
        increment=settings.oracle_pool_increment,
    )


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> Any:
    if _pool is None:
        raise RuntimeError("Connection pool not initialised — call init_pool() first")
    return _pool
