"""Dev-only routes: test page + DB seed/reset endpoints.

Only registered when ENV=development. Returns 404 in all other environments.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse, Response

from fittrack.api.errors import problem_response

router = APIRouter(prefix="/dev", tags=["dev"])

_STATIC_DIR = Path(__file__).parent.parent.parent.parent / "static" / "dev"
_TEST_PAGE = _STATIC_DIR / "test_page.html"


@router.get("", include_in_schema=False)
@router.get("/", include_in_schema=False)
async def serve_test_page() -> Response:
    if not _TEST_PAGE.exists():
        return problem_response(status_code=404, title="Test page not found")
    return FileResponse(_TEST_PAGE)  # type: ignore[return-value]


@router.post("/seed", response_model=None)
async def seed_db() -> JSONResponse:
    try:
        import importlib.util
        import sys
        from pathlib import Path as _P

        seed_path = _P(__file__).parent.parent.parent.parent / "scripts" / "seed_data.py"
        spec = importlib.util.spec_from_file_location("seed_data", seed_path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            sys.modules["seed_data"] = mod
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
            if hasattr(mod, "main"):
                import asyncio

                if asyncio.iscoroutinefunction(mod.main):
                    await mod.main()
                else:
                    mod.main()
        return JSONResponse({"status": "seeded"})
    except Exception as exc:
        return JSONResponse({"status": "error", "detail": str(exc)}, status_code=500)


@router.post("/reset", response_model=None)
async def reset_db() -> JSONResponse:
    return JSONResponse({"status": "not implemented — use `make db-reset`"}, status_code=501)
