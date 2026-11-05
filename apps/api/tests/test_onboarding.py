from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from sqlalchemy.exc import OperationalError

from lingora.modules.onboarding import application
from lingora.modules.onboarding.contracts import AssessmentFields, ProfileResponse, ProfileWrite
from tests.auth_support import TokenFactory


def test_empty_profile_and_explicit_unknown_level() -> None:
    profile = ProfileResponse()
    assert profile.version == 0
    assert profile.onboarding_status == "not_started"
    assert profile.selected_cefr is None
    assert profile.correction_mode == "balanced"
    assert ProfileWrite(expected_version=0, intent="finish").goals == []


@pytest.mark.parametrize(
    "data",
    [
        {"student_id": "someone-else"},
        {"sessions_per_week": 8},
        {"sessions_per_week": True},
        {"session_duration_minutes": 4},
        {"session_duration_minutes": 121},
        {"selected_cefr": "beginner"},
        {"goals": ["Travel", "travel"]},
        {"interests": [" "]},
        {"goals": [str(i) for i in range(11)]},
        {"preferred_name": "x" * 81},
        {"correction_mode": "always"},
        {"completed_at": "2026-11-01"},
    ],
)
def test_profile_validation(data: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        ProfileWrite.model_validate({"expected_version": 0, **data})


def test_original_assessment_scores_are_not_converted() -> None:
    record = AssessmentFields.model_validate(
        {
            "provider": "other",
            "test_name": "Example",
            "variant": "Receptive only",
            "taken_on": "2026-01-01",
            "overall_score": {"value": "005.50", "scale": "0–10"},
            "component_scores": [
                {"skill": "Reading", "value": "125–135", "scale": "original range"}
            ],
        }
    )
    assert record.overall_score is not None
    assert record.overall_score.value == "005.50"
    assert record.component_scores[0].value == "125–135"
    assert record.reported_cefr is None


@pytest.mark.parametrize(
    "extra",
    [
        {},
        {"overall_score": {"value": " "}},
        {"reported_cefr": "B3"},
        {"overall_score": {"value": 50}},
        {"reported_cefr": "B1", "student_id": "other"},
        {
            "reported_cefr": "B1",
            "taken_on": (datetime.now(UTC).date() + timedelta(days=1)).isoformat(),
        },
        {
            "component_scores": [
                {"skill": "Reading", "value": "1"},
                {"skill": "reading", "value": "2"},
            ]
        },
    ],
)
def test_assessment_validation(extra: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        AssessmentFields.model_validate(
            {"provider": "other", "test_name": "Test", "taken_on": "2026-01-01", **extra}
        )


async def test_database_outage_returns_sanitized_retryable_problem(
    authenticated_app: FastAPI, token_factory: TokenFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def unavailable(*args: Any, **kwargs: Any) -> None:
        raise OperationalError(
            "private SQL",
            {"preferred_name": "private-student-content"},
            Exception("database offline"),
        )

    monkeypatch.setattr(application, "read_profile", unavailable)
    async with AsyncClient(
        transport=ASGITransport(app=authenticated_app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/me/profile", headers={"Authorization": "Bearer " + token_factory()}
        )
    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/problem+json")
    assert "private" not in response.text
