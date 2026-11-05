import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from pydantic import SecretStr
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from lingora.core.config import Settings
from lingora.modules.learning.models import (
    Content,
    ExerciseAttempt,
    GenerationEvent,
    Lesson,
    LessonJob,
)
from lingora.modules.learning.provider import GenerationFailure
from lingora.modules.learning.worker import claim, run_once
from tests.auth_support import TokenFactory
from tests.integration.test_authenticated_accounts import account_client as account_client
from tests.integration.test_onboarding import owner as owner
from tests.learning_support import FakeProvider


@pytest.fixture
def auth_settings(auth_settings: Settings) -> Settings:
    return auth_settings.model_copy(update={"openai_api_key": SecretStr("test-only-never-sent")})


@pytest.fixture
async def source(session: AsyncSession) -> UUID:
    async with session.begin():
        content = Content(
            url=f"https://www.gov.uk/government/news/{uuid4()}",
            fingerprint=uuid4().hex,
            title="Community gardens grow",
            summary="A community garden opens in June. Volunteers will plant flowers together.",
            published_at=datetime(2026, 1, 1, tzinfo=UTC),
            source="GOV.UK",
            topics=["environment"],
            license_name="OGL-3.0",
            license_url="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
            attribution="Contains public sector information licensed under OGL v3.0.",
            available=True,
        )
        session.add(content)
        await session.flush()
        return content.id


@pytest.fixture
async def factory(session: AsyncSession) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(session.bind, expire_on_commit=False)


async def prepare(
    client: AsyncClient, owner: dict[str, str], source: UUID, key: UUID | None = None
) -> dict[str, object]:
    response = await client.post(
        "/api/v1/me/lessons",
        headers={**owner, "Idempotency-Key": str(key or uuid4())},
        json={"content_id": str(source)},
    )
    assert response.status_code == 202, response.text
    return response.json()


async def test_catalog_recommendation_and_level_use_explicit_preferences(
    account_client: AsyncClient, owner: dict[str, str], source: UUID
) -> None:
    await account_client.put(
        "/api/v1/me/profile",
        headers=owner,
        json={"expected_version": 0, "selected_cefr": "B1", "interests": ["Environment"]},
    )
    catalog = await account_client.get("/api/v1/me/content?topic=environment", headers=owner)
    assert catalog.status_code == 200
    item = next(x for x in catalog.json()["items"] if x["id"] == str(source))
    assert "environment" in item["recommendation_reason"]
    assert item["difficulty"] == "unrated" and item["license_name"] == "OGL-3.0"
    job = await prepare(account_client, owner, source)
    assert job["cefr"] == "B1"
    override = await account_client.post(
        "/api/v1/me/lessons",
        headers={**owner, "Idempotency-Key": str(uuid4())},
        json={"content_id": str(source), "cefr": "C1"},
    )
    assert override.json()["cefr"] == "C1"
    assert (await account_client.get("/api/v1/me/profile", headers=owner)).json()[
        "selected_cefr"
    ] == "B1"


async def test_concurrent_job_creation_and_keys_are_durable(
    account_client: AsyncClient, owner: dict[str, str], source: UUID, session: AsyncSession
) -> None:
    key = uuid4()
    jobs = await asyncio.gather(*[prepare(account_client, owner, source, key) for _ in range(6)])
    assert len({str(x["id"]) for x in jobs}) == 1
    assert jobs[0]["cefr"] == "A2"
    conflict = await account_client.post(
        "/api/v1/me/lessons",
        headers={**owner, "Idempotency-Key": str(key)},
        json={"content_id": str(source), "cefr": "B2"},
    )
    assert conflict.status_code == 409
    await prepare(account_client, owner, source)
    capped = await account_client.post(
        "/api/v1/me/lessons",
        headers={**owner, "Idempotency-Key": str(uuid4())},
        json={"content_id": str(source)},
    )
    assert capped.status_code == 429
    assert await session.scalar(select(func.count()).select_from(LessonJob)) == 2


async def test_worker_publishes_once_and_attempts_survive_reload(
    account_client: AsyncClient,
    owner: dict[str, str],
    source: UUID,
    factory: async_sessionmaker[AsyncSession],
    session: AsyncSession,
) -> None:
    job = await prepare(account_client, owner, source)
    fake = FakeProvider()
    assert await run_once(factory, fake, "test-model")
    assert not await run_once(factory, fake, "test-model")
    response = await account_client.get(f"/api/v1/me/lesson-jobs/{job['id']}", headers=owner)
    assert response.json()["status"] == "succeeded"
    identifier = response.json()["lesson_id"]
    lesson = await account_client.get(f"/api/v1/me/lessons/{identifier}", headers=owner)
    assert lesson.status_code == 200
    assert all(
        "correct_answers" not in x and "explanation" not in x and "evidence" not in x
        for x in lesson.json()["exercises"]
    )
    body = {
        "answers": [
            ["A garden"],
            ["plant"],
            ["A person who helps", "A planned piece of work"],
            ["June"],
            ["meet"],
        ]
    }
    key = str(uuid4())
    requests = await asyncio.gather(
        *[
            account_client.post(
                f"/api/v1/me/lessons/{identifier}/attempts",
                headers={**owner, "Idempotency-Key": key},
                json=body,
            )
            for _ in range(5)
        ]
    )
    assert {x.status_code for x in requests} == {200}
    assert len({x.json()["id"] for x in requests}) == 1
    assert requests[0].json()["correct"] == 5
    history = await account_client.get(f"/api/v1/me/lessons/{identifier}/attempts", headers=owner)
    assert len(history.json()) == 1
    assert (await account_client.get(f"/api/v1/me/lessons/{identifier}", headers=owner)).json()[
        "attempt_count"
    ] == 1
    body["answers"][0] = ["Wrong"]
    assert (
        await account_client.post(
            f"/api/v1/me/lessons/{identifier}/attempts",
            headers={**owner, "Idempotency-Key": key},
            json=body,
        )
    ).status_code == 409
    assert await session.scalar(select(func.count()).select_from(ExerciseAttempt)) == 1
    event = await session.scalar(select(GenerationEvent))
    assert event and event.outcome == "validated" and event.input_tokens == 100


async def test_cross_student_jobs_lessons_and_attempts_are_inaccessible(
    account_client: AsyncClient,
    owner: dict[str, str],
    source: UUID,
    factory: async_sessionmaker[AsyncSession],
    token_factory: TokenFactory,
) -> None:
    job = await prepare(account_client, owner, source)
    await run_once(factory, FakeProvider(), "test-model")
    data = (await account_client.get(f"/api/v1/me/lesson-jobs/{job['id']}", headers=owner)).json()
    other = {"Authorization": "Bearer " + token_factory({"sub": "auth0|another-student"})}
    await account_client.post("/api/v1/me/bootstrap", headers=other, json={})
    for path in [
        f"/lesson-jobs/{job['id']}",
        f"/lessons/{data['lesson_id']}",
        f"/lessons/{data['lesson_id']}/attempts",
    ]:
        assert (await account_client.get("/api/v1/me" + path, headers=other)).status_code == 404
    assert (
        await account_client.post(
            f"/api/v1/me/lessons/{data['lesson_id']}/attempts",
            headers={**other, "Idempotency-Key": str(uuid4())},
            json={"answers": [[""]] * 5},
        )
    ).status_code == 404
    assert (await account_client.get("/api/v1/me/lessons", headers=other)).json()["items"] == []


async def test_expired_lease_recovery_is_fenced(
    account_client: AsyncClient,
    owner: dict[str, str],
    source: UUID,
    factory: async_sessionmaker[AsyncSession],
    session: AsyncSession,
) -> None:
    job = await prepare(account_client, owner, source)
    first = await claim(factory)
    assert first
    async with session.begin():
        await session.execute(
            update(LessonJob)
            .where(LessonJob.id == first.id)
            .values(lease_until=datetime.now(UTC) - timedelta(seconds=1))
        )
    assert await run_once(factory, FakeProvider(), "test-model")
    async with factory() as check:
        row = await check.get(LessonJob, first.id)
        assert row and row.attempts == 2 and row.status == "succeeded" and row.lease_token is None
        assert await check.scalar(select(func.count()).select_from(Lesson)) == 1
    assert (await account_client.get(f"/api/v1/me/lesson-jobs/{job['id']}", headers=owner)).json()[
        "status"
    ] == "succeeded"


async def test_generation_failures_do_not_publish_and_retry_is_bounded(
    account_client: AsyncClient,
    owner: dict[str, str],
    source: UUID,
    factory: async_sessionmaker[AsyncSession],
    session: AsyncSession,
) -> None:
    class Failed(FakeProvider):
        async def generate(self, context: dict[str, object]):
            raise GenerationFailure("provider_timeout", retryable=True)

    await prepare(account_client, owner, source)
    for expected in [1, 2, 3]:
        assert await run_once(factory, Failed(), "test-model")
        async with session.begin():
            row = await session.scalar(select(LessonJob).execution_options(populate_existing=True))
            assert (
                row
                and row.attempts == expected
                and row.status == ("failed" if expected == 3 else "queued")
            )
            row.available_at = datetime.now(UTC) - timedelta(seconds=1)
    assert await session.scalar(select(func.count()).select_from(Lesson)) == 0
    assert await session.scalar(select(func.count()).select_from(GenerationEvent)) == 3


async def test_unavailable_source_and_unknown_identity_fields_are_rejected(
    account_client: AsyncClient, owner: dict[str, str], source: UUID, session: AsyncSession
) -> None:
    headers = {**owner, "Idempotency-Key": str(uuid4())}
    assert (
        await account_client.post(
            "/api/v1/me/lessons",
            headers=headers,
            json={"content_id": str(source), "student_id": str(uuid4())},
        )
    ).status_code == 422
    assert (
        await account_client.get("/api/v1/me/content?student_id=other", headers=owner)
    ).status_code == 422
    assert (
        await account_client.get("/api/v1/me/lessons?student_id=other", headers=owner)
    ).status_code == 422
    async with session.begin():
        await session.execute(update(Content).where(Content.id == source).values(available=False))
    assert (
        await account_client.post(
            "/api/v1/me/lessons", headers=headers, json={"content_id": str(source)}
        )
    ).status_code == 404


async def test_late_worker_cannot_overwrite_a_recovered_lease(
    account_client: AsyncClient,
    owner: dict[str, str],
    source: UUID,
    factory: async_sessionmaker[AsyncSession],
    session: AsyncSession,
) -> None:
    started, release = asyncio.Event(), asyncio.Event()

    class Slow(FakeProvider):
        async def generate(self, context: dict[str, object]):
            started.set()
            await release.wait()
            return await super().generate(context)

    await prepare(account_client, owner, source)
    task = asyncio.create_task(run_once(factory, Slow(), "slow-model"))
    await asyncio.wait_for(started.wait(), 5)
    async with session.begin():
        await session.execute(
            update(LessonJob).values(lease_until=datetime.now(UTC) - timedelta(seconds=1))
        )
    await run_once(factory, FakeProvider(), "winner-model")
    release.set()
    assert await task
    async with factory() as check:
        assert await check.scalar(select(func.count()).select_from(Lesson)) == 1
        outcomes = set(await check.scalars(select(GenerationEvent.outcome)))
        assert outcomes == {"validated", "lease_superseded"}


async def test_publication_transaction_rolls_back_and_worker_can_recover(
    account_client: AsyncClient,
    owner: dict[str, str],
    source: UUID,
    factory: async_sessionmaker[AsyncSession],
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await prepare(account_client, owner, source)
    with monkeypatch.context() as patch:

        def fail(*args: object, **kwargs: object) -> None:
            raise RuntimeError("simulated publication failure")

        patch.setattr("lingora.modules.learning.worker.Lesson", fail)
        with pytest.raises(RuntimeError):
            await run_once(factory, FakeProvider(), "test-model")
    async with session.begin():
        assert await session.scalar(select(func.count()).select_from(Lesson)) == 0
        assert await session.scalar(select(func.count()).select_from(GenerationEvent)) == 0
        await session.execute(
            update(LessonJob).values(lease_until=datetime.now(UTC) - timedelta(seconds=1))
        )
    assert await run_once(factory, FakeProvider(), "test-model")
    async with factory() as check:
        assert await check.scalar(select(func.count()).select_from(Lesson)) == 1
