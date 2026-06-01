"""Forward-only SQL migration runner for Oracle 23ai.

Migrations are plain .sql files named NNNN_<slug>.sql (e.g. 0001_core.sql).
Applied versions are tracked in the ``schema_migrations`` table.

Usage (CLI):
    python -m fittrack.database.migrations apply
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

MIGRATION_RE = re.compile(r"^(\d{4})_([a-z][a-z0-9_]*)\.sql$")

MIGRATIONS_DIR = Path(__file__).parent


@dataclass(order=True, eq=True)
class Migration:
    version: int
    name: str
    filename: str

    @property
    def path(self) -> Path:
        return MIGRATIONS_DIR / self.filename


def parse_migration_filename(filename: str) -> Migration:
    """Parse a migration filename into a Migration dataclass.

    Raises ValueError if the filename doesn't match the expected pattern.
    """
    match = MIGRATION_RE.match(filename)
    if not match:
        raise ValueError(
            f"Invalid migration filename '{filename}'. "
            "Expected pattern: NNNN_<slug>.sql (e.g. 0001_core.sql)"
        )
    return Migration(
        version=int(match.group(1)),
        name=match.group(2),
        filename=filename,
    )


def discover_migrations() -> list[Migration]:
    """Return all .sql migration files sorted by version."""
    migrations = []
    for path in MIGRATIONS_DIR.glob("*.sql"):
        try:
            migrations.append(parse_migration_filename(path.name))
        except ValueError:
            pass
    return sorted(migrations)


async def get_applied_versions(conn: object) -> set[int]:
    """Return the set of already-applied migration version numbers."""
    from typing import Any

    c = conn  # type: ignore[assignment]
    try:
        cursor = await c.cursor()
        await cursor.execute("SELECT version FROM schema_migrations")
        rows: list[Any] = await cursor.fetchall()
        return {row[0] for row in rows}
    except Exception:
        return set()


async def ensure_migrations_table(conn: object) -> None:
    c = conn  # type: ignore[assignment]
    cursor = await c.cursor()
    await cursor.execute(
        """
        DECLARE
            v_count NUMBER;
        BEGIN
            SELECT COUNT(*) INTO v_count
            FROM user_tables
            WHERE table_name = 'SCHEMA_MIGRATIONS';
            IF v_count = 0 THEN
                EXECUTE IMMEDIATE '
                    CREATE TABLE schema_migrations (
                        version   NUMBER(4) PRIMARY KEY,
                        name      VARCHAR2(255) NOT NULL,
                        applied_at TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
                    )';
            END IF;
        END;
        """
    )
    await c.commit()


async def apply_migrations(conn: object) -> int:
    """Apply all unapplied migrations. Returns number of migrations applied."""
    await ensure_migrations_table(conn)
    applied = await get_applied_versions(conn)
    pending = [m for m in discover_migrations() if m.version not in applied]

    c = conn  # type: ignore[assignment]
    for migration in pending:
        sql = migration.path.read_text(encoding="utf-8")
        cursor = await c.cursor()
        # Oracle scripts may contain multiple statements separated by "/"
        for statement in _split_statements(sql):
            if statement.strip():
                await cursor.execute(statement)
        await cursor.execute(
            "INSERT INTO schema_migrations (version, name) VALUES (:1, :2)",
            [migration.version, migration.name],
        )
        await c.commit()

    return len(pending)


def _split_statements(sql: str) -> list[str]:
    """Split a SQL script into individual statements (Oracle-style, '/' delimiter)."""
    statements = []
    current: list[str] = []
    for line in sql.splitlines():
        stripped = line.strip()
        if stripped == "/":
            if current:
                statements.append("\n".join(current))
                current = []
        else:
            current.append(line)
    if current:
        remaining = "\n".join(current).strip()
        if remaining:
            statements.append(remaining)
    return statements


if __name__ == "__main__":  # pragma: no cover
    import asyncio

    async def _main() -> None:
        from fittrack.config import get_settings
        from fittrack.database.connection import close_pool, get_pool, init_pool

        settings = get_settings()
        await init_pool(settings)
        pool = get_pool()
        async with pool.acquire() as conn:
            n = await apply_migrations(conn)
        await close_pool()
        print(f"Applied {n} migration(s).")

    if len(sys.argv) > 1 and sys.argv[1] == "apply":
        asyncio.run(_main())
    else:
        print("Usage: python -m fittrack.database.migrations apply")
