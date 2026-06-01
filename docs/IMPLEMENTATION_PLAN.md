# Implementation Plan: FitTrack

## Executive Summary

FitTrack is a gamified fitness platform that converts physical activity from connected trackers (Apple Health, Google Fit, Fitbit) into points users spend on sweepstakes tickets. The MVP targets US users 18+ in sweepstakes-compliant states, runs on Oracle Cloud Infrastructure using Oracle Autonomous JSON Database with JSON Duality Views, and exposes a FastAPI backend behind a responsive React web frontend.

This plan delivers the MVP across **10 sequential checkpoints**, each producing a demonstrable, integrated increment. Checkpoint 1 establishes the foundation — Oracle 23ai locally via Docker, all entity models, full CRUD APIs, synthetic data generators, and an HTML test page — so that every subsequent checkpoint extends working software rather than building atop scaffolding. Authentication is layered in CP2, then the core domain (sync, points, tiers, leaderboards) is built in CP3–CP4, the sweepstakes engine in CP5–CP6, real tracker integrations in CP7, the React user and admin frontends in CP8–CP9, and production hardening/deployment in CP10.

**Key technical decisions** (rationale captured in `CLAUDE.md`): no ORM — Oracle JSON Duality Views are the abstraction; CSPRNG via OCI Vault is the only acceptable RNG for drawings; point balance updates use optimistic locking; OAuth tokens are encrypted at rest with AES-256-GCM. **Major risks** are concentrated around drawing integrity (mitigated by CSPRNG + immutable snapshots + audit trail) and tracker-API instability (mitigated by an abstraction layer + mock providers used through CP6).

## Checkpoint Overview

| CP  | Title                                          | Dependencies | Demo                                                          |
| --- | ---------------------------------------------- | ------------ | ------------------------------------------------------------- |
| 1   | Foundation: Data Layer, CRUD APIs, Test Page   | None         | Seed DB; exercise every entity from the HTML test page         |
| 2   | Authentication & Authorization                 | CP1          | Register, verify email, log in, hit protected endpoints       |
| 3   | Activity Sync & Points Engine                  | CP1, CP2     | Mock-synced activities produce correct points with daily cap  |
| 4   | Tier Assignment & Leaderboards                 | CP3          | Users land in correct tiers; leaderboards rank within tier    |
| 5   | Sweepstakes Engine: Drawings & Tickets         | CP3          | Buy tickets, execute drawing with CSPRNG, view results        |
| 6   | Prize Fulfillment Workflow                     | CP5          | Winner notified → address confirmed → shipped → delivered     |
| 7   | Real Tracker Integrations (Fitbit, GFit, Apple)| CP3          | Live OAuth + 15-min sync from real providers                  |
| 8   | React User Web App                             | CP2–CP6      | Mobile-responsive dashboard, activity, leaderboards, drawings |
| 9   | React Admin Web App                            | CP5, CP6     | Admin manages drawings, sponsors, fulfillment, users          |
| 10  | Production Readiness: OCI, Observability, Sec  | All prior    | Blue-green deploy to staging; SLO dashboards live             |

---

## Detailed Checkpoint Specifications

---

## Checkpoint 1: Foundation — Data Layer, CRUD APIs, and Test Page

### Objective

Establish a production-shaped Python/FastAPI project with Oracle 23ai locally, a complete data layer for every PRD entity, full CRUD endpoints with pagination and RFC 7807 errors, synthetic data generators covering every role and workflow scenario, and an HTML test harness that validates the API end to end. Result: a developer can `make setup && make dev && make db-seed` in under 15 minutes and explore the entire data model from a browser.

### Prerequisites

- [x] Docker Desktop installed
- [x] Python 3.12+ available
- [x] PRD reviewed and approved

### Deliverables

#### Infrastructure

| Item                       | Path                                   | Description                                                       |
| -------------------------- | -------------------------------------- | ----------------------------------------------------------------- |
| Docker Compose stack       | `docker/docker-compose.yml`            | Oracle Free 23ai + Redis (placeholder, used CP4+)                  |
| Oracle init script         | `docker/oracle-init/01-create-app.sql` | Create `fittrack` schema, app user, grants                        |
| Dockerfile (API)           | `docker/Dockerfile`                    | Multi-stage build (slim runtime image)                            |
| Makefile                   | `Makefile`                             | `setup`, `dev`, `db-migrate`, `db-seed`, `db-reset`, `test`, `lint` |
| pyproject.toml             | `pyproject.toml`                       | Dependencies, ruff, black, mypy, pytest config                    |
| Environment template       | `.env.example`                         | Documents every required env var; copied to `.env` by `make setup` |
| GitHub Actions CI          | `.github/workflows/ci.yml`             | Lint (ruff + black) + type (mypy) + pytest with Oracle service    |
| pre-commit config          | `.pre-commit-config.yaml`              | ruff, black, mypy, secrets scan                                   |

#### Code Deliverables

| Component             | Path                                            | Description                                                     |
| --------------------- | ----------------------------------------------- | --------------------------------------------------------------- |
| App entrypoint        | `src/fittrack/main.py`                          | FastAPI app, lifespan, router registration                      |
| Config                | `src/fittrack/config.py`                        | Pydantic Settings; loads from env                               |
| DB connection pool    | `src/fittrack/database/connection.py`           | `python-oracledb` async pool with health check                  |
| Migrations runner     | `src/fittrack/database/migrations/__init__.py`  | Simple forward-only SQL migration runner                        |
| Migration 0001        | `src/fittrack/database/migrations/0001_core.sql`| All 10 core tables + indexes from PRD §7                         |
| Migration 0002        | `src/fittrack/database/migrations/0002_views.sql`| JSON Duality Views (user_profile_dv, drawing_dv, activity_dv)   |
| Repositories          | `src/fittrack/database/repositories/*.py`       | CRUD for each entity (users, profiles, connections, activities, point_transactions, drawings, tickets, prizes, fulfillments, sponsors) |
| Domain enums          | `src/fittrack/domain/enums.py`                  | `UserStatus`, `Role`, `Provider`, `ActivityType`, `Intensity`, `DrawingType`, `DrawingStatus`, `FulfillmentStatus` |
| Tier code helper      | `src/fittrack/domain/tier.py`                   | Pure function: `compute_tier_code(sex, age_bracket, level)`     |
| API routers           | `src/fittrack/api/v1/routes/*.py`               | One module per entity with list/get/create/update/delete         |
| Schemas               | `src/fittrack/api/v1/schemas/*.py`              | Pydantic models with camelCase aliases                          |
| Error handlers        | `src/fittrack/api/errors.py`                    | RFC 7807 `application/problem+json` responses                   |
| Pagination helper     | `src/fittrack/api/pagination.py`                | `Page`, `Paginated[T]` generic                                  |
| Health endpoints      | `src/fittrack/api/v1/routes/health.py`          | `/healthz` (liveness), `/readyz` (DB + Redis check)             |
| Dev test page route   | `src/fittrack/api/dev.py`                       | Serves static HTML test page when `ENV=development`             |

#### Database Deliverables

| Item                               | Description                                                                 |
| ---------------------------------- | --------------------------------------------------------------------------- |
| Migration 0001: core tables        | All 10 entity tables, constraints, indexes per PRD §7.2                     |
| Migration 0002: JSON Duality Views | `user_profile_dv`, `drawing_dv`, `activity_summary_dv`                      |
| Migration 0003: audit columns      | `created_by`, `updated_by`, `version` (optimistic locking) where needed     |

#### Synthetic Data Deliverables

| Item                          | Path                                | Description                                                                |
| ----------------------------- | ----------------------------------- | -------------------------------------------------------------------------- |
| Factory base                  | `tests/factories/base.py`           | Polyfactory + Faker setup with deterministic seed for reproducibility       |
| Entity factories              | `tests/factories/*.py`              | One factory per entity producing valid Pydantic models                     |
| Seed script                   | `scripts/seed_data.py`              | Generates the dataset described below; idempotent via deterministic IDs    |
| Reset script                  | `scripts/reset_db.py`               | Drops user data tables, re-runs migrations, re-seeds                       |

**Seed dataset (`make db-seed`):**
- 5 admin users (across diverse profiles)
- 5 premium users
- **300 regular users** — 10 per each of 30 tier combinations
- Realistic activity history: 60 days × ~3 activities/day for ~50 users, sparser for the rest
- Point transactions matching activity history
- 5 sponsors with logos (placeholder URLs)
- 30 drawings: 14 daily (past + open + scheduled), 8 weekly, 4 monthly, 2 annual, 2 completed-with-winners
- ~5,000 tickets distributed across open drawings
- 8 prize fulfillment records in various states (`pending`, `notified`, `address_confirmed`, `shipped`, `delivered`)

#### API Endpoints

All endpoints are unauthenticated in CP1 (auth lands in CP2). Every list endpoint supports `?page=&limit=&sort=`. All write endpoints return the created/updated resource.

| Method | Path                              | Description                                  |
| ------ | --------------------------------- | -------------------------------------------- |
| GET    | `/healthz`                        | Liveness                                     |
| GET    | `/readyz`                         | DB + Redis readiness                         |
| GET    | `/api/v1/users`                   | List users (filter: status, role)            |
| GET    | `/api/v1/users/{id}`              | Get user                                     |
| POST   | `/api/v1/users`                   | Create user (no password yet — CP2 wires that) |
| PATCH  | `/api/v1/users/{id}`              | Update                                       |
| DELETE | `/api/v1/users/{id}`              | Soft delete (status=banned)                  |
| GET    | `/api/v1/users/{id}/profile`      | Get profile via Duality View                 |
| PUT    | `/api/v1/users/{id}/profile`      | Upsert profile (recomputes tier code)        |
| GET/POST/PATCH/DELETE | `/api/v1/connections`        | Tracker connections (no real OAuth yet)      |
| GET    | `/api/v1/activities`              | List activities (filters: userId, type, dateRange) |
| POST   | `/api/v1/activities`              | Manual create (test data; gated to dev/admin in CP2) |
| GET    | `/api/v1/point-transactions`      | List with filters                            |
| GET/POST/PATCH/DELETE | `/api/v1/drawings`           | Drawings CRUD                                 |
| GET/POST/DELETE | `/api/v1/tickets`                  | Tickets CRUD                                  |
| GET/POST/PATCH/DELETE | `/api/v1/prizes`             | Prizes CRUD                                   |
| GET/PATCH | `/api/v1/fulfillments`         | Fulfillment records                          |
| GET/POST/PATCH/DELETE | `/api/v1/sponsors`           | Sponsors                                      |
| GET    | `/dev`                            | HTML test page (404 outside development)     |
| POST   | `/dev/seed`                       | Trigger seed script (dev only)               |
| POST   | `/dev/reset`                      | Trigger DB reset (dev only)                  |

#### HTML Test Page (`static/dev/test_page.html`)

A single-file static HTML page (vanilla JS + Fetch API) served at `/dev`. It provides:
- A navigation sidebar listing every entity
- For each entity: a paginated table viewer, a "View JSON" panel, a create form, an edit form, and a delete confirmation
- A top bar with **Seed DB** and **Reset DB** buttons
- A live log pane showing every request/response with status + timing
- A "Sample reports" panel showing seeded data summaries: user count by tier, drawings by status, activity histogram

#### Test Deliverables

| Test Suite             | Path                                        | Coverage Target |
| ---------------------- | ------------------------------------------- | --------------- |
| Domain unit tests      | `tests/unit/test_tier.py`, `test_enums.py`  | >95%            |
| Repository integration | `tests/integration/test_repositories.py`    | >90%            |
| API endpoint tests     | `tests/integration/test_api_*.py`           | >85%            |
| Factory validation     | `tests/unit/test_factories.py`              | 100% of factories |
| Migration tests        | `tests/integration/test_migrations.py`      | Forward + idempotency |

#### Documentation

| Item                  | Path                              | Description                                                       |
| --------------------- | --------------------------------- | ----------------------------------------------------------------- |
| README                | `README.md`                       | <15 minute setup, architecture overview, links                    |
| CLAUDE.md             | `CLAUDE.md`                       | AI context (already created)                                      |
| ADR-0001              | `docs/adr/0001-oracle-json.md`    | Why Oracle JSON Duality Views vs. ORM                             |
| ADR-0002              | `docs/adr/0002-fastapi.md`        | FastAPI vs. Flask/Django choice                                   |
| ADR-0003              | `docs/adr/0003-no-orm.md`         | No ORM rationale                                                  |
| ADR-0004              | `docs/adr/0004-tier-encoding.md`  | Tier code derivation strategy                                     |

### Acceptance Criteria

```gherkin
Feature: Foundation environment

  Scenario: Fresh-clone setup completes in under 15 minutes
    Given a developer clones the repo on a clean machine
    When they run `make setup && make dev`
    Then the Oracle container reaches "READY" state
    And the FastAPI app responds 200 on /healthz within 15 minutes

  Scenario: Database seeding produces complete realistic data
    Given a fresh database
    When `make db-seed` runs
    Then there are exactly 310 users (5 admin + 5 premium + 300 regular)
    And every one of the 30 tier combinations has at least 10 users
    And there are 30 drawings spanning every type and status
    And the seed completes in under 60 seconds

  Scenario: Test page exercises every CRUD endpoint
    Given the dev server is running with ENV=development
    When a user visits http://localhost:8000/dev
    Then they see a panel for each of the 10 entities
    And clicking "Create" → "Save" on each entity creates a record
    And clicking "Reset DB" returns the database to seeded baseline

  Scenario: Errors follow RFC 7807
    Given the API is running
    When any 4xx or 5xx response is returned
    Then the Content-Type is "application/problem+json"
    And the body contains "type", "title", "status", "detail"

  Scenario: Test page is disabled in production
    Given ENV=production
    When a user requests GET /dev
    Then the response is 404
```

### Security Considerations

- `.env` is gitignored; `.env.example` documents every var with placeholder values
- Secrets scanner runs in pre-commit and CI (gitleaks)
- Test page routes return 404 outside `development` env
- DB user `fittrack_app` has only `CONNECT`, `RESOURCE` + table privileges — no DBA
- No password handling in CP1 — `password_hash` column exists but is null/test-only
- All HTTP responses include security headers via middleware (HSTS, X-Content-Type-Options, X-Frame-Options=DENY)

### Definition of Done

- [ ] `make setup && make dev` works from a fresh clone in <15 minutes
- [ ] `make db-seed` populates the full dataset deterministically
- [ ] All CRUD endpoints functional for all 10 entities
- [ ] HTML test page exercises every endpoint
- [ ] `make test` passes with coverage gates met (unit >90%, integration >85%)
- [ ] GitHub Actions CI green on `main`
- [ ] ADRs 0001–0004 written
- [ ] README setup walkthrough verified by a second developer

---

## Checkpoint 2: Authentication & Authorization

### Objective

Layer secure JWT-based authentication, email verification, password reset, and RBAC onto the CP1 foundation. After CP2, every endpoint built going forward is protected by default, and the test page authenticates as different roles to demonstrate access control.

### Prerequisites

- [x] CP1 completed

### Deliverables

#### Code

| Component                | Path                                          | Description                                              |
| ------------------------ | --------------------------------------------- | -------------------------------------------------------- |
| Password hashing         | `src/fittrack/services/auth/password.py`      | Argon2id (argon2-cffi); strength validation (12+ chars)   |
| JWT service              | `src/fittrack/services/auth/tokens.py`        | RS256 sign/verify; access (1h) + refresh (30d)           |
| Key management           | `src/fittrack/services/auth/keys.py`          | Load RSA keypair from env (dev) or OCI Vault (prod)      |
| Auth dependencies        | `src/fittrack/api/v1/deps.py`                 | `current_user`, `require_role(...)`, `require_active`    |
| Email verification       | `src/fittrack/services/auth/verification.py`  | Token generation + redemption; mock SMTP in dev          |
| Password reset           | `src/fittrack/services/auth/reset.py`         | Token + email flow                                       |
| Rate limiter             | `src/fittrack/api/middleware/rate_limit.py`   | slowapi backed by Redis (CP4 wires real Redis; in-memory for now) |
| Account lockout          | `src/fittrack/services/auth/lockout.py`       | 5 failed attempts → 15min lock with progressive backoff   |
| Auth routes              | `src/fittrack/api/v1/routes/auth.py`          | `/auth/register`, `/login`, `/refresh`, `/verify-email`, `/forgot-password`, `/reset-password`, `/logout` |
| State eligibility        | `src/fittrack/domain/states.py`               | Eligible states list; rejects NY, FL, RI                 |
| Age check                | `src/fittrack/domain/age.py`                  | 18+ validation from DOB                                  |
| Audit log                | `src/fittrack/services/audit.py`              | Auth-events table append-only                            |

#### Database

| Migration                              | Description                                            |
| -------------------------------------- | ------------------------------------------------------ |
| 0004_auth_tables                       | `refresh_tokens`, `email_verifications`, `password_resets`, `auth_events` (audit), `account_lockouts` |

#### API Endpoints (additions)

| Method | Path                          | Auth | Description                                  |
| ------ | ----------------------------- | ---- | -------------------------------------------- |
| POST   | `/api/v1/auth/register`       | None | Create user with password, send verification |
| POST   | `/api/v1/auth/login`          | None | Returns access + refresh tokens              |
| POST   | `/api/v1/auth/refresh`        | RT   | New access token                             |
| POST   | `/api/v1/auth/verify-email`   | None | Redeem verification token                    |
| POST   | `/api/v1/auth/forgot-password`| None | Issue reset token                            |
| POST   | `/api/v1/auth/reset-password` | None | Redeem reset token                           |
| POST   | `/api/v1/auth/logout`         | AT   | Revoke refresh token                         |
| GET    | `/api/v1/users/me`            | AT   | Current user                                 |

All CP1 endpoints are now wrapped with auth dependencies; `/users` listing requires admin.

#### HTML Test Page

- Login form (3 prefilled buttons: user, premium, admin)
- "Logged in as" indicator
- All API calls now send the bearer token
- 401/403 responses surfaced in the log pane

#### Tests

| Suite                         | Path                                       | Target |
| ----------------------------- | ------------------------------------------ | ------ |
| Auth unit tests               | `tests/unit/test_password.py`, `test_tokens.py` | >95%   |
| Auth integration              | `tests/integration/test_auth_flows.py`     | >90%   |
| RBAC enforcement              | `tests/integration/test_rbac.py`           | 100% of protected endpoints |

### Acceptance Criteria

```gherkin
Feature: Registration with age and state eligibility

  Scenario: Underage registration is rejected
    When a user submits dateOfBirth that makes them 17
    Then the response is 400 with detail "Must be 18 or older"

  Scenario: Ineligible state is rejected
    When a user submits stateOfResidence "NY"
    Then the response is 400 with detail referencing sweepstakes eligibility

  Scenario: Account lockout after 5 failed logins
    When a user fails login 5 times within 15 minutes
    Then the 6th attempt returns 423 with retry-after header

  Scenario: Admin endpoints reject non-admins
    Given a user authenticated as role "user"
    When they GET /api/v1/users
    Then the response is 403
```

### Security Considerations

- Argon2id for password hashing (NIST recommendation)
- JWT signed with RS256; private key never leaves the server
- Refresh tokens stored hashed; rotated on every refresh
- Failed login attempts logged with IP for security audit
- Password reset tokens single-use, 1-hour expiry
- Email verification required before `status` flips from `pending` to `active`

### Definition of Done

- [ ] All auth endpoints implemented and tested
- [ ] Every existing endpoint either auth-protected or explicitly public
- [ ] Rate limiting active on auth routes
- [ ] Test page demonstrates user/premium/admin role differences
- [ ] Coverage gates met

---

## Checkpoint 3: Activity Sync & Points Engine

### Objective

Implement the points calculation engine, activity ingestion pipeline (with mock providers), daily cap enforcement, and anti-gaming measures. After CP3, seeded users earn correct points from synced activities, the ledger is consistent, and the activity summary endpoints feed dashboards.

### Prerequisites

- [x] CP1, CP2 completed

### Deliverables

#### Code

| Component                  | Path                                                | Description                                                     |
| -------------------------- | --------------------------------------------------- | --------------------------------------------------------------- |
| Points calculator          | `src/fittrack/services/points/calculator.py`        | Pure function: activity → points; honors PRD §4.3.1 rate table  |
| Daily cap enforcer         | `src/fittrack/services/points/cap.py`               | 1,000 pts/user/day in `America/New_York` TZ                     |
| Points service             | `src/fittrack/services/points/service.py`           | Atomic: insert activity → compute points → insert transaction → bump balance with optimistic locking |
| Activity normalizer        | `src/fittrack/services/sync/normalizer.py`          | Provider-specific raw → internal `Activity` schema              |
| Sync provider interface    | `src/fittrack/services/sync/provider.py`            | Abstract `SyncProvider` with `fetch_since(user, last_sync)`     |
| Mock provider              | `src/fittrack/services/sync/mock_provider.py`       | Generates plausible activities for CP3 demo                     |
| Deduplicator               | `src/fittrack/services/sync/dedup.py`               | Per PRD §4.2.3: primary tracker → most metrics → first received |
| Sync worker                | `src/fittrack/workers/sync_worker.py`               | APScheduler job, 15-min cadence (dev); production wires OCI Queue |
| Anti-gaming detector       | `src/fittrack/services/points/anti_gaming.py`       | Flags accounts >3σ from tier average; queues for admin review   |
| Heart-rate zone calculator | `src/fittrack/domain/heart_rate.py`                 | Max HR from age; intensity bucket from HR sample                |

#### Database

| Migration             | Description                                                        |
| --------------------- | ------------------------------------------------------------------ |
| 0005_anti_gaming      | `flagged_accounts`, `manual_review_queue` tables                   |
| 0006_sync_state       | Adds `sync_state` column (per-provider checkpoint) to connections  |

#### API Endpoints (additions)

| Method | Path                                | Description                              |
| ------ | ----------------------------------- | ---------------------------------------- |
| GET    | `/api/v1/activities/summary`        | Dashboard summary (today/week/month)     |
| POST   | `/api/v1/connections/{provider}/sync` | Force sync (rate-limited)                |
| GET    | `/api/v1/points/balance`            | Current balance                          |
| GET    | `/api/v1/points/transactions`       | Ledger with filters                      |

#### Tests

| Suite                         | Path                                       | Target |
| ----------------------------- | ------------------------------------------ | ------ |
| Points calculator (hypothesis)| `tests/unit/test_points_calculator.py`     | Property-based: cap never exceeded, sum of components matches |
| Points service (integration)  | `tests/integration/test_points_service.py` | Concurrent purchase race test            |
| Sync worker                   | `tests/integration/test_sync_worker.py`    | Mock provider produces expected ledger entries |
| Dedup                         | `tests/unit/test_dedup.py`                 | Multi-tracker overlap scenarios          |

### Acceptance Criteria

```gherkin
Feature: Points are awarded correctly

  Scenario: Vigorous workout earns base + bonus
    Given a user completes a 45-minute vigorous workout
    When the sync worker processes the activity
    Then the user earns 45×3 + 50 = 185 points
    And a corresponding point_transaction is recorded

  Scenario: Daily cap is enforced
    Given a user has already earned 950 points today
    When they sync a workout worth 100 points
    Then they earn exactly 50 additional points
    And the rest is silently dropped (logged for audit)

  Scenario: Concurrent ticket purchases respect balance
    Given a user has 100 points
    When two ticket purchases for 100 points each execute concurrently
    Then exactly one succeeds and one returns 409 Conflict
```

### Security Considerations

- Anti-gaming detection runs every sync; flagged users cannot purchase tickets until reviewed
- Point adjustments by admin require audit log entry with reason
- Sync forced-refresh endpoint rate-limited (1/min/user)

### Definition of Done

- [ ] Points calculation matches PRD §4.3.1 rate table exactly (verified by property tests)
- [ ] Daily cap enforced
- [ ] Sync worker runs on schedule; failures logged with retry
- [ ] Anti-gaming detector flags outliers
- [ ] All tests pass

---

## Checkpoint 4: Tier Assignment & Leaderboards

### Objective

Compute tier codes for every user, build daily/weekly/monthly/all-time leaderboards per tier, and expose ranking endpoints. Leaderboard reads are cached in Redis sorted sets; writes happen via a worker.

### Prerequisites

- [x] CP1, CP3 completed

### Deliverables

#### Code

| Component                | Path                                        | Description                                                |
| ------------------------ | ------------------------------------------- | ---------------------------------------------------------- |
| Tier service             | `src/fittrack/services/tiers/service.py`    | Compute + persist + recalculate on profile change          |
| Leaderboard service      | `src/fittrack/services/leaderboards/service.py` | Read top-N + user rank ± 10 from Redis sorted set      |
| Leaderboard worker       | `src/fittrack/workers/leaderboard_worker.py`| Rebuilds sorted sets every 15 min from `point_transactions` |
| Period boundaries        | `src/fittrack/services/leaderboards/periods.py` | Daily/weekly/monthly resets in `America/New_York`     |
| Redis client             | `src/fittrack/infra/redis_client.py`        | Async Redis with pool; health check                        |

#### Database

| Migration             | Description                                                      |
| --------------------- | ---------------------------------------------------------------- |
| 0007_leaderboard_audit| `leaderboard_snapshots` for audit (winners-by-period archive)    |

#### API Endpoints

| Method | Path                                    | Description                                |
| ------ | --------------------------------------- | ------------------------------------------ |
| GET    | `/api/v1/leaderboards/{period}`         | Top-N + user ± 10 within tier              |
| GET    | `/api/v1/leaderboards/{period}/tiers`   | All tier codes with population             |
| GET    | `/api/v1/users/me/rank`                 | Current user's rank across all periods      |

### Acceptance Criteria

```gherkin
Feature: Leaderboards respect tiers and periods

  Scenario: User sees only their tier's leaderboard
    Given a user in tier F-30-39-INT
    When they GET /api/v1/leaderboards/weekly
    Then all returned users are also in F-30-39-INT
    And user's own rank is included

  Scenario: Leaderboard resets at period boundary
    Given the weekly leaderboard has data Sunday 11:59 PM EST
    When the clock crosses Monday 00:00 EST
    Then the weekly board shows everyone at 0 points
    And the previous week's data is in leaderboard_snapshots
```

### Definition of Done

- [ ] All 30 tiers populated; users in correct tier
- [ ] Leaderboards return correct rankings within 15 minutes of activity
- [ ] Period resets verified at boundary
- [ ] Tier recalculation on profile change verified

---

## Checkpoint 5: Sweepstakes Engine — Drawings & Tickets

### Objective

Implement the drawing lifecycle: admin creates drawings, users purchase tickets atomically, drawings execute via OCI Vault CSPRNG (with a deterministic local-dev fallback for tests), and results are immutable and auditable.

### Prerequisites

- [x] CP1, CP3 completed

### Deliverables

#### Code

| Component                | Path                                                | Description                                                   |
| ------------------------ | --------------------------------------------------- | ------------------------------------------------------------- |
| Drawing service          | `src/fittrack/services/drawings/service.py`         | Lifecycle: draft → scheduled → open → closed → completed      |
| Ticket purchase          | `src/fittrack/services/drawings/purchase.py`        | Atomic: debit points + insert tickets with optimistic locking |
| Drawing executor         | `src/fittrack/services/drawings/executor.py`        | Snapshot tickets → assign numbers → CSPRNG select → record    |
| CSPRNG client            | `src/fittrack/services/drawings/csprng.py`          | OCI Vault for prod; `secrets.SystemRandom` for dev (logged)   |
| Snapshot store           | `src/fittrack/services/drawings/snapshot.py`        | Immutable ticket snapshot at sales close                      |
| Drawing scheduler worker | `src/fittrack/workers/drawing_worker.py`            | Closes sales at T-5; executes at T-0                          |
| Eligibility check        | `src/fittrack/services/drawings/eligibility.py`     | `min_account_age_days`, user role, status                     |

#### Database

| Migration             | Description                                                       |
| --------------------- | ----------------------------------------------------------------- |
| 0008_drawing_audit    | `drawing_audit_log`, `drawing_snapshots` immutable tables         |

#### API Endpoints

| Method | Path                                       | Auth        | Description                          |
| ------ | ------------------------------------------ | ----------- | ------------------------------------ |
| GET    | `/api/v1/drawings`                         | user        | List open/recent/upcoming            |
| GET    | `/api/v1/drawings/{id}`                    | user        | Detail with user's ticket count      |
| POST   | `/api/v1/drawings/{id}/tickets`            | user        | Buy tickets                          |
| GET    | `/api/v1/drawings/{id}/results`            | user        | Post-execution results               |
| POST   | `/api/v1/admin/drawings`                   | admin       | Create                               |
| PUT    | `/api/v1/admin/drawings/{id}`              | admin       | Update (only `draft` or `scheduled`) |
| POST   | `/api/v1/admin/drawings/{id}/execute`      | admin + MFA | Force-execute                        |
| DELETE | `/api/v1/admin/drawings/{id}`              | admin       | Cancel (refunds tickets)             |

### Acceptance Criteria

```gherkin
Feature: Drawing execution is deterministic and auditable

  Scenario: Drawing produces single winner from CSPRNG
    Given a drawing with 4,521 tickets
    When the drawing executes
    Then exactly 1 winner is selected (rank 1)
    And the random seed is recorded in drawing_audit_log
    And the result is identical when replayed with the same seed (deterministic test)

  Scenario: Ticket purchase is atomic
    Given a user with 250 points
    When they purchase 3 tickets at 100 points each
    Then 0 tickets are created and 250 points remain (insufficient funds)

  Scenario: Drawing is immutable after execution
    Given a completed drawing
    When an admin attempts to update it
    Then the response is 409 Conflict
```

### Security Considerations

- Admin drawing execution requires MFA (CP10 wires real MFA; CP5 stubs with admin-role + audit)
- All admin actions logged immutably
- CSPRNG seed sourced from OCI Vault in prod; never `random.random()`

### Definition of Done

- [ ] Drawings progress through state machine correctly
- [ ] Ticket purchases atomic under concurrency (load tested)
- [ ] CSPRNG path tested; deterministic-mode replays match
- [ ] Audit log immutable (DB-level CHECK or trigger)

---

## Checkpoint 6: Prize Fulfillment Workflow

### Objective

After a drawing completes, winners are notified, provide shipping info, admins ship and confirm delivery. Includes the forfeit/timeout path and re-drawing logic.

### Prerequisites

- [x] CP5 completed

### Deliverables

#### Code

| Component               | Path                                              | Description                                              |
| ----------------------- | ------------------------------------------------- | -------------------------------------------------------- |
| Fulfillment service     | `src/fittrack/services/fulfillment/service.py`    | State machine transitions with guards                    |
| Notification dispatcher | `src/fittrack/services/notifications/dispatcher.py`| Email (SMTP mock dev / OCI Email prod) + in-app          |
| Address validator       | `src/fittrack/services/fulfillment/address.py`    | USPS-style validation (mock in dev; real provider in v1.1) |
| Forfeit worker          | `src/fittrack/workers/forfeit_worker.py`          | 7-day warning, 14-day forfeit                            |

#### Database

| Migration             | Description                                                |
| --------------------- | ---------------------------------------------------------- |
| 0009_notifications    | `notifications` table for in-app inbox                     |

#### API Endpoints

| Method | Path                                                  | Auth   | Description                            |
| ------ | ----------------------------------------------------- | ------ | -------------------------------------- |
| GET    | `/api/v1/users/me/fulfillments`                       | user   | My prizes                              |
| POST   | `/api/v1/fulfillments/{id}/confirm-address`           | user   | Submit shipping address                |
| GET    | `/api/v1/users/me/notifications`                      | user   | In-app notifications                   |
| PATCH  | `/api/v1/users/me/notifications/{id}`                 | user   | Mark read                              |
| GET    | `/api/v1/admin/fulfillments`                          | admin  | Pending fulfillments queue             |
| POST   | `/api/v1/admin/fulfillments/{id}/ship`                | admin  | Mark shipped with tracking number      |
| POST   | `/api/v1/admin/fulfillments/{id}/deliver`             | admin  | Mark delivered                         |
| POST   | `/api/v1/admin/fulfillments/{id}/forfeit`             | admin  | Force forfeit (with reason)            |

### Acceptance Criteria

```gherkin
Feature: Fulfillment state machine

  Scenario: Winner notified, confirms address, prize ships
    Given a user wins a drawing
    Then they receive email + in-app notification within 5 minutes
    When they submit their address
    Then the fulfillment transitions to ADDRESS_CONFIRMED
    When admin enters tracking number
    Then fulfillment transitions to SHIPPED and user is notified
    When delivery confirmed
    Then fulfillment is DELIVERED

  Scenario: Unclaimed prize forfeits after 14 days
    Given a winner has not confirmed address for 7 days
    Then they receive a forfeit-warning notification
    And after 14 days the fulfillment is FORFEITED
    And the prize is queued for re-drawing or sponsor return
```

### Definition of Done

- [ ] All state transitions enforced (no skipping states)
- [ ] Notifications delivered via both channels
- [ ] Forfeit worker tested with frozen-clock fixtures
- [ ] Admin can override states with audit entry

---

## Checkpoint 7: Real Tracker Integrations

### Objective

Replace mock sync providers with real Fitbit, Google Fit, and Apple Health (via Terra API placeholder) integrations. Includes OAuth flows, encrypted token storage, rate limit handling, and circuit breakers.

### Prerequisites

- [x] CP3 completed
- [x] Fitbit developer account approved
- [x] Google Fit API enabled
- [x] Apple Health aggregator account (Terra API) provisioned

### Deliverables

#### Code

| Component               | Path                                                | Description                                            |
| ----------------------- | --------------------------------------------------- | ------------------------------------------------------ |
| OAuth abstraction       | `src/fittrack/services/sync/oauth_base.py`          | Common OAuth 2.0 flow + state CSRF protection          |
| Fitbit provider         | `src/fittrack/services/sync/fitbit.py`              | Fitbit Web API impl                                    |
| Google Fit provider     | `src/fittrack/services/sync/google_fit.py`          | Google Fit REST API impl                               |
| Apple Health provider   | `src/fittrack/services/sync/apple_health.py`        | Terra API integration                                  |
| Token encryption        | `src/fittrack/services/crypto/token_cipher.py`      | AES-256-GCM with OCI Vault-managed DEK                 |
| Rate limit guard        | `src/fittrack/services/sync/rate_limiter.py`        | Per-provider per-user token bucket                     |
| Circuit breaker         | `src/fittrack/services/sync/circuit_breaker.py`     | Open after N consecutive failures                      |

#### API Endpoints

| Method | Path                                            | Description                              |
| ------ | ----------------------------------------------- | ---------------------------------------- |
| POST   | `/api/v1/connections/{provider}/initiate`       | Return OAuth authorization URL           |
| POST   | `/api/v1/connections/{provider}/callback`       | Complete OAuth flow with code            |
| DELETE | `/api/v1/connections/{provider}`                | Disconnect                               |

### Acceptance Criteria

```gherkin
Feature: Real tracker connections

  Scenario: User connects Fitbit
    When a user completes the Fitbit OAuth flow
    Then their access + refresh tokens are stored encrypted
    And the next sync cycle imports their last 30 days of activities

  Scenario: Token refresh on expiration
    Given a user's access token has expired
    When the sync worker attempts to fetch data
    Then it refreshes the token before retrying
    And updates the stored encrypted token

  Scenario: Rate limit triggers backoff
    Given a provider returns 429
    Then the circuit breaker opens
    And retries are scheduled with exponential backoff
```

### Definition of Done

- [ ] All three providers tested against sandbox accounts
- [ ] Tokens encrypted with AES-256-GCM, verified at rest
- [ ] Rate limits respected per provider docs
- [ ] Circuit breaker prevents cascading failures

---

## Checkpoint 8: React User Web Application

### Objective

Replace the HTML test page with a full mobile-first React user-facing web app implementing the screens described in PRD §9. Reuses the existing API; no backend changes.

### Prerequisites

- [x] CP2–CP6 completed

### Deliverables

| Component               | Path                                       | Description                                            |
| ----------------------- | ------------------------------------------ | ------------------------------------------------------ |
| Vite + React 18 app     | `frontend/user/`                           | TS, React Router, TanStack Query                       |
| Design tokens           | `frontend/user/src/design/tokens.ts`       | From PRD §9.3                                          |
| Auth screens            | `register`, `login`, `verify`, `forgot-password` | Per PRD §9                                      |
| Dashboard               | `/`                                        | Per PRD §9.2.1                                         |
| Activity (today/history)| `/activity/*`                              |                                                        |
| Leaderboards            | `/leaderboards/*`                          | Per PRD §9.2.4                                         |
| Drawings + purchase     | `/drawings/*`                              | Per PRD §9.2.2, §9.2.3                                 |
| Profile + connections   | `/profile/*`                               |                                                        |
| Notifications           | In-header dropdown                         |                                                        |
| E2E tests               | `frontend/user/e2e/`                       | Playwright; critical journeys from PRD §11.4           |

### Definition of Done

- [ ] All routes responsive (375px → 1440px)
- [ ] Lighthouse mobile score >85
- [ ] Playwright covers: register → connect → sync → buy ticket → see ranking
- [ ] WCAG 2.1 AA spot-check

---

## Checkpoint 9: React Admin Web Application

### Objective

Build the admin dashboard for managing drawings, sponsors, fulfillment, users, and viewing analytics.

### Prerequisites

- [x] CP5, CP6 completed

### Deliverables

| Component         | Path                  | Description                                           |
| ----------------- | --------------------- | ----------------------------------------------------- |
| Admin app shell   | `frontend/admin/`     | Vite + React; auth-gated to role=admin                |
| Dashboard         | `/`                   | Key metrics: MAU/DAU, drawings status, sync health    |
| Drawings manager  | `/drawings`           | CRUD, schedule, execute (MFA prompt), cancel          |
| Sponsors          | `/sponsors`           | CRUD                                                  |
| Fulfillments      | `/fulfillments`       | Queue, ship, deliver, forfeit                         |
| Users             | `/users`              | Search, suspend, adjust points (audited)              |
| Analytics         | `/analytics`          | Charts (recharts); CSV export                         |

### Definition of Done

- [ ] All admin user stories (US-050 to US-055) demonstrable
- [ ] MFA prompt on drawing execution
- [ ] CSV export verified

---

## Checkpoint 10: Production Readiness

### Objective

Deploy FitTrack to OCI staging with full observability, security hardening, performance baselines, and a documented runbook. Result: production go/no-go meeting.

### Prerequisites

- [x] All prior checkpoints completed

### Deliverables

| Component              | Path / Tool                       | Description                                          |
| ---------------------- | --------------------------------- | ---------------------------------------------------- |
| Terraform              | `infra/terraform/`                | OCI Compute, Autonomous DB, Cache, Queue, Vault, WAF |
| Helm chart             | `infra/helm/fittrack/`            | Kubernetes manifests for OKE                          |
| OCI Vault wiring       | Production secrets                | RSA keypair, DB password, OAuth client secrets       |
| OCI Cache (Redis) prod | Replaces in-memory rate limiter   |                                                      |
| OCI Queue              | Replaces APScheduler              | Sync, drawing, leaderboard, fulfillment jobs         |
| OCI APM tracing        | OpenTelemetry instrumentation     |                                                      |
| Prometheus metrics     | `/metrics` endpoint               | Latency, error rate, queue depth, sync success       |
| Loki + Grafana         | Log aggregation + dashboards      |                                                      |
| Alerting               | PagerDuty integration             | Per PRD §12.4 alert table                            |
| Blue-green deploy      | GitHub Actions workflow           | Auto-rollback on health-check failure                |
| WAF rules              | OCI WAF                           | DDoS, bot mitigation                                 |
| Security headers       | Middleware                        | HSTS, CSP, X-Frame-Options, etc.                     |
| Pen test               | Third-party engagement            | Full OWASP Top 10 review                             |
| Load test              | k6 scripts                        | 5,000 concurrent users; drawing-close burst          |
| MFA for admins         | TOTP                              | Required for drawing execution and user mgmt        |
| 1099 reporting hooks   | Admin workflow                    | Prizes ≥ $600 flagged for tax reporting              |
| Runbook                | `docs/runbook.md`                 | DR procedures, common incident patterns              |

### Acceptance Criteria

```gherkin
Feature: Production-ready

  Scenario: 99.9% uptime target verified
    Given the staging environment has been running 14 days
    Then uptime ≥ 99.9%

  Scenario: Load test passes targets
    When 5,000 concurrent users hit the API
    Then p95 latency < 500ms
    And error rate < 0.1%

  Scenario: Disaster recovery validated
    When the primary region is simulated as failed
    Then the system recovers within 1 hour (RTO)
    And data loss ≤ 15 minutes (RPO)
```

### Definition of Done

- [ ] Terraform applies cleanly to staging
- [ ] Blue-green deploy demonstrated
- [ ] Pen test findings remediated or risk-accepted
- [ ] Load test results meet PRD §5.1 targets
- [ ] Runbook complete; on-call rotation defined
- [ ] Go/no-go meeting held

---

## Risk Register

| ID  | Risk                                              | Probability | Impact   | Mitigation                                                                              |
| --- | ------------------------------------------------- | ----------- | -------- | --------------------------------------------------------------------------------------- |
| R1  | Oracle Free container too slow for dev iteration  | Medium      | Medium   | Provide container snapshot; persist volumes; document expected startup ~60s             |
| R2  | JSON Duality Views complex for team unfamiliar    | Medium      | High     | ADR + worked examples; pair-programming on CP1; fallback to plain JSON tables if needed |
| R3  | Apple Health requires native app                  | High        | Medium   | Use Terra API aggregator (assumption A-Apple); revisit at CP7                            |
| R4  | Fitness API rate limits exceeded at scale         | Medium      | Medium   | Per-user token buckets; aggressive caching; user-staggered sync windows                 |
| R5  | Concurrent ticket purchase race                   | High        | High     | Optimistic locking on `point_balance` + version column; load-tested in CP3              |
| R6  | Drawing manipulation / CSPRNG misuse              | Low         | Critical | OCI Vault CSPRNG only; immutable audit log; deterministic-mode replay tests; pen test    |
| R7  | Legal: state eligibility list changes pre-launch  | Medium      | Medium   | State list isolated in `domain/states.py`; config-driven                                |
| R8  | Email deliverability (verification, notifications)| Medium      | Medium   | Use OCI Email Delivery; warm sender domain; monitor bounce rate                          |
| R9  | Leaderboard staleness frustrates users            | Medium      | Low      | 15-min refresh acceptable for MVP per A-002; instrument latency for v1.1 prioritization |
| R10 | Premium scope creep into MVP                      | Medium      | High     | Premium subscription explicitly out of MVP per decision D-001; v1.1+                    |

## Assumptions

| ID  | Assumption                                                                  | Impact if Wrong                          | Validation                                          |
| --- | --------------------------------------------------------------------------- | ---------------------------------------- | --------------------------------------------------- |
| A1  | Oracle Database Free 23ai is sufficient parity with Autonomous JSON DB      | Late-stage migration pain                 | Spike: deploy CP1 schema to Autonomous in CP10 prep |
| A2  | Social login deferred to v1.1 (per D-001)                                   | Higher friction at registration           | Track registration funnel; revisit post-launch      |
| A3  | Apple Health via Terra API aggregator (per D-002)                           | Subscription cost; possible data gaps     | Validate Terra coverage at CP7 kickoff              |
| A4  | No "Open" tier in MVP (per D-003)                                           | Some advanced users want broader pools    | User research post-launch                           |
| A5  | No per-tier point normalization in MVP (per D-004)                          | Fairness complaints from older users      | Monitor leaderboard distributions; A/B test in v1.1 |
| A6  | Eligible states list excludes NY, FL, RI; legal will confirm pre-launch     | Compliance violations                     | Legal sign-off blocker for production deploy        |
| A7  | Prize tax reporting (1099) handled manually for prizes ≥ $600 at launch     | Admin burden; possible IRS issues         | Threshold automated in CP10; legal review            |
| A8  | Premium subscription deferred to v1.1                                       | Revenue delay                             | Revisit after MAU > 10K                              |
| A9  | 15-minute sync interval acceptable for MVP                                  | User dissatisfaction with latency         | Beta-user feedback; instrument sync latency         |
| A10 | Daily 1,000-point cap prevents gaming without frustrating power users       | Either gaming or frustration              | Monitor cap-hit rate; tune in v1.1                  |
| A11 | Three tracker integrations cover the majority of target users               | Low adoption                              | Survey beta cohort                                  |
| A12 | Email-only auth + verification is sufficient for MVP (no MFA for end users) | Account takeovers                         | Add user MFA in v1.1; admin MFA required from CP10 |

## Glossary

See `docs/FitTrack-PRD-v1.0.md` Appendix A.

---

_This plan is the single source of truth for FitTrack MVP development. Deviations should be documented as ADRs in `docs/adr/`._
