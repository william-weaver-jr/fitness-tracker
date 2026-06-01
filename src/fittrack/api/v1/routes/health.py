"""Liveness and readiness check endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])


@router.get("/healthz", include_in_schema=False)
async def liveness() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@router.get("/readyz", include_in_schema=False)
async def readiness() -> JSONResponse:
    checks: dict[str, Any] = {}
    all_ok = True

    # DB check — attempt a pool ping; gracefully degrade if pool not ready.
    try:
        from fittrack.database.connection import get_pool

        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.ping()
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"unavailable: {exc}"
        all_ok = False

    status_code = 200 if all_ok else 503
    body = {"status": "ok" if all_ok else "degraded", "checks": checks}
    return JSONResponse(body, status_code=status_code)
