# Implementation Checklist: FitTrack

> Living document. Update boxes as work completes. Each checkpoint corresponds to a section in `IMPLEMENTATION_PLAN.md`.

**Legend:** `[ ]` = todo · `[~]` = in progress · `[x]` = done · `[-]` = skipped/deferred

---

## Checkpoint 1: Foundation — Data Layer, CRUD APIs, Test Page

### 1.1 Project Bootstrap

- [x] `pyproject.toml` with Python 3.12, FastAPI, python-oracledb, Pydantic v2, polyfactory, pytest, hypothesis, ruff, black, mypy
- [x] `.env.example` with every required environment variable documented
- [x] `.gitignore` covering `.env`, `__pycache__`, `.venv`, `coverage`, `node_modules`
- [x] `.pre-commit-config.yaml` with ruff, black, mypy, gitleaks
- [x] `Makefile` targets: `setup`, `dev`, `db-migrate`, `db-seed`, `db-reset`, `test`, `lint`, `test-page`, `clean`
- [ ] README with <15 minute setup walkthrough

### 1.2 Docker Compose Infrastructure

- [x] `docker/docker-compose.yml` with services: `oracle`, `redis`, `api`
- [x] Oracle service uses `gvenzl/oracle-free:23-slim` with persistent volume
- [x] Redis service (placeholder for CP4)
- [x] `docker/oracle-init/01-create-app.sql` creates `fittrack` schema + user
- [x] `docker/Dockerfile` (multi-stage; slim runtime)
- [x] Healthchecks defined for all services
- [x] `make dev` waits for Oracle "READY" before starting API

### 1.3 Application Skeleton

- [x] `src/fittrack/main.py` — FastAPI app with lifespan
- [x] `src/fittrack/config.py` — Pydantic Settings
- [x] `src/fittrack/api/middleware/security_headers.py`
- [x] `src/fittrack/api/middleware/request_id.py`
- [x] `src/fittrack/api/errors.py` — RFC 7807 problem+json handler
- [x] `src/fittrack/api/pagination.py` — `Page[T]` generic
- [ ] Logging configured (JSON in prod, pretty in dev)

### 1.4 Database Layer

- [x] `src/fittrack/database/connection.py` — async connection pool with health check
- [x] `src/fittrack/database/migrations/__init__.py` — forward-only migration runner
- [x] Migration `0001_core.sql` — all 10 tables, constraints, indexes
- [x] Migration `0002_views.sql` — `user_profile_dv`, `drawing_dv`, `activity_dv`
- [x] Migration `0003_audit.sql` — functional JSON indexes + supplemental indexes
- [x] Repository: `users_repo.py`
- [x] Repository: `profiles_repo.py`
- [x] Repository: `connections_repo.py`
- [x] Repository: `activities_repo.py`
- [x] Repository: `point_transactions_repo.py`
- [x] Repository: `drawings_repo.py`
- [x] Repository: `tickets_repo.py`
- [x] Repository: `prizes_repo.py`
- [x] Repository: `fulfillments_repo.py`
- [x] Repository: `sponsors_repo.py`

### 1.5 Domain Layer

- [x] `domain/enums.py` — all status/type enums (StrEnum)
- [x] `domain/tier.py` — `compute_tier_code()` + `TierCode.parse()` with tests
- [x] `domain/age.py` — age + bracket helpers with property tests
- [x] `domain/states.py` — eligible state list (48 states, excludes NY/FL/RI)

### 1.6 API Routes (CRUD)

- [x] `health.py` (`/healthz`, `/readyz`)
- [x] `users.py`
- [x] `profiles.py`
- [x] `connections.py`
- [x] `activities.py`
- [x] `point_transactions.py`
- [x] `drawings.py`
- [x] `tickets.py`
- [x] `prizes.py`
- [x] `fulfillments.py`
- [x] `sponsors.py`
- [x] `dev.py` — gated to `ENV != production`

### 1.7 Synthetic Data

- [x] `tests/factories/base.py` — deterministic Faker seed
- [x] Factory per entity (user, profile, activity, drawing, sponsor + helpers)
- [x] `scripts/seed_data.py` — 5 admin + 5 premium + 300 regular users (10 per tier)
- [x] Seed: 60-day activity history for ~50 users
- [x] Seed: 5 sponsors
- [x] Seed: 30 drawings across types/statuses
- [x] Seed: ~5,000 tickets across open drawings
- [x] Seed: 8 fulfillment records in varied states
- [x] `scripts/reset_db.py` — drop + migrate + seed
- [ ] Seed completes in <60s (requires Oracle to verify)

### 1.8 HTML Test Page

- [x] `static/dev/test_page.html` — vanilla JS, single file
- [x] Sidebar with entity navigation
- [x] Paginated table viewer per entity
- [x] JSON detail panel
- [x] Create/Edit forms per entity (users, drawings, sponsors)
- [x] Delete confirmation
- [x] Seed DB button (POST `/dev/seed`)
- [x] Reset DB button (POST `/dev/reset`)
- [x] Live request/response log
- [x] Sample reports panel (users by tier, drawings by status)
- [x] Returns 404 when `ENV == production`

### 1.9 Testing

- [x] `pytest` configured with coverage gates (85% full suite)
- [x] Unit tests: `test_tier.py`, `test_age.py`, `test_states.py`, `test_factories.py`, `test_enums.py`, `test_pagination.py`, `test_errors.py`, `test_health.py`, `test_middleware.py`, `test_migrations.py`, `test_schemas.py`, `test_routes_*.py` (170 tests total)
- [ ] Integration tests: one per repository (requires Oracle)
- [x] API tests: one per route module (mocked, unit-level)
- [ ] Migration tests: forward + idempotency
- [ ] Test DB fixture using Oracle Free container (or test schema)

### 1.10 CI/CD (skeleton)

- [x] `.github/workflows/ci.yml` — lint + unit + integration jobs
- [x] CI runs: ruff, black --check, mypy, pytest with coverage gate
- [x] CI starts Oracle Free service container for integration tests
- [ ] PR template
- [ ] Branch protection on `main` (1 review + CI green)

### 1.11 Documentation

- [ ] `CLAUDE.md` (done)
- [ ] `IMPLEMENTATION_PLAN.md` (done)
- [ ] `IMPLEMENTATION_CHECKLIST.md` (this file)
- [ ] `README.md` with quickstart
- [ ] `docs/adr/0001-oracle-json.md`
- [ ] `docs/adr/0002-fastapi.md`
- [ ] `docs/adr/0003-no-orm.md`
- [ ] `docs/adr/0004-tier-encoding.md`

### 1.12 CP1 Demo

- [ ] Fresh clone setup verified by second developer in <15 minutes
- [ ] All acceptance gherkin scenarios pass
- [ ] Stakeholder demo of test page walkthrough

---

## Checkpoint 2: Authentication & Authorization

### 2.1 Password & Tokens

- [ ] Argon2id password hashing service
- [ ] Password strength validator (12+ chars, complexity)
- [ ] RSA keypair generation for dev; OCI Vault for prod
- [ ] JWT access token (RS256, 1h)
- [ ] JWT refresh token (RS256, 30d, hashed in DB, rotated)
- [ ] JWT denylist (in-memory for CP2; Redis in CP4)

### 2.2 Auth Endpoints

- [ ] `POST /auth/register`
- [ ] `POST /auth/login`
- [ ] `POST /auth/refresh`
- [ ] `POST /auth/verify-email`
- [ ] `POST /auth/forgot-password`
- [ ] `POST /auth/reset-password`
- [ ] `POST /auth/logout`
- [ ] `GET /users/me`

### 2.3 Eligibility

- [ ] 18+ DOB check rejects underage
- [ ] State eligibility check rejects NY/FL/RI
- [ ] ToS + Sweepstakes Rules acceptance timestamps recorded

### 2.4 RBAC

- [ ] `current_user` dependency
- [ ] `require_role(...)` dependency
- [ ] All CP1 endpoints wrapped with auth dependencies
- [ ] Admin endpoints protected with `require_role("admin")`
- [ ] 100% of protected endpoints covered by RBAC tests

### 2.5 Rate Limiting & Lockout

- [ ] slowapi rate limiter middleware
- [ ] Per-route limits: anonymous 10/min, authenticated 100/min, admin 500/min
- [ ] 5 failed login attempts → 15-min lockout with progressive backoff
- [ ] 423 Locked response with retry-after header
- [ ] Auth events logged to immutable `auth_events` table

### 2.6 Email Verification

- [ ] Mock SMTP for dev (`mailhog`)
- [ ] Verification token (24h expiry, single-use)
- [ ] `email_verified` and `email_verified_at` updated on redemption
- [ ] `status` flips `pending` → `active` after verification

### 2.7 Database

- [ ] Migration `0004_auth_tables` — `refresh_tokens`, `email_verifications`, `password_resets`, `auth_events`, `account_lockouts`

### 2.8 Tests

- [ ] Unit: `test_password.py`, `test_tokens.py`, `test_lockout.py`
- [ ] Integration: `test_auth_flows.py`, `test_rbac.py`
- [ ] All CP2 acceptance scenarios pass

### 2.9 Test Page Updates

- [ ] Login form with 3 prefilled buttons (user/premium/admin)
- [ ] "Logged in as" indicator
- [ ] All requests now send bearer token
- [ ] 401/403 surfaced in log pane

---

## Checkpoint 3: Activity Sync & Points Engine

### 3.1 Points Engine

- [ ] `points/calculator.py` — pure function matching PRD §4.3.1
- [ ] Daily cap enforcer (1,000 pts, `America/New_York` boundary)
- [ ] Workout cap (max 3/day)
- [ ] Streak bonus (250 pts for 7 consecutive active days)
- [ ] Hypothesis property tests: cap never exceeded, sum matches components

### 3.2 Points Service

- [ ] Atomic activity-to-points operation (single transaction)
- [ ] Optimistic locking on `users.point_balance` via `version` column
- [ ] Concurrent-purchase race test (load tested)
- [ ] All point movements produce a `point_transaction` ledger entry

### 3.3 Sync Pipeline

- [ ] `SyncProvider` abstract interface
- [ ] `MockProvider` generating realistic activity stream
- [ ] Normalizer: provider raw → internal `Activity` schema
- [ ] Deduplicator (primary tracker → most metrics → first received)
- [ ] APScheduler-backed sync worker (15-min cadence)
- [ ] Sync failures logged with retry (exponential backoff)

### 3.4 Heart Rate Zones

- [ ] `domain/heart_rate.py` — max HR from age, intensity bucketing
- [ ] Re-derives on profile update (no caching of intensity)

### 3.5 Anti-Gaming

- [ ] Anomaly detector flags >3σ from tier average
- [ ] Manual review queue table + admin endpoint
- [ ] Flagged accounts blocked from ticket purchase until reviewed

### 3.6 API Endpoints

- [ ] `GET /activities/summary`
- [ ] `POST /connections/{provider}/sync` (rate-limited 1/min/user)
- [ ] `GET /points/balance`
- [ ] `GET /points/transactions`

### 3.7 Database

- [ ] Migration `0005_anti_gaming` — `flagged_accounts`, `manual_review_queue`
- [ ] Migration `0006_sync_state` — adds `sync_state` to `tracker_connections`

### 3.8 Tests

- [ ] Property tests pass
- [ ] Concurrent ticket purchase race resolved correctly
- [ ] Sync worker integration test produces expected ledger
- [ ] Dedup test covering multi-tracker overlap

---

## Checkpoint 4: Tier Assignment & Leaderboards

- [ ] Tier service: compute, persist, recalculate on profile change
- [ ] Redis client wired (replaces in-memory rate limiter from CP2)
- [ ] Leaderboard service reads from Redis sorted sets
- [ ] Leaderboard worker rebuilds sorted sets every 15 min
- [ ] Period boundary helpers (daily/weekly/monthly/all-time in `America/New_York`)
- [ ] Endpoint: `GET /leaderboards/{period}` with tier code + user ± 10
- [ ] Endpoint: `GET /leaderboards/{period}/tiers`
- [ ] Endpoint: `GET /users/me/rank`
- [ ] Migration `0007_leaderboard_audit` — `leaderboard_snapshots`
- [ ] Period reset verified at boundary
- [ ] All 30 tiers have correct membership after seed

---

## Checkpoint 5: Sweepstakes Engine

- [ ] Drawing state machine: draft → scheduled → open → closed → completed
- [ ] Ticket purchase: atomic point debit + ticket insert
- [ ] Drawing executor: snapshot → assign ticket numbers → CSPRNG → record
- [ ] CSPRNG client (OCI Vault prod, `secrets.SystemRandom` dev with audit log)
- [ ] Snapshot store (immutable)
- [ ] Drawing scheduler worker (closes T-5, executes T-0)
- [ ] Eligibility check (min_account_age_days, role, status)
- [ ] Endpoints: list drawings, detail, buy tickets, results
- [ ] Admin endpoints: create, update, execute, cancel
- [ ] Migration `0008_drawing_audit`
- [ ] Deterministic replay test passes
- [ ] Concurrent ticket purchase load test
- [ ] Audit log immutability verified (DB trigger or CHECK)

---

## Checkpoint 6: Prize Fulfillment

- [ ] Fulfillment state machine service
- [ ] Notification dispatcher (email + in-app)
- [ ] Address validator (mock dev; real provider in v1.1)
- [ ] Forfeit worker (7-day warning, 14-day forfeit)
- [ ] Migration `0009_notifications`
- [ ] User endpoints: `/users/me/fulfillments`, address confirm, notifications
- [ ] Admin endpoints: fulfillment queue, ship, deliver, forfeit
- [ ] All state transitions enforced (no skipping)
- [ ] Forfeit worker tested with frozen clock

---

## Checkpoint 7: Real Tracker Integrations

- [ ] OAuth 2.0 abstraction with state CSRF
- [ ] Fitbit provider
- [ ] Google Fit provider
- [ ] Apple Health provider (Terra API)
- [ ] AES-256-GCM token encryption with OCI Vault-managed DEK
- [ ] Per-provider per-user rate limit guard
- [ ] Circuit breaker on consecutive failures
- [ ] Endpoints: OAuth initiate, callback, disconnect
- [ ] Sandbox test runs against real providers
- [ ] Token refresh on expiration tested

---

## Checkpoint 8: React User App

- [ ] Vite + React 18 + TS scaffold
- [ ] Design tokens from PRD §9.3
- [ ] Routing + auth guards
- [ ] TanStack Query for API state
- [ ] Auth screens (register, login, verify, forgot-password)
- [ ] Dashboard (PRD §9.2.1)
- [ ] Activity screens (today, history, achievements)
- [ ] Leaderboards (PRD §9.2.4)
- [ ] Drawings list (PRD §9.2.2)
- [ ] Ticket purchase modal (PRD §9.2.3)
- [ ] Profile + connections
- [ ] Notifications dropdown
- [ ] Playwright E2E: full critical-path journey
- [ ] Lighthouse mobile score ≥85
- [ ] WCAG 2.1 AA spot-check passes

---

## Checkpoint 9: React Admin App

- [ ] Admin app scaffold (separate Vite project)
- [ ] Admin-only auth gate
- [ ] Dashboard with KPIs
- [ ] Drawings manager (CRUD, schedule, execute with MFA)
- [ ] Sponsors CRUD
- [ ] Fulfillments queue
- [ ] User management (search, suspend, point adjust)
- [ ] Analytics with CSV export
- [ ] All admin user stories US-050 through US-055 demonstrable

---

## Checkpoint 10: Production Readiness

### 10.1 Infrastructure

- [ ] Terraform: OCI Compute, OKE, Autonomous JSON DB, Cache, Queue, Vault, WAF, Object Storage
- [ ] Helm chart for OKE
- [ ] OCI Vault wired for all secrets (JWT keys, DB pw, OAuth client secrets)
- [ ] OCI Cache (Redis) replaces dev Redis
- [ ] OCI Queue replaces APScheduler
- [ ] OCI Email Delivery for transactional emails

### 10.2 Observability

- [ ] OpenTelemetry instrumentation
- [ ] OCI APM dashboards
- [ ] Prometheus `/metrics` endpoint
- [ ] Loki + Grafana log dashboards
- [ ] PagerDuty wired for critical alerts
- [ ] Alert rules from PRD §12.4 in place

### 10.3 CI/CD Full Pipeline

- [ ] Docker build & push to OCI Container Registry
- [ ] Staging auto-deploy on `main`
- [ ] Production deploy with manual approval gate
- [ ] Blue-green deployment
- [ ] Automated rollback on health-check failure

### 10.4 Security

- [ ] WAF rules (DDoS, bot mitigation)
- [ ] Security headers middleware (HSTS, CSP, X-Frame-Options, etc.)
- [ ] CORS allowlist
- [ ] CSRF protection (SameSite + custom header)
- [ ] Snyk SAST + dependency scanning in CI
- [ ] OWASP ZAP DAST weekly
- [ ] Third-party penetration test
- [ ] Admin MFA (TOTP) for drawing execution + user mgmt

### 10.5 Compliance

- [ ] CCPA privacy controls (data export, deletion within 30 days)
- [ ] Cookie consent banner
- [ ] 1099 tax reporting flag for prizes ≥ $600
- [ ] State-specific sweepstakes rules display
- [ ] Legal sign-off on ToS + Sweepstakes Rules

### 10.6 Performance & DR

- [ ] k6 load test: 5,000 concurrent users
- [ ] k6 stress test to find breaking point
- [ ] k6 soak test: 24h sustained load
- [ ] Performance baseline meets PRD §5.1 targets
- [ ] DR drill: RTO < 1h, RPO < 15min verified

### 10.7 Operational Readiness

- [ ] `docs/runbook.md` with common incidents
- [ ] On-call rotation defined
- [ ] Soft launch with limited user cohort
- [ ] Go/no-go meeting held; production launch approved
- [ ] Post-launch monitoring plan documented

---

## Post-MVP Backlog (v1.1+)

- [ ] Native iOS app (Apple Health direct)
- [ ] Native Android app
- [ ] Stripe premium subscription
- [ ] Social login (Google, Apple)
- [ ] Real-time leaderboards (WebSocket)
- [ ] Professional services marketplace
- [ ] Sponsor self-service portal
- [ ] Team/group competitions
- [ ] User MFA (TOTP)
- [ ] Open tier opt-in
- [ ] Per-tier point normalization
- [ ] International expansion
