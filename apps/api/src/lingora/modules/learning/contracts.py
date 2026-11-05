"""Validated lesson documents, public views, and deterministic grading contracts."""

import re
import unicodedata
from datetime import datetime
from random import SystemRandom
from typing import Any, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from lingora.modules.onboarding.contracts import CEFR as Cefr

PROMPT_VERSION = "lesson-v1"
SCHEMA_VERSION = "1"
Kind = Literal["choice", "gap", "matching", "comprehension", "short_answer"]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class Vocabulary(Contract):
    term: str = Field(min_length=1, max_length=80)
    meaning: str = Field(min_length=1, max_length=300)


class ExerciseView(Contract):
    kind: Kind
    prompt: str = Field(min_length=5, max_length=800)
    options: list[str] = Field(max_length=6)
    parts: list[str] = Field(max_length=6)
    skill: str = Field(min_length=3, max_length=120)


class Exercise(ExerciseView):
    correct_answers: list[str] = Field(min_length=1, max_length=6)
    explanation: str = Field(min_length=10, max_length=1000)
    evidence: str = Field(max_length=500)

    @model_validator(mode="after")
    def validate_key(self) -> Self:
        if any(
            not x.strip() or len(x) > 300 for x in self.options + self.parts + self.correct_answers
        ):
            raise ValueError("Exercise values must be nonempty and bounded")
        if len(set(map(normalize, self.options))) != len(self.options):
            raise ValueError("Options must be distinct")
        if self.kind == "choice":
            if (
                len(self.options) < 3
                or len(self.correct_answers) != 1
                or self.correct_answers[0] not in self.options
            ):
                raise ValueError("Choice requires options and exactly one matching answer")
        elif self.kind == "matching":
            if not 2 <= len(self.parts) == len(self.options) == len(
                self.correct_answers
            ) <= 6 or sorted(self.options) != sorted(self.correct_answers):
                raise ValueError("Matching requires a complete bijection")
            if len(set(map(normalize, self.parts))) != len(self.parts):
                raise ValueError("Matching terms must be distinct")
        elif self.options or self.parts:
            raise ValueError("Text exercises have no options or parts")
        if self.kind == "gap" and re.findall(r"_+", self.prompt) != ["___"]:
            raise ValueError("Gap requires exactly one blank")
        if len(set(map(normalize, self.correct_answers))) != len(self.correct_answers):
            raise ValueError("Accepted answers must be distinct")
        if self.kind in {"gap", "comprehension", "short_answer"} and any(
            len(answer.split()) > 8 for answer in self.correct_answers
        ):
            raise ValueError("Exact-match questions require short answer phrases")
        if self.kind == "choice" and self.parts:
            raise ValueError("Choice exercises have no matching parts")
        if self.kind == "comprehension" and not self.evidence.strip():
            raise ValueError("Comprehension requires supporting evidence")
        return self


class LessonDraft(Contract):
    title: str = Field(min_length=5, max_length=160)
    objectives: list[str] = Field(min_length=2, max_length=4)
    reading: str = Field(min_length=250, max_length=6000)
    vocabulary: list[Vocabulary] = Field(min_length=3, max_length=8)
    exercises: list[Exercise] = Field(min_length=5, max_length=5)
    discussion: list[str] = Field(min_length=2, max_length=4)

    @model_validator(mode="after")
    def educational_checks(self) -> Self:
        if {e.kind for e in self.exercises} != {
            "choice",
            "gap",
            "matching",
            "comprehension",
            "short_answer",
        }:
            raise ValueError("Include each exercise type exactly once")
        for value in self.objectives + self.discussion:
            if not 5 <= len(value.strip()) <= 500:
                raise ValueError("Learning instructions must be nonempty and bounded")
        for exercise in self.exercises:
            if exercise.evidence and exercise.evidence not in self.reading:
                raise ValueError("Evidence must be a verbatim passage from the reading")
        for word in self.vocabulary:
            if normalize(word.term) not in normalize(self.reading):
                raise ValueError("Vocabulary must occur in the reading")
        return self


class ContentView(Contract):
    id: UUID
    title: str
    url: str
    published_at: datetime
    source: str
    license_name: str
    license_url: str
    attribution: str
    summary: str
    topics: list[str]
    language: Literal["en"] = "en"
    difficulty: Literal["unrated"] = "unrated"
    recommendation_reason: str | None = None


class Catalog(Contract):
    items: list[ContentView]
    total: int
    generation_available: bool


class GenerateLesson(Contract):
    content_id: UUID
    cefr: Cefr | None = None


class JobView(Contract):
    id: UUID
    content_id: UUID
    status: Literal["queued", "running", "succeeded", "failed"]
    cefr: Cefr
    level_reason: str
    lesson_id: UUID | None
    error_code: str | None
    created_at: datetime


class LessonView(Contract):
    id: UUID
    created_at: datetime
    cefr: Cefr
    level_reason: str
    source: ContentView
    title: str
    objectives: list[str]
    reading: str
    vocabulary: list[Vocabulary]
    exercises: list[ExerciseView]
    discussion: list[str]
    prompt_version: str
    schema_version: str
    attempt_count: int


class LessonList(Contract):
    items: list[JobView]
    total: int


class SubmitAttempt(Contract):
    answers: list[list[str]] = Field(min_length=5, max_length=5)

    @model_validator(mode="after")
    def bounded_answers(self) -> Self:
        if any(len(a) > 6 or any(len(x) > 300 for x in a) for a in self.answers):
            raise ValueError("Answers exceed the supported size")
        return self


class ExerciseFeedback(Contract):
    correct: bool
    expected: list[str]
    explanation: str
    skill: str


class AttemptView(Contract):
    id: UUID
    lesson_id: UUID
    created_at: datetime
    answers: list[list[str]]
    results: list[ExerciseFeedback]
    correct: int
    total: int


def normalize(value: str) -> str:
    # Predictable exact matching; no subjective or model-based proficiency grade.
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value).strip()).casefold()


def grade(draft: LessonDraft, submission: SubmitAttempt) -> list[ExerciseFeedback]:
    results: list[ExerciseFeedback] = []
    for exercise, answers in zip(draft.exercises, submission.answers, strict=True):
        expected = list(map(normalize, exercise.correct_answers))
        actual = list(map(normalize, answers))
        correct = (
            actual == expected
            if exercise.kind == "matching"
            else len(actual) == 1 and actual[0] in expected
        )
        results.append(
            ExerciseFeedback(
                correct=correct,
                expected=exercise.correct_answers,
                explanation=exercise.explanation,
                skill=exercise.skill,
            )
        )
    return results


class LearningUnavailable(Exception):
    pass


class QueueFull(Exception):
    pass


def reading_prefix(context: dict[str, Any]) -> str:
    source = context["source"]
    return f"News brief: {source['title']} — {source['summary']}\n\nImagined practice: "


def assemble_lesson(document: LessonDraft, context: dict[str, Any]) -> LessonDraft:
    # Trusted code owns attribution and presentation, rather than asking a model to copy/shuffle.
    prefix = reading_prefix(context)
    result = document.model_copy(deep=True)
    if not result.reading.startswith(prefix):
        result.reading = prefix + result.reading
    for exercise in result.exercises:
        if exercise.kind == "matching" and exercise.options == exercise.correct_answers:
            SystemRandom().shuffle(exercise.options)
            if exercise.options == exercise.correct_answers:
                exercise.options = exercise.options[1:] + exercise.options[:1]
    return LessonDraft.model_validate(result.model_dump())
