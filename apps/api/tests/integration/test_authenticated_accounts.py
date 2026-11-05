import asyncio
from collections.abc import AsyncIterator

import pytest
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lingora.core.config import Settings
from lingora.main import create_app
from lingora.modules.identity.models import ExternalIdentity, Student
from tests.auth_support import JwksEndpoint, TokenFactory


@pytest.fixture
async def account_client(
    auth_settings: Settings,
    migration_config: Config,
    jwks_endpoint: JwksEndpoint,
    session: AsyncSession,
) -> AsyncIterator[AsyncClient]:
    settings = auth_settings.model_copy(
        update={"database_url": SecretStr(str(migration_config.attributes["database_url"]))}
    )
    app = create_app(settings)
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client,
    ):
        yield client


async def test_bootstrap_is_idempotent_and_me_is_read_only(
    account_client: AsyncClient, token_factory: TokenFactory, session: AsyncSession
) -> None:
    headers = {"Authorization": "Bearer " + token_factory()}
    assert (await account_client.get("/api/v1/me", headers=headers)).status_code == 404
    assert await session.scalar(select(func.count()).select_from(Student)) == 0
    first = await account_client.post("/api/v1/me/bootstrap", headers=headers, json={})
    second = await account_client.post("/api/v1/me/bootstrap", headers=headers, json={})
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert set(first.json()) == {"id", "created_at"}
    current = await account_client.get("/api/v1/me", headers=headers)
    assert current.json() == first.json()
    assert await session.scalar(select(func.count()).select_from(Student)) == 1


async def test_students_are_isolated_even_when_emails_match(
    account_client: AsyncClient, token_factory: TokenFactory
) -> None:
    tokens = [
        token_factory({"sub": sub, "email": "same@example.test"})
        for sub in ["auth0|a", "google-oauth2|b"]
    ]
    accounts: list[dict[str, str]] = []
    for token in tokens:
        response = await account_client.post(
            "/api/v1/me/bootstrap", headers={"Authorization": "Bearer " + token}
        )
        assert response.status_code == 200
        accounts.append(response.json())
    assert accounts[0]["id"] != accounts[1]["id"]
    for token, expected in zip(tokens, accounts, strict=True):
        response = await account_client.get(
            "/api/v1/me", headers={"Authorization": "Bearer " + token}
        )
        assert response.json() == expected


async def test_concurrent_first_login_leaves_no_orphans(
    account_client: AsyncClient, token_factory: TokenFactory, session: AsyncSession
) -> None:
    headers = {"Authorization": "Bearer " + token_factory({"sub": "auth0|concurrent"})}
    responses = await asyncio.gather(
        *[account_client.post("/api/v1/me/bootstrap", headers=headers, json={}) for _ in range(8)]
    )
    assert {response.status_code for response in responses} == {200}
    assert len({response.json()["id"] for response in responses}) == 1
    assert await session.scalar(select(func.count()).select_from(Student)) == 1
    assert await session.scalar(select(func.count()).select_from(ExternalIdentity)) == 1


async def test_invalid_authorization_never_provisions_students(
    account_client: AsyncClient, token_factory: TokenFactory, session: AsyncSession
) -> None:
    for claims, status in [({"exp": 1}, 401), ({"scope": "profile:read"}, 403)]:
        response = await account_client.post(
            "/api/v1/me/bootstrap", headers={"Authorization": "Bearer " + token_factory(claims)}
        )
        assert response.status_code == status
    assert await session.scalar(select(func.count()).select_from(Student)) == 0
