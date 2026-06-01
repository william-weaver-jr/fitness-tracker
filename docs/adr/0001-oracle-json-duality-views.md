# ADR-0001: Oracle 23ai with JSON Duality Views as the data layer

**Status:** Accepted  
**Date:** 2026-06-01  
**Deciders:** FitTrack engineering

---

## Context

FitTrack needs a database that can:

1. Serve document-shaped API responses efficiently (user + profile + connections as one JSON document; drawing + prizes as another) without a proliferation of joins in application code.
2. Enforce relational integrity for financial operations — ticket purchases must atomically debit a point balance and insert a ticket row; that cannot fail silently.
3. Support concurrent write safety for the ticket-purchase race condition (`point_balance` optimistic locking, version column).
4. Deploy on Oracle Cloud Infrastructure, where the production target is **Oracle Autonomous JSON Database**.

The two requirements pull in opposite directions: NoSQL databases handle document access well but give up ACID multi-table transactions; traditional RDBMS give ACID but require application-level mapping from rows to JSON objects.

---

## Decision

Use **Oracle Database 23ai** (locally: Oracle Database Free 23ai via Docker; production: Oracle Autonomous JSON Database) with **JSON Relational Duality Views** as the primary data access pattern.

All application reads and writes flow through Duality Views (`user_profile_dv`, `drawing_dv`, `activity_dv`). Underlying tables (`users`, `profiles`, `tracker_connections`, etc.) retain full relational constraints and indexes. Python code uses `python-oracledb` in thin mode directly — no ORM.

---

## Alternatives Considered

| Option | Why Rejected |
|--------|-------------|
| **PostgreSQL + JSONB** | Strong JSONB support, but we are deploying to OCI and Autonomous JSON DB is the managed DB service there. Switching engines would mean foregoing managed HA, backups, and scaling that Autonomous provides. |
| **MongoDB** | Document model fits the API shape, but lacks the multi-table ACID transactions required for the ticket-purchase race and point-ledger atomicity. Aggregation pipeline complexity also grows quickly. |
| **Oracle + SQLAlchemy ORM** | ORM would add a redundant abstraction layer on top of Duality Views, which already provide the document/object mapping. See ADR-0003. |
| **Oracle + raw SQL only (no Duality Views)** | Possible, but means writing join-heavy queries for every composite read. Duality Views centralise that mapping once and make the document shape explicit and auditable. |

---

## Consequences

**Positive:**
- Duality Views give document-style reads and writes with full relational integrity — one SQL/JSON object maps directly to an API response with no application-layer mapping code.
- Oracle ACID guarantees cover the ticket-purchase transaction and optimistic locking on `point_balance`.
- `python-oracledb` thin mode requires no Oracle Instant Client installation, which keeps local developer setup to Docker + pip.
- Dev/prod parity: Oracle Free 23ai locally mirrors Autonomous JSON DB closely enough that schema, Duality View definitions, and functional JSON indexes port directly.

**Negative:**
- Oracle expertise is less common than PostgreSQL in the Python community. Onboarding requires reading the JSON Duality Views documentation.
- Oracle Free container is ~3.5 GB and takes ~60 s to boot on first start, slowing the initial `make docker-up`.
- `python-oracledb>=2.5.0` has no pre-built ARM Mac wheel; developers on Apple Silicon must run integration tests in CI rather than locally (see `CLAUDE.md` gotchas).

**Neutral:**
- Functional JSON indexes must be added for every JSON path queried through a Duality View, or queries silently fall back to full table scans (migration `0003_audit.sql`).
- Autonomous JSON DB in production uses Wallet authentication; local dev uses plain user/password. The `ORACLE_WALLET_DIR` env var switches modes without code changes.

---

## References

- Oracle JSON Relational Duality Views documentation
- `src/fittrack/database/migrations/0002_views.sql` — view definitions
- `src/fittrack/database/migrations/0003_audit.sql` — functional indexes
- ADR-0003 — no ORM rationale
