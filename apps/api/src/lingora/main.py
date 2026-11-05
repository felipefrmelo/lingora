from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lingora.core.config import Settings
from lingora.core.errors import ProblemDetails, register_error_handlers
from lingora.core.observability import (
    configure_logging,
    create_tracer_provider,
    register_request_middleware,
)
from lingora.health import router
from lingora.infrastructure.database import Database
from lingora.integrations.auth0.verifier import Auth0TokenVerifier
from lingora.modules.identity.http import router as identity_router
from lingora.modules.learning.http import router as learning_router
from lingora.modules.onboarding.http import router as onboarding_router


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    configure_logging()
    database = Database(settings)
    tracer_provider = create_tracer_provider(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
        try:
            yield
        finally:
            await database.close()
            tracer_provider.shutdown()

    app = FastAPI(
        title="Lingora API",
        version="0.1.0",
        description="The authoritative backend for Lingora learning data.",
        lifespan=lifespan,
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url=None,
        responses={"default": {"model": ProblemDetails, "description": "Request error"}},
    )
    app.state.database = database
    app.state.settings = settings
    app.state.token_verifier = Auth0TokenVerifier(settings)
    app.include_router(router)
    app.include_router(identity_router)
    app.include_router(onboarding_router)
    app.include_router(learning_router)
    register_error_handlers(app)
    register_request_middleware(app, tracer_provider)
    # Outermost application middleware: error responses receive the same CORS headers.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
        expose_headers=["X-Request-ID"],
    )
    return app


app = create_app()
