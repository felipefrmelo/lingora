import json
import logging
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.exc import OperationalError

from lingora.core.observability import JsonFormatter


async def test_health_requires_neither_database_nor_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["x-request-id"]


async def test_ready_success(app: FastAPI, client: AsyncClient) -> None:
    app.state.database.check = AsyncMock()
    response = await client.get("/api/v1/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


@pytest.mark.parametrize(
    "failure", [TimeoutError(), OperationalError("private SQL", {}, Exception("unavailable"))]
)
async def test_ready_failure_is_sanitized(
    app: FastAPI, client: AsyncClient, failure: Exception
) -> None:
    app.state.database.check = AsyncMock(side_effect=failure)
    response = await client.get("/api/v1/ready")
    assert response.status_code == 503
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["request_id"] == response.headers["x-request-id"]
    assert "private SQL" not in response.text


async def test_unknown_route_uses_problem_details(client: AsyncClient) -> None:
    response = await client.get("/does-not-exist")
    assert response.status_code == 404
    assert response.json()["type"] == "about:blank"


async def test_cors_allows_only_configured_origins(client: AsyncClient) -> None:
    allowed = await client.get("/api/v1/health", headers={"Origin": "http://localhost:5173"})
    rejected = await client.get("/api/v1/health", headers={"Origin": "https://untrusted.example"})
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-origin" not in rejected.headers
    assert "access-control-allow-credentials" not in allowed.headers


async def test_cors_is_present_on_readiness_errors(app: FastAPI, client: AsyncClient) -> None:
    app.state.database.check = AsyncMock(side_effect=TimeoutError())
    response = await client.get("/api/v1/ready", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 503
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


async def test_unexpected_errors_do_not_expose_details(app: FastAPI, client: AsyncClient) -> None:
    app.state.database.check = AsyncMock(side_effect=RuntimeError("student-private-data"))
    response = await client.get("/api/v1/ready")
    assert response.status_code == 500
    assert "student-private-data" not in response.text


async def test_validation_never_echoes_submitted_values(app: FastAPI, client: AsyncClient) -> None:
    @app.get("/test-validation")
    async def validation_endpoint(count: int) -> dict[str, int]:
        return {"count": count}

    response = await client.get("/test-validation", params={"count": "private-value"})
    assert response.status_code == 422
    assert "private-value" not in response.text
    assert response.json()["errors"][0]["location"] == ["query", "count"]


def test_json_logs_only_allowlisted_fields() -> None:
    record = logging.LogRecord("lingora.http", logging.INFO, __file__, 1, "http.request", (), None)
    record.request_id = "request-123"
    record.authorization = "Bearer secret"
    record.body = "student transcript"
    output = JsonFormatter().format(record)
    assert json.loads(output)["request_id"] == "request-123"
    assert "secret" not in output
    assert "transcript" not in output
