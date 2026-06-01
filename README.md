# FitTrack

> Gamified fitness tracker — earn points from activity, spend them on sweepstakes tickets for tiered prize drawings.

FitTrack converts physical activity (synced from Apple Health, Google Fit, and Fitbit) into points that users spend on sweepstakes tickets across daily, weekly, monthly, and annual prize drawings. Competition is structured across **30 demographic tiers** (5 age brackets × 2 sex categories × 3 fitness levels) to keep drawings fair. The API is built with FastAPI on Oracle 23ai, deployed on Oracle Cloud Infrastructure; the React 18 frontend is planned for CP8.

## Quick Start

**Target: < 15 minutes from fresh clone**

### Prerequisites

- Python 3.12+
- Docker Desktop (or Colima/Podman with compose support)
- Make
- ~5 GB free disk (Oracle Free image is ~3.5 GB)

### Setup

```bash
# 1. Bootstrap virtualenv and install dependencies
make setup

# 2. Start Oracle Free + Redis containers (Oracle takes ~60 s on first start)
make docker-up

# 3. Apply migrations and seed synthetic data
make db-migrate
make db-seed

# 4. Run the dev server
make dev
```

Then open:

| URL | Purpose |
|-----|---------|
| http://localhost:8000/docs | Interactive API docs (Swagger UI) |
| http://localhost:8000/dev | HTML test harness (dev only) |
| http://localhost:8000/healthz | Health check endpoint |

### Common commands

```bash
make test              # Full pytest suite with coverage gate (requires Oracle)
make test-unit         # Fast unit tests only (no DB needed)
make test-integration  # Integration tests (requires running Oracle)
make lint              # ruff + black --check
make format            # Auto-fix with ruff + black
make typecheck         # mypy strict
make db-reset          # Drop user data + re-migrate + re-seed (destructive)
make docker-down       # Stop containers
make logs              # Tail container logs
make shell             # SQL*Plus shell into the dev DB
```

## Configuration

Copy `.env.example` to `.env`. The example file ships with working defaults for local Docker development — no changes needed for `make dev`.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENV` | Yes | `development` | `development` \| `staging` \| `production` |
| `LOG_LEVEL` | No | `INFO` | Python log level |
| `ORACLE_HOST` | Yes | `localhost` | DB host (`oracle` inside Docker network) |
| `ORACLE_PORT` | No | `1521` | Oracle listener port |
| `ORACLE_SERVICE_NAME` | Yes | `FREEPDB1` | PDB service name |
| `ORACLE_USER` | Yes | `fittrack_app` | App schema user |
| `ORACLE_PASSWORD` | Yes | *(see example)* | DB password — rotate before staging |
| `ORACLE_POOL_MIN` / `MAX` | No | `2` / `10` | Connection pool bounds |
| `REDIS_URL` | No | `redis://localhost:6379/0` | Cache (required from CP4+) |
| `JWT_PRIVATE_KEY_PATH` | CP2+ | — | RS256 private key; generate with `openssl genpkey -algorithm RSA -pkcs8` |
| `JWT_PUBLIC_KEY_PATH` | CP2+ | — | RS256 public key path |
| `CORS_ALLOWED_ORIGINS` | No | `http://localhost:5173,...` | Comma-separated allowed origins |
| `ENABLE_DEV_TEST_PAGE` | No | `true` | Expose `/dev` route; force-disabled when `ENV=production` |

## Architecture

See `docs/IMPLEMENTATION_PLAN.md` for the 10-checkpoint roadmap and `CLAUDE.md` for full project context.

### Key decisions

- **Oracle 23ai JSON Duality Views** as the data access layer — no ORM. Duality Views give document-style access with relational integrity; repositories query them directly via `python-oracledb`.
- **`python-oracledb` thin mode** — no Oracle Instant Client install required.
- **FastAPI + Pydantic v2** — auto OpenAPI, async-native, strict typed schemas.
- **OCI Vault CSPRNG** for drawing selection — audited cryptographic randomness required; never `random`/`secrets`.
- **30 competition tiers** — tier code (`{M|F}-{AGE}-{LEVEL}`) is computed from profile at query time, never stored as source of truth.

### Project layout

```
src/fittrack/
├── api/v1/         FastAPI routes + Pydantic schemas (RFC 7807 errors)
├── api/middleware/ Security headers, request ID injection
├── database/       Connection pool, migrations (SQL runners), repositories
├── domain/         Pure-logic value objects and enums (no I/O)
├── services/       Business logic — points, tiers, drawings (CP3+)
├── workers/        Background jobs — activity sync, drawing exec (CP3+)
└── utils/          Crypto, JWT helpers
tests/
├── unit/           Pure-Python tests (no DB, no network) — Hypothesis property tests
├── integration/    Repository + API tests against live Oracle Free container
└── factories/      Polyfactory factories for synthetic test data
scripts/            Seed / reset utilities
static/dev/         HTML test harness (dev only — 404 in production)
docker/             Compose stack, Dockerfile, Oracle init SQL
docs/               PRD, implementation plan, ADRs
```

## Contributing

1. Follow strict TDD: write a failing test first, then the minimum implementation, then refactor.
2. Install pre-commit hooks: `pre-commit install` (activates ruff, black, mypy, gitleaks).
3. Coverage gates: unit > 90%, overall > 85% (integration tests require Oracle — run with `make test-integration`).
4. Branch protection on `main` requires CI green + 1 review.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `make docker-up` hangs or `db-migrate` fails immediately | Oracle Free container still initializing | Wait ~60 s on first start; run `make logs` to watch Oracle boot progress |
| `pip install -e ".[dev]"` fails: *no matching distribution for python-oracledb* | ARM Mac — no pre-built wheel available | Install all deps except oracledb (see the unit-test job in `.github/workflows/ci.yml`); use `make test-unit` locally — `make test` (full suite with coverage gate) only runs in CI |
| `TestClient` import fails: *cannot import name 'Client' from 'httpx'* | Starlette 1.2 requires `httpx2` alongside `httpx` | `pip install httpx2` |
| Port 1521 already in use | Another Oracle instance running locally | `docker ps` to find it, stop it, or update `ORACLE_PORT` in `.env` |
| Tier code looks stale after a profile update | Tier code is computed, not stored — must be recalculated explicitly | Call `services.tiers.recalculate()`; never set `tier_code` directly |

## Documentation

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Project context and constraints for AI-assisted development |
| `docs/IMPLEMENTATION_PLAN.md` | 10-checkpoint roadmap |
| `docs/IMPLEMENTATION_CHECKLIST.md` | Granular task tracker |
| `docs/FitTrack-PRD-v1.0.md` | Full Product Requirements Document |
| `docs/adr/` | Architecture Decision Records |

## License

Proprietary. See LICENSE for details.
