from collections.abc import AsyncIterator
from uuid import UUID

import pytest
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr

from lingora.core.config import Settings
from lingora.infrastructure.database import Database
from lingora.integrations.mcp.server import build_mcp_app
from tests.auth_support import JwksEndpoint, TokenFactory
from tests.integration.test_authenticated_accounts import account_client as account_client
from tests.integration.test_conversation import lesson_id as lesson_id
from tests.integration.test_learning import auth_settings as auth_settings
from tests.integration.test_learning import factory as factory
from tests.integration.test_learning import source as source
from tests.integration.test_onboarding import owner as owner

RESOURCE = "https://example.ngrok-free.dev/mcp"


@pytest.fixture
async def mcp_client(
    auth_settings: Settings, migration_config: Config, jwks_endpoint: JwksEndpoint
) -> AsyncIterator[AsyncClient]:
    settings = auth_settings.model_copy(
        update={
            "database_url": SecretStr(str(migration_config.attributes["database_url"])),
            "mcp_resource_url": RESOURCE,
            "mcp_allowed_clients": ["test-client"],
        }
    )
    database = Database(settings)
    server, app = build_mcp_app(settings, database)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="https://example.ngrok-free.dev"
    ) as client:
        client.server_manager = server.session_manager  # type: ignore[attr-defined]
        yield client
    await database.close()


def rpc(name: str, args: dict[str, object] | None = None) -> dict[str, object]:
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": name, "arguments": args or {}},
    }


async def test_http_discovery_and_token_boundaries(
    mcp_client: AsyncClient, token_factory: TokenFactory
) -> None:
    async with mcp_client.server_manager.run():  # type: ignore[attr-defined]
        metadata = await mcp_client.get("/.well-known/oauth-protected-resource/mcp")
        assert metadata.status_code == 200
        assert metadata.json()["resource"] == RESOURCE
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        }
        denied = await mcp_client.post("/mcp", headers=headers, json=rpc("get_student_context"))
        assert denied.status_code == 401
        assert "resource_metadata=" in denied.headers["www-authenticate"]
        for claims in [
            {"azp": "test-client"},
            {"aud": RESOURCE, "azp": "wrong-client"},
            {"aud": RESOURCE, "azp": "test-client", "exp": 1},
        ]:
            denied = await mcp_client.post(
                "/mcp",
                headers={**headers, "Authorization": "Bearer " + token_factory(claims)},
                json=rpc("get_student_context"),
            )
            assert denied.status_code == 401
        assert (await mcp_client.get("/api/v1/me")).status_code == 404


async def test_tool_requires_enabled_student_and_scope(
    mcp_client: AsyncClient,
    account_client: AsyncClient,
    owner: dict[str, str],
    token_factory: TokenFactory,
) -> None:
    async with mcp_client.server_manager.run():  # type: ignore[attr-defined]
        token = token_factory({"aud": RESOURCE, "azp": "test-client", "scope": "profile:read"})
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token,
        }
        request = rpc("get_student_context")
        disabled = await mcp_client.post("/mcp", headers=headers, json=request)
        assert disabled.json()["result"]["isError"] is True
        await account_client.put("/api/v1/me/mcp-access", headers=owner, json={"enabled": True})
        enabled = await mcp_client.post("/mcp", headers=headers, json=request)
        assert enabled.status_code == 200
        assert not enabled.json()["result"].get("isError", False)
        denied = await mcp_client.post("/mcp", headers=headers, json=rpc("get_pending_session"))
        assert denied.json()["result"]["isError"] is True
        await account_client.put("/api/v1/me/mcp-access", headers=owner, json={"enabled": False})
        revoked = await mcp_client.post("/mcp", headers=headers, json=request)
        assert revoked.json()["result"]["isError"] is True


async def test_mcp_conversation_completion_is_persisted_and_idempotent(
    mcp_client: AsyncClient,
    account_client: AsyncClient,
    owner: dict[str, str],
    token_factory: TokenFactory,
    lesson_id: UUID,
) -> None:
    from uuid import uuid4

    async with mcp_client.server_manager.run():  # type: ignore[attr-defined]
        response = await account_client.post(
            "/api/v1/me/conversation-sessions",
            headers={**owner, "Idempotency-Key": str(uuid4())},
            json={"lesson_id": str(lesson_id), "save_examples": True},
        )
        identifier = response.json()["id"]
        await account_client.put("/api/v1/me/mcp-access", headers=owner, json={"enabled": True})
        token = token_factory(
            {
                "aud": RESOURCE,
                "azp": "test-client",
                "scope": "sessions:read sessions:write lessons:read profile:read",
            }
        )
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token,
        }
        pending = await mcp_client.post("/mcp", headers=headers, json=rpc("get_pending_session"))
        assert pending.json()["result"]["structuredContent"]["session"]["id"] == identifier
        start = await mcp_client.post(
            "/mcp",
            headers=headers,
            json=rpc(
                "start_learning_session",
                {"session_id": identifier, "expected_version": 1, "idempotency_key": str(uuid4())},
            ),
        )
        assert start.json()["result"]["structuredContent"]["status"] == "IN_PROGRESS"
        key = str(uuid4())
        payload: dict[str, object] = {
            "session_id": identifier,
            "idempotency_key": key,
            "feedback": {
                "expected_version": 2,
                "summary": "Good progress",
                "priorities": ["Past tense"],
                "observations": [
                    {
                        "skill": "grammar",
                        "feedback": "Try the past tense",
                        "example": "I go yesterday",
                        "correction": "I went yesterday",
                    }
                ],
            },
        }
        first = await mcp_client.post(
            "/mcp", headers=headers, json=rpc("complete_learning_session", payload)
        )
        second = await mcp_client.post(
            "/mcp", headers=headers, json=rpc("complete_learning_session", payload)
        )
        assert (
            first.json()["result"]["structuredContent"]
            == second.json()["result"]["structuredContent"]
        )
        saved = await account_client.get(
            "/api/v1/me/conversation-sessions/" + identifier, headers=owner
        )
        assert saved.json()["feedback"]["summary"] == "Good progress"
        assert saved.json()["status"] == "COMPLETED"


async def test_jwks_outage_returns_service_unavailable(
    mcp_client: AsyncClient, token_factory: TokenFactory, jwks_endpoint: JwksEndpoint
) -> None:
    async with mcp_client.server_manager.run():  # type: ignore[attr-defined]
        jwks_endpoint.fail = True
        token = token_factory({"aud": RESOURCE, "azp": "test-client"})
        response = await mcp_client.post(
            "/mcp",
            headers={
                "Accept": "application/json, text/event-stream",
                "Authorization": "Bearer " + token,
            },
            json=rpc("get_student_context"),
        )
        assert response.status_code == 503


async def test_tool_rejects_client_supplied_student_id(
    mcp_client: AsyncClient, token_factory: TokenFactory
) -> None:
    async with mcp_client.server_manager.run():  # type: ignore[attr-defined]
        token = token_factory({"aud": RESOURCE, "azp": "test-client", "scope": "profile:read"})
        response = await mcp_client.post(
            "/mcp",
            headers={
                "Accept": "application/json, text/event-stream",
                "Authorization": "Bearer " + token,
            },
            json=rpc("get_student_context", {"student_id": "someone-else"}),
        )
        assert response.json()["error"]["code"] == -32602
        listing = await mcp_client.post(
            "/mcp",
            headers={
                "Accept": "application/json, text/event-stream",
                "Authorization": "Bearer " + token,
            },
            json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        )
        assert all(
            tool["inputSchema"]["additionalProperties"] is False
            for tool in listing.json()["result"]["tools"]
        )
