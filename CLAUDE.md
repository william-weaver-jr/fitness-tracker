# FitTrack

> Gamified fitness tracker — earn points from activity, spend them on sweepstakes tickets for tiered prize drawings.

## Overview

FitTrack converts physical activity (synced from Apple Health, Google Fit, and Fitbit) into points that users spend on sweepstakes tickets across daily, weekly, monthly, and annual drawings. Fairness comes from **30 demographic competition tiers** (5 age brackets × 2 sex categories × 3 fitness levels). MVP is US-only, 18+, on Oracle Cloud Infrastructure.

## Tech Stack

| Component       | Choice                          | Why (if non-obvious)                                                                                 |
| --------------- | ------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Database (prod) | Oracle Autonomous JSON Database | JSON Duality Views give document-style access with relational integrity; required by deploy target   |
| Database (dev)  | Oracle Database Free 23ai       | Closest local parity to Autonomous JSON DB; supports JSON Tables + Duality Views                     |
| DB driver       | `python-oracledb` (thin mode)   | No client install, async support; no ORM — JSON Duality Views replace it                             |
| API framework   | FastAPI + Pydantic v2           | Auto OpenAPI, strict request/response schemas, async-native                                          |
| Worker queue    | OCI Queue (prod) / APScheduler (dev) | 15-min batch syncs and drawing execution don't justify Celery/Redis Streams in MVP             |
| Cache           | OCI Cache (Redis)               | Leaderboard sorted sets, session/JWT denylist                                                        |
| RNG             | OCI Vault CSPRNG                | Drawing integrity requires audited cryptographic randomness — never use `random`/`secrets` directly  |
| Frontend (CP1)  | Static HTML + vanilla JS        | Development test harness only — disabled in production                                               |
| Frontend (CP8+) | React 18 + Vite                 | Mobile-first responsive web app; native apps deferred to v1.1                                        |
| Auth            | JWT RS256 (keys in OCI Vault)   | Symmetric HS256 would couple all services to one shared secret                                       |

## Database Requirements

**CRITICAL**: Oracle 23ai/26ai with **JSON Duality Views** is the primary access pattern. Do not introduce an ORM (SQLAlchemy, Tortoise, etc.) — Duality Views are the abstraction.

- Use `python-oracledb` in async/thin mode with a connection pool
- Define JSON Duality Views for every aggregate (user+profile+connections, drawing+prizes, etc.)
- Functional JSON indexes for any field queried via Duality View
- OAuth tokens stored encrypted (AES-256-GCM) — never in plain text columns
- `point_balance` updates require optimistic locking (version column) — concurrent ticket purchases race

## Project Layout

```
src/fittrack/
├── api/v1/        # FastAPI routes + Pydantic schemas (RFC 7807 errors)
├── services/      # Business logic (points, tiers, drawings, sync)
├── database/      # Connection pool, repositories, migrations, Duality Views
├── workers/       # Background jobs (sync, drawing execution, leaderboard)
├── domain/        # Enums, value objects (tier codes, intensity levels)
└── utils/         # Crypto, RNG client, JWT helpers
tests/
├── unit/          # Pure logic (points calc, tier assignment) — hypothesis property tests
├── integration/   # Repository + API tests against real Oracle Free container
└── factories/     # polyfactory factories for synthetic data
static/dev/        # HTML test page — served only when ENV != production
scripts/           # Seed data, DB reset, ad-hoc utilities
```

## Domain Concepts

| Term                | Meaning                                                                                          |
| ------------------- | ------------------------------------------------------------------------------------------------ |
| Tier code           | `{M\|F}-{AGE_BRACKET}-{LEVEL}` e.g. `F-30-39-INT`. Derived from profile — never stored as source |
| Active minute       | A minute with heart rate ≥ 50% max; intensity bucket determined by HR zone                       |
| Points earned       | Total accumulated (used for ranking)                                                             |
| Point balance       | Spendable current — can go down via ticket purchase                                              |
| Ticket number       | Sequential integer assigned at drawing close; the snapshot is immutable                          |
| Drawing snapshot    | Frozen ticket set captured at `ticket_sales_close`; CSPRNG selects from this snapshot only       |
| Fulfillment         | Post-win workflow: `pending → notified → address_confirmed → shipped → delivered`                |

## Key Business Rules

- **Daily point cap: 1,000 pts/user** — enforced in points service, not just UI
- **18+ only** — DOB checked at registration; ineligible states (NY, FL, RI for MVP) rejected
- **Tier code is computed**, not stored as source of truth — recalculate whenever age bracket, sex, or fitness level changes
- **Drawings are immutable after execution** — winners cannot be changed; audit trail required
- **Points never convert to cash** and never expire; non-transferable between users
- **OAuth tokens are encrypted at rest** (AES-256-GCM with OCI Vault-managed keys)
- **Ticket purchase must be atomic**: point debit + ticket insert must be in one DB transaction with optimistic locking on balance
- **Drawing execution uses OCI Vault CSPRNG**, with seed value recorded for audit — never `random` or `secrets`

## Entities

- **User**: Email auth, role (`user|premium|admin`), point balance, account status
- **Profile**: DOB, state, sex, age bracket, fitness level → drives tier code
- **TrackerConnection**: OAuth tokens for one provider per user; encrypted at rest
- **Activity**: Normalized fitness event with type/intensity/metrics + points awarded
- **PointTransaction**: Ledger entry — `earn|spend|adjust|expire` with balance_after
- **Drawing**: Sweepstakes event (daily/weekly/monthly/annual) with status machine
- **Ticket**: Drawing entry purchased with points; ticket_number assigned at close
- **Prize**: 1+ per drawing with rank, value, fulfillment type
- **PrizeFulfillment**: Post-win shipping state machine
- **Sponsor**: Prize provider; admin-managed

## API Patterns

- Errors follow **RFC 7807** (`application/problem+json` with `type`, `title`, `detail`, `instance`)
- All list endpoints support `?page=N&limit=M` (limit ≤ 100); response includes `pagination` object
- Camel-case JSON externally, snake_case internally — Pydantic aliases handle conversion
- Timestamps in ISO 8601 UTC; drawing times in `America/New_York` (sweepstakes legal venue)
- Pagination uses page/limit, not cursor — leaderboard rank requires stable offset

## Commands

```bash
make setup        # First-time: create venv, install deps, pull Oracle Free image
make dev          # Start docker-compose (Oracle Free + Redis) + FastAPI hot reload
make db-migrate   # Run pending migrations against the running DB
make db-seed      # Populate synthetic users, activities, drawings, tickets
make db-reset     # Drop + migrate + seed (destructive — dev only)
make test         # Run pytest with coverage gate
make lint         # ruff + black --check + mypy
make test-page    # Open the dev test harness at http://localhost:8000/dev
```

## Gotchas

- **Oracle Free container is slow to boot** (~60s on first start). `make dev` polls `lsnrctl status` before running migrations; don't bypass this
- **`python-oracledb` thin mode** can't use Wallet auth — local dev uses standard user/pass; production uses Wallet (set `ORACLE_WALLET_DIR`)
- **Tier codes change** when a user updates birth date or fitness level. Use the `services.tiers.recalculate()` helper; never set `tier_code` directly
- **Daily point cap is timezone-sensitive** — "day" boundary is `America/New_York` midnight, not UTC. Use `services.points.day_boundary()`
- **Ticket purchase races**: two concurrent purchases of the user's last 100 points can both succeed under naive code. Use `UPDATE ... WHERE point_balance = :expected` and retry on zero rows affected
- **Drawing execution is one-shot**: idempotency key required — re-running a completed drawing must be a no-op
- **HTML test page is dev-only**: gated by `ENV=development` env var; the route returns 404 in staging/production
- **JSON Duality Views** require the underlying tables to have functional indexes on queried JSON paths or queries fall back to full scans
- **Heart rate zones depend on user age** — `max_hr = 220 - age`. Re-derive on profile updates; do not cache stale intensity buckets

## Constraints

- MVP: US only, 18+, excludes **NY, FL, RI** (sweepstakes legal compliance)
- Sync latency: ≤ 15 min (batch worker)
- Drawing execution: < 30s, must complete deterministically given snapshot + seed
- Daily point cap: 1,000 pts/user/day
- Premium subscription, native iOS/Android apps, real-time leaderboards, social login: **deferred to v1.1+**

## References

- PRD: `docs/FitTrack-PRD-v1.0.md`
- Implementation plan: `IMPLEMENTATION_PLAN.md`
- Checklist: `IMPLEMENTATION_CHECKLIST.md`
- ADRs: `docs/adr/`
- API docs (when running): `http://localhost:8000/docs`
- Dev test page (when running): `http://localhost:8000/dev`
