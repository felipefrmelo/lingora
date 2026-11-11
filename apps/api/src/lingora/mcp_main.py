"""Dedicated public MCP-only listener; the REST API is not exposed through this app."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from lingora.core.config import Settings
from lingora.infrastructure.database import Database
from lingora.integrations.mcp.server import build_mcp_app

settings = Settings()
database = Database(settings)
server, mcp_app = build_mcp_app(settings, database)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    try:
        async with server.session_manager.run():
            yield
    finally:
        await database.close()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/", mcp_app)
