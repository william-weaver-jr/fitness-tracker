# ADR-0002: FastAPI as the API framework

**Status:** Accepted  
**Date:** 2026-06-01  
**Deciders:** FitTrack engineering

---

## Context

FitTrack needs a Python HTTP API framework for an async workload: every request involves at least one async Oracle connection-pool acquire plus cursor execution, and the activity-sync workers and drawing executor run alongside the API in the same process during development. The framework must:

- Support `async def` route handlers natively (no sync-to-async bridging overhead).
- Produce OpenAPI/Swagger docs automatically — the HTML test page and integration tests rely on the live `/docs` endpoint.
- Enforce request/response schemas strictly — the sweepstakes domain has non-negotiable invariants (point balance ≥ 0, tier code format, drawing status machine) that must be caught at the API boundary.
- Integrate with Pydantic v2, which is already required for `pydantic-settings`.

---

## Decision

Use **FastAPI 0.115+** with **Pydantic v2** for all API routes, request validation, and response serialization.

Routes live in `src/fittrack/api/v1/routes/`. Schemas (request/response models with camelCase aliases) live in `src/fittrack/api/v1/schemas/`. RFC 7807 `application/problem+json` error responses are centralised in `src/fittrack/api/errors.py`.

---

## Alternatives Considered

| Option | Why Rejected |
|--------|-------------|
| **Flask + Flask-RESTX** | Synchronous by default; async support is bolted on via `asgiref`. Route handler dispatching in the Oracle async pool would require careful thread-bridging. Auto OpenAPI generation is less integrated. |
| **Django REST Framework** | Full-stack Django overhead is inappropriate for a pure API service. DRF's ORM integration adds pressure to add SQLAlchemy or Django ORM (which we explicitly reject — ADR-0003). Async support in DRF is still partial as of 2026. |
| **Starlette (bare)** | FastAPI is built on Starlette; using bare Starlette would mean re-implementing OpenAPI generation, dependency injection, and Pydantic integration that FastAPI provides out of the box. |
| **Litestar** | Viable alternative with similar feature set. FastAPI chosen because of larger ecosystem, more community resources, and team familiarity. |

---

## Consequences

**Positive:**
- Native `asyncio` support: route handlers, dependencies, and middleware are all `async def`; no thread-pool overhead when awaiting Oracle connections.
- Automatic OpenAPI 3.1 documentation at `/docs` (Swagger UI) and `/redoc` — served in dev/staging, disabled in production via `docs_url=None`.
- Pydantic v2 integration: request bodies are validated and deserialized with strict type checking; response models enforce the camelCase↔snake_case alias contract without manual conversion.
- FastAPI's dependency injection (`Depends`) cleanly handles auth tokens (CP2+), database connections, and pagination parameters across all routes.
- `TestClient` (from Starlette/httpx) enables fully synchronous unit tests of async route handlers without spinning up a live server.

**Negative:**
- The Pydantic model proliferation (one schema per entity per operation) adds file count. Mitigated by shared `common.py` schemas and `Paginated[T]` generic.
- FastAPI's dependency injection is implicit — a new developer must understand the `Depends(...)` pattern before the auth layer (CP2) makes sense.

**Neutral:**
- Uvicorn is the ASGI server in development (`make dev`) and in the Docker image. No changes required for production; Gunicorn with Uvicorn workers is a straightforward upgrade if process management is needed in CP10.
- CORS, security headers, and request-ID injection are handled as Starlette middleware, not FastAPI-specific features — this code is framework-portable if we ever switch.

---

## References

- `src/fittrack/main.py` — app factory and middleware stack
- `src/fittrack/api/v1/routes/` — route modules
- `src/fittrack/api/v1/schemas/` — Pydantic schemas
- `src/fittrack/api/errors.py` — RFC 7807 error handlers
