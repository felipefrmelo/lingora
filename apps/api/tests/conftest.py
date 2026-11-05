from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr

from lingora.core.config import Settings
from lingora.main import create_app


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    for name in (
        "DATABASE_URL",
        "CORS_ORIGINS",
        "DB_READY_TIMEOUT_SECONDS",
        "OTEL_EXPORTER_OTLP_ENDPOINT",
    ):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def app() -> FastAPI:
    return create_app(
        Settings(
            app_env="test",
            database_url=SecretStr("postgresql+psycopg://test:test@127.0.0.1:1/test"),
            otel_exporter_otlp_endpoint="",
        )
    )


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http,
    ):
        yield http
