from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from lingora.modules.onboarding.contracts import AssessmentFields, ProfileResponse, ProfileWrite


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
