from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, StringConstraints

from lingora.modules.onboarding.contracts import CEFR, Contract, CorrectionMode

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]


class PrepareSession(Contract):
    lesson_id: UUID
    save_examples: bool = True


class Observation(Contract):
    skill: ShortText
    feedback: ShortText
    example: (
        Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]
        | None
    ) = None
    correction: (
        Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]
        | None
    ) = None


class CompleteSession(Contract):
    expected_version: int = Field(ge=1, strict=True)
    summary: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
    strengths: list[ShortText] = Field(default_factory=list, max_length=3)
    priorities: list[ShortText] = Field(default_factory=list, max_length=3)
    observations: list[Observation] = Field(
        default_factory=lambda: list[Observation](), max_length=6
    )


class SessionFeedback(Contract):
    summary: str
    strengths: list[str]
    priorities: list[str]
    observations: list[Observation]


class SessionView(Contract):
    id: UUID
    lesson_id: UUID
    status: Literal["READY", "IN_PROGRESS", "COMPLETED", "ABANDONED"]
    cefr: CEFR
    correction_mode: CorrectionMode
    save_examples: bool
    version: int
    created_at: datetime
    completed_at: datetime | None
    feedback: SessionFeedback | None


class SessionVersion(Contract):
    expected_version: int = Field(ge=1, strict=True)


class SessionPreferences(SessionVersion):
    correction_mode: CorrectionMode


class McpAccessView(Contract):
    enabled: bool
