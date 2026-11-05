from datetime import UTC, date, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

CEFR = Literal["A1", "A2", "B1", "B2", "C1", "C2"]
CorrectionMode = Literal["free", "balanced", "intensive"]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class ProfileFields(Contract):
    preferred_name: str | None = Field(default=None, max_length=80)
    native_language: str | None = Field(default=None, max_length=80)
    goals: list[ShortText] = Field(default_factory=list, max_length=10)
    interests: list[ShortText] = Field(default_factory=list, max_length=10)
    selected_cefr: CEFR | None = None
    sessions_per_week: int | None = Field(default=None, ge=1, le=7, strict=True)
    session_duration_minutes: int | None = Field(default=None, ge=5, le=120, strict=True)
    correction_mode: CorrectionMode = "balanced"

    @field_validator("preferred_name", "native_language")
    @classmethod
    def optional_text(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None

    @field_validator("goals", "interests")
    @classmethod
    def unique_items(cls, values: list[str]) -> list[str]:
        if len({item.casefold() for item in values}) != len(values):
            raise ValueError("Remove duplicate entries")
        return values


class ProfileWrite(ProfileFields):
    expected_version: int = Field(ge=0, strict=True)
    intent: Literal["save", "resume", "skip", "finish"] = "save"


class ProfileResponse(ProfileFields):
    version: int = 0
    onboarding_status: Literal["not_started", "in_progress", "skipped", "completed"] = "not_started"
    completed_at: datetime | None = None
    updated_at: datetime | None = None


class Score(Contract):
    # Preserve provider formatting (including leading zeroes, ranges, and scale labels).
    value: str = Field(min_length=1, max_length=64)
    scale: str | None = Field(default=None, max_length=100)

    @field_validator("value")
    @classmethod
    def nonblank_score(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("A score cannot be blank")
        return value


class ComponentScore(Score):
    skill: ShortText
    reported_cefr: CEFR | None = None


class AssessmentFields(Contract):
    provider: Literal["englishscore", "ef_set", "other"]
    test_name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)
    ]
    variant: str | None = Field(default=None, max_length=120)
    taken_on: date
    overall_score: Score | None = None
    component_scores: list[ComponentScore] = Field(
        default_factory=lambda: list[ComponentScore](), max_length=20
    )
    reported_cefr: CEFR | None = None

    @field_validator("taken_on")
    @classmethod
    def no_future_results(cls, value: date) -> date:
        if value > datetime.now(UTC).date():
            raise ValueError("An assessment date cannot be in the future")
        return value

    @model_validator(mode="after")
    def has_result(self) -> "AssessmentFields":
        if not (self.overall_score or self.component_scores or self.reported_cefr):
            raise ValueError("Record at least one score or the test's reported CEFR")
        labels = [score.skill.casefold() for score in self.component_scores]
        if len(set(labels)) != len(labels):
            raise ValueError("Component labels must be unique")
        return self


class AssessmentWrite(AssessmentFields):
    expected_version: int = Field(ge=1, strict=True)


class AssessmentResponse(AssessmentFields):
    id: UUID
    version: int
    created_at: datetime
    updated_at: datetime
    self_reported: Literal[True] = True


class AssessmentList(Contract):
    items: list[AssessmentResponse]
    total: int


class VersionConflict(Exception):
    pass


class ResourceNotFound(Exception):
    pass


class CreationGone(Exception):
    pass
