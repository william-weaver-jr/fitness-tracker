"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from fittrack.api.errors import (
    http_exception_handler,
    problem_response,
    validation_exception_handler,
)
from fittrack.api.middleware.request_id import RequestIdMiddleware
from fittrack.api.middleware.security_headers import SecurityHeadersMiddleware
from fittrack.api.v1.routes.activities import router as activities_router
from fittrack.api.v1.routes.connections import router as connections_router
from fittrack.api.v1.routes.drawings import router as drawings_router
from fittrack.api.v1.routes.fulfillments import router as fulfillments_router
from fittrack.api.v1.routes.health import router as health_router
from fittrack.api.v1.routes.point_transactions import router as transactions_router
from fittrack.api.v1.routes.prizes import router as prizes_router
from fittrack.api.v1.routes.profiles import router as profiles_router
from fittrack.api.v1.routes.sponsors import router as sponsors_router
from fittrack.api.v1.routes.tickets import router as tickets_router
from fittrack.api.v1.routes.users import router as users_router
from fittrack.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()

    # Initialize DB connection pool (skipped gracefully if DB unavailable in dev/test)
    try:
        from fittrack.database.connection import close_pool, init_pool

        await init_pool(settings)
        yield
        await close_pool()
    except Exception:
        yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="FitTrack API",
        version="0.1.0",
        description="Gamified fitness tracker — earn points, win prizes.",
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    # Middleware (added in reverse order — last added is outermost)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]

    @app.exception_handler(404)
    async def not_found_handler(request: object, exc: object) -> object:
        from fastapi import Request

        if isinstance(request, Request):
            return problem_response(
                status_code=404,
                title="Not Found",
                detail="The requested resource could not be found.",
                instance=str(request.url.path),
            )
        return problem_response(status_code=404, title="Not Found")

    # Routers
    app.include_router(health_router)
    app.include_router(users_router)
    app.include_router(profiles_router)
    app.include_router(connections_router)
    app.include_router(activities_router)
    app.include_router(transactions_router)
    app.include_router(drawings_router)
    app.include_router(tickets_router)
    app.include_router(prizes_router)
    app.include_router(fulfillments_router)
    app.include_router(sponsors_router)

    if not settings.is_production and settings.enable_dev_test_page:
        from fittrack.api.dev import router as dev_router

        app.include_router(dev_router)

    return app


app = create_app()
