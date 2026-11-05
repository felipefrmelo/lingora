import asyncio
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from lingora.modules.onboarding.models import (
    AssessmentCreation,
    PlacementAssessment,
    StudentProfile,
)
from tests.auth_support import TokenFactory
from tests.integration.test_authenticated_accounts import account_client as account_client


@pytest.fixture
async def owner(account_client: AsyncClient, token_factory: TokenFactory) -> dict[str, str]:
    headers = {"Authorization": "Bearer " + token_factory()}
    assert (
        await account_client.post("/api/v1/me/bootstrap", headers=headers, json={})
    ).status_code == 200
    return headers


def result(**changes: object) -> dict[str, object]:
    return {
        "provider": "englishscore",
        "test_name": "EnglishScore",
        "variant": "Core Skills",
        "taken_on": "2026-01-01",
        "overall_score": {"value": "0400", "scale": "0–599"},
        "component_scores": [{"skill": "Reading", "value": "399", "scale": "0–599"}],
        "reported_cefr": "B1",
        **changes,
    }


async def test_profile_default_does_not_write(
    account_client: AsyncClient, owner: dict[str, str], session: AsyncSession
) -> None:
    response = await account_client.get("/api/v1/me/profile", headers=owner)
    assert response.status_code == 200
    assert response.json()["onboarding_status"] == "not_started"
    assert response.json()["version"] == 0
    assert await session.scalar(select(func.count()).select_from(StudentProfile)) == 0


async def test_profile_draft_skip_resume_finish_and_edit(
    account_client: AsyncClient, owner: dict[str, str]
) -> None:
    body = {
        "expected_version": 0,
        "preferred_name": " Ana ",
        "selected_cefr": "A2",
        "goals": ["Travel"],
        "interests": ["Art"],
        "native_language": "Portuguese",
    }
    first = await account_client.put("/api/v1/me/profile", headers=owner, json=body)
    assert first.status_code == 200
    assert first.json()["preferred_name"] == "Ana"
    assert first.json()["onboarding_status"] == "in_progress"
    assert (await account_client.get("/api/v1/me/profile", headers=owner)).json() == first.json()
    for version, intent, status in [
        (1, "skip", "skipped"),
        (2, "save", "skipped"),
        (3, "resume", "in_progress"),
        (4, "finish", "completed"),
        (5, "save", "completed"),
    ]:
        response = await account_client.put(
            "/api/v1/me/profile",
            headers=owner,
            json={**body, "expected_version": version, "intent": intent},
        )
        assert response.status_code == 200
        assert response.json()["version"] == version + 1
        assert response.json()["onboarding_status"] == status
    completed = response.json()["completed_at"]
    response = await account_client.put(
        "/api/v1/me/profile", headers=owner, json={"expected_version": 6, "intent": "finish"}
    )
    assert response.json()["completed_at"] == completed
    assert response.json()["selected_cefr"] is None


async def test_empty_completion_and_stale_write_preserves_data(
    account_client: AsyncClient, owner: dict[str, str]
) -> None:
    first = await account_client.put(
        "/api/v1/me/profile", headers=owner, json={"expected_version": 0, "intent": "finish"}
    )
    assert first.json()["onboarding_status"] == "completed"
    stale = await account_client.put(
        "/api/v1/me/profile",
        headers=owner,
        json={"expected_version": 0, "preferred_name": "Lost edit"},
    )
    assert stale.status_code == 409
    assert stale.headers["content-type"].startswith("application/problem+json")
    assert (await account_client.get("/api/v1/me/profile", headers=owner)).json() == first.json()


async def test_concurrent_profile_edits_have_one_winner(
    account_client: AsyncClient, owner: dict[str, str]
) -> None:
    responses = await asyncio.gather(
        *[
            account_client.put(
                "/api/v1/me/profile",
                headers=owner,
                json={"expected_version": 0, "preferred_name": f"Edit {i}"},
            )
            for i in range(4)
        ]
    )
    assert sorted(r.status_code for r in responses) == [200, 409, 409, 409]
    saved = (await account_client.get("/api/v1/me/profile", headers=owner)).json()
    assert saved == next(r.json() for r in responses if r.status_code == 200)


async def test_assessment_idempotency_concurrency_and_no_orphans(
    account_client: AsyncClient, owner: dict[str, str], session: AsyncSession
) -> None:
    headers = {**owner, "Idempotency-Key": str(uuid4())}
    responses = await asyncio.gather(
        *[
            account_client.post("/api/v1/me/assessments", headers=headers, json=result())
            for _ in range(5)
        ]
    )
    assert sorted(r.status_code for r in responses) == [200, 200, 200, 200, 201]
    assert len({r.json()["id"] for r in responses}) == 1
    assert await session.scalar(select(func.count()).select_from(PlacementAssessment)) == 1
    assert await session.scalar(select(func.count()).select_from(AssessmentCreation)) == 1
    bad = await account_client.post(
        "/api/v1/me/assessments", headers=headers, json=result(reported_cefr="B2")
    )
    assert bad.status_code == 409


async def test_assessment_crud_preserves_raw_scores_and_selected_level(
    account_client: AsyncClient, owner: dict[str, str]
) -> None:
    await account_client.put(
        "/api/v1/me/profile", headers=owner, json={"expected_version": 0, "selected_cefr": "A2"}
    )
    headers = {**owner, "Idempotency-Key": str(uuid4())}
    created = await account_client.post("/api/v1/me/assessments", headers=headers, json=result())
    item = created.json()
    assert item["overall_score"]["value"] == "0400"
    assert item["self_reported"] is True
    path = "/api/v1/me/assessments/" + item["id"]
    updated = await account_client.put(
        path, headers=owner, json={**result(reported_cefr="C1"), "expected_version": 1}
    )
    assert updated.status_code == 200
    assert updated.json()["version"] == 2
    assert (
        await account_client.put(path, headers=owner, json={**result(), "expected_version": 1})
    ).status_code == 409
    listed = await account_client.get("/api/v1/me/assessments?limit=1&offset=0", headers=owner)
    assert listed.json()["items"] == [updated.json()]
    assert listed.json()["total"] == 1
    assert (
        await account_client.delete(path + "?expected_version=1", headers=owner)
    ).status_code == 409
    assert (
        await account_client.delete(path + "?expected_version=2", headers=owner)
    ).status_code == 204
    assert (
        await account_client.post("/api/v1/me/assessments", headers=headers, json=result())
    ).status_code == 410
    assert (await account_client.get("/api/v1/me/assessments", headers=owner)).json()["items"] == []
    assert (await account_client.get("/api/v1/me/profile", headers=owner)).json()[
        "selected_cefr"
    ] == "A2"


async def test_cross_student_resources_are_hidden(
    account_client: AsyncClient, owner: dict[str, str], token_factory: TokenFactory
) -> None:
    first = await account_client.post(
        "/api/v1/me/assessments", headers={**owner, "Idempotency-Key": str(uuid4())}, json=result()
    )
    other = {"Authorization": "Bearer " + token_factory({"sub": "auth0|other"})}
    await account_client.post("/api/v1/me/bootstrap", headers=other, json={})
    assert (await account_client.get("/api/v1/me/assessments", headers=other)).json()["total"] == 0
    path = "/api/v1/me/assessments/" + first.json()["id"]
    assert (
        await account_client.put(path, headers=other, json={**result(), "expected_version": 1})
    ).status_code == 404
    assert (
        await account_client.delete(path + "?expected_version=1", headers=other)
    ).status_code == 404
    await account_client.put(
        "/api/v1/me/profile",
        headers=owner,
        json={"expected_version": 0, "preferred_name": "Private"},
    )
    assert (await account_client.get("/api/v1/me/profile", headers=other)).json()[
        "preferred_name"
    ] is None


async def test_scope_validation_and_rejected_identity_inputs(
    account_client: AsyncClient, owner: dict[str, str], token_factory: TokenFactory
) -> None:
    assert (await account_client.get("/api/v1/me/profile")).status_code == 401
    read_only = {"Authorization": "Bearer " + token_factory({"scope": "profile:read"})}
    assert (
        await account_client.put(
            "/api/v1/me/profile", headers=read_only, json={"expected_version": 0}
        )
    ).status_code == 403
    assert (
        await account_client.put(
            "/api/v1/me/profile", headers=owner, json={"expected_version": 0, "student_id": "other"}
        )
    ).status_code == 422
    assert (
        await account_client.get("/api/v1/me/assessments?student_id=other", headers=owner)
    ).status_code == 422
    assert (
        await account_client.post("/api/v1/me/assessments", headers=owner, json=result())
    ).status_code == 422


async def test_new_profile_reads_require_bootstrap(
    account_client: AsyncClient, token_factory: TokenFactory
) -> None:
    headers = {"Authorization": "Bearer " + token_factory({"sub": "unprovisioned"})}
    assert (await account_client.get("/api/v1/me/profile", headers=headers)).status_code == 404


async def test_database_constraint_failure_rolls_back_profile_changes(
    account_client: AsyncClient, owner: dict[str, str], session: AsyncSession
) -> None:
    first = await account_client.put(
        "/api/v1/me/profile",
        headers=owner,
        json={"expected_version": 0, "preferred_name": "Original"},
    )
    with pytest.raises(IntegrityError):
        async with session.begin():
            await session.execute(
                update(StudentProfile).values(
                    preferred_name="Should roll back", sessions_per_week=99
                )
            )
    assert (await account_client.get("/api/v1/me/profile", headers=owner)).json() == first.json()
