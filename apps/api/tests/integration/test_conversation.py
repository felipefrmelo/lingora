import asyncio
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from lingora.modules.conversation import application
from lingora.modules.conversation.contracts import CompleteSession, Observation
from lingora.modules.conversation.models import ConversationEvent, ConversationSession
from lingora.modules.identity.principal import AuthenticatedPrincipal
from lingora.modules.learning.worker import run_once
from lingora.modules.onboarding.contracts import VersionConflict
from tests.auth_support import ISSUER, TokenFactory
from tests.integration.test_authenticated_accounts import account_client as account_client
from tests.integration.test_learning import auth_settings as auth_settings
from tests.integration.test_learning import factory as factory
from tests.integration.test_learning import prepare
from tests.integration.test_learning import source as source
from tests.integration.test_onboarding import owner as owner
from tests.learning_support import FakeProvider


@pytest.fixture
async def lesson_id(
    account_client: AsyncClient,
    owner: dict[str, str],
    source: UUID,
    factory: async_sessionmaker[AsyncSession],
) -> UUID:
    job = await prepare(account_client, owner, source)
    assert await run_once(factory, FakeProvider(), "test-model")
    response = await account_client.get(f"/api/v1/me/lesson-jobs/{job['id']}", headers=owner)
    return UUID(response.json()["lesson_id"])


async def test_preparation_is_idempotent_and_isolated(
    account_client: AsyncClient, owner: dict[str, str], lesson_id: UUID, token_factory: TokenFactory
) -> None:
    key = str(uuid4())
    headers = {**owner, "Idempotency-Key": key}
    body = {"lesson_id": str(lesson_id), "save_examples": False}
    results = await asyncio.gather(
        *[
            account_client.post("/api/v1/me/conversation-sessions", headers=headers, json=body)
            for _ in range(4)
        ]
    )
    assert {r.status_code for r in results} == {200}
    assert len({r.json()["id"] for r in results}) == 1
    result = results[0].json()
    assert result["status"] == "READY" and result["cefr"] == "A2"
    conflict = await account_client.post(
        "/api/v1/me/conversation-sessions", headers=headers, json={**body, "save_examples": True}
    )
    assert conflict.status_code == 409
    other = {"Authorization": "Bearer " + token_factory({"sub": "auth0|someone-else"})}
    await account_client.post("/api/v1/me/bootstrap", headers=other, json={})
    assert (
        await account_client.get("/api/v1/me/conversation-sessions/" + result["id"], headers=other)
    ).status_code == 404
    assert (
        await account_client.get("/api/v1/me/conversation-sessions", headers=other)
    ).json() == []
    assert (
        await account_client.post(
            "/api/v1/me/conversation-sessions",
            headers=headers,
            json={**body, "student_id": str(uuid4())},
        )
    ).status_code == 422


async def test_completion_is_atomic_and_replayable(
    account_client: AsyncClient, owner: dict[str, str], lesson_id: UUID, session: AsyncSession
) -> None:
    result = await account_client.post(
        "/api/v1/me/conversation-sessions",
        headers={**owner, "Idempotency-Key": str(uuid4())},
        json={"lesson_id": str(lesson_id), "save_examples": False},
    )
    identifier = UUID(result.json()["id"])
    principal = AuthenticatedPrincipal(
        issuer=ISSUER, subject="auth0|student-one", scopes=frozenset({"profile:write"})
    )
    key = uuid4()
    invalid_payloads = [
        CompleteSession(expected_version=1, summary='You said "I go yesterday".'),
        CompleteSession(expected_version=1, summary="Good work", strengths=["You said 'I go'."]),
        CompleteSession(expected_version=1, summary="Good work", priorities=["Change ‘I go’."]),
        CompleteSession(
            expected_version=1,
            summary="Good work",
            observations=[Observation(skill="grammar", feedback="You said «I go».")],
        ),
        CompleteSession(
            expected_version=1,
            summary="Good work",
            observations=[
                Observation(
                    skill="grammar", feedback="Try the past tense", example="I go yesterday"
                )
            ],
        ),
    ]
    for invalid in invalid_payloads:
        with pytest.raises(application.ExamplesDisabled):
            await application.change(
                session, principal, identifier, 1, "complete", key, completion=invalid
            )
    saved = CompleteSession(
        expected_version=1, summary="Good work", priorities=["Don't omit past tense"]
    )
    completed = await application.change(
        session, principal, identifier, 1, "complete", key, completion=saved
    )
    repeated = await application.change(
        session, principal, identifier, 1, "complete", key, completion=saved
    )
    assert completed == repeated and completed.status == "COMPLETED" and completed.version == 2
    with pytest.raises(VersionConflict):
        await application.change(
            session,
            principal,
            identifier,
            1,
            "complete",
            key,
            completion=CompleteSession(expected_version=1, summary="Different"),
        )
    async with session.begin():
        assert await session.scalar(select(func.count()).select_from(ConversationSession)) == 1
        assert await session.scalar(select(func.count()).select_from(ConversationEvent)) == 2
    history = await account_client.get(
        f"/api/v1/me/conversation-sessions/{identifier}", headers=owner
    )
    assert history.json()["feedback"]["summary"] == "Good work"


async def test_mcp_access_defaults_disabled_and_revokes_older_tokens(
    account_client: AsyncClient, owner: dict[str, str], session: AsyncSession
) -> None:
    from datetime import UTC, datetime

    from lingora.modules.conversation import access
    from lingora.modules.identity.principal import AuthorizationDenied

    path = "/api/v1/me/mcp-access"
    assert (await account_client.get(path, headers=owner)).json() == {"enabled": False}
    old = AuthenticatedPrincipal(
        issuer=ISSUER,
        subject="auth0|student-one",
        scopes=frozenset(),
        issued_at=int(datetime.now(UTC).timestamp()) - 100,
    )
    with pytest.raises(AuthorizationDenied):
        await access.authorize(session, old)
    assert (await account_client.put(path, headers=owner, json={"enabled": True})).json()["enabled"]
    await access.authorize(session, old)
    assert not (await account_client.put(path, headers=owner, json={"enabled": False})).json()[
        "enabled"
    ]
    with pytest.raises(AuthorizationDenied):
        await access.authorize(session, old)
    await account_client.put(path, headers=owner, json={"enabled": True})
    with pytest.raises(AuthorizationDenied):
        await access.authorize(session, old)
    fresh = AuthenticatedPrincipal(
        issuer=ISSUER,
        subject="auth0|student-one",
        scopes=frozenset(),
        issued_at=int(datetime.now(UTC).timestamp()) + 1,
    )
    await access.authorize(session, fresh)
