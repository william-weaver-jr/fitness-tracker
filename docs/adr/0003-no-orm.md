# ADR-0003: No ORM — python-oracledb directly with JSON Duality Views

**Status:** Accepted  
**Date:** 2026-06-01  
**Deciders:** FitTrack engineering

---

## Context

Python projects with relational databases conventionally reach for an ORM (SQLAlchemy, Django ORM, Tortoise-ORM) to avoid writing SQL and to get a Python object model "for free." The question was whether to introduce an ORM for FitTrack, given that Oracle 23ai JSON Duality Views are the chosen data layer (ADR-0001).

---

## Decision

Use **no ORM**. All database access goes through `python-oracledb` thin mode directly, via repository modules in `src/fittrack/database/repositories/`. JSON Duality Views (`user_profile_dv`, `drawing_dv`, `activity_dv`) are the abstraction layer; repositories issue parameterised SQL/JSON queries against them.

---

## Why

An ORM solves two problems: (1) it translates Python objects to and from SQL rows, and (2) it provides a query builder so developers do not write raw SQL. JSON Duality Views already solve problem (1): a Duality View presents a composite document that maps directly to the API's JSON shape. Adding an ORM on top creates a second translation layer that the Views make redundant.

Concretely:

- **Double-mapping is wasteful.** An ORM would map Python objects → ORM internal state → SQL rows. The Duality View then presents those rows back as a JSON document. The document is what the API actually needs. Removing the ORM cuts out the middle step entirely.
- **ORMs do not understand Duality Views.** SQLAlchemy and Tortoise-ORM have no concept of a JSON Relational Duality View. We would end up bypassing the ORM for every Duality View query anyway, giving us an inconsistent codebase — some queries through the ORM, others raw.
- **Optimistic locking is explicit.** The ticket-purchase race requires `UPDATE users SET point_balance = :new WHERE point_balance = :old AND version = :v`. ORM-generated UPDATE statements do not naturally express this pattern; it requires dropping to raw SQL regardless.
- **JSON index hygiene is visible.** Forgetting a functional JSON index causes a full table scan. With raw queries, the SQL is visible in code review and easy to correlate with migration `0003_audit.sql`. An ORM abstracts the query away, making index gaps harder to spot.
- **`python-oracledb` thin mode.** No Oracle Instant Client installation is required. The thin driver is a pure-Python async driver that integrates directly with `asyncio` connection pools. Adding an ORM would add a dependency that wraps this driver without improving the async story.

---

## Alternatives Considered

| Option | Why Rejected |
|--------|-------------|
| **SQLAlchemy 2.0 (async)** | Best-in-class Python ORM. However, it has no Duality View support; all Duality View queries would need `text()` raw SQL anyway. The Oracle dialect in SQLAlchemy is maintained but less actively than the PostgreSQL dialect — edge cases around RAW(16) primary keys, JSON columns, and Duality View syntax would need workarounds. |
| **Tortoise-ORM** | Async-native, simpler than SQLAlchemy. Lacks Oracle support entirely as of 2026. |
| **SQLModel (Pydantic + SQLAlchemy)** | Attractive because it unifies Pydantic and SQLAlchemy models. Same rejection reason as SQLAlchemy; additionally, SQLModel's Oracle support inherits SQLAlchemy's limitations. |
| **Raw SQL with a query builder (e.g., pypika)** | A query builder without a full ORM was considered. Rejected because the Duality View queries are simple enough (mostly JSON_OBJECT selects and MERGE statements) that a query builder adds complexity without removing any SQL. |

---

## Consequences

**Positive:**
- No additional abstraction layer. SQL in repository modules is readable, reviewable, and directly correlates to the migration files that define the schema.
- Optimistic locking and other Oracle-specific patterns (MERGE, HEXTORAW, JSON_OBJECT) are expressed naturally.
- No ORM migration files competing with the forward-only SQL migration runner in `src/fittrack/database/migrations/`.
- `python-oracledb` thin mode requires no system dependency — `pip install python-oracledb` is sufficient (except on ARM Mac where a wheel is not yet available; CI handles this).

**Negative:**
- Developers must write SQL. For straightforward CRUD this is low overhead, but complex analytical queries (CP4 leaderboards) will require more care.
- No automatic schema reflection or model-driven validation at the DB layer — constraints are enforced by Oracle CHECK constraints in the migration SQL, not by ORM field validators.
- Repository code is more verbose than ORM equivalents. Mitigated by keeping repositories thin (data access only) and pushing business logic into service modules (CP3+).

**Neutral:**
- Each repository module has one function per query. This is intentionally simple: no base class, no metaclass magic, no session scoping. Testing uses `unittest.mock.AsyncMock` to stub the pool at the unit level; integration tests use a real Oracle container.

---

## References

- `src/fittrack/database/repositories/` — repository modules
- `src/fittrack/database/connection.py` — async pool
- ADR-0001 — Oracle JSON Duality Views rationale
- `CLAUDE.md` — "Database Requirements" section
