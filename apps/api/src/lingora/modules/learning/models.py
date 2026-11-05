from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from lingora.infrastructure.database import Base
from lingora.modules.identity.models import Student


class Content(Base):
    __tablename__ = "contents"
    __table_args__ = (
        CheckConstraint("length(summary) BETWEEN 40 AND 8000", name="content_summary"),
        CheckConstraint("license_name = 'OGL-3.0'", name="content_license"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    url: Mapped[str] = mapped_column(String(1000), unique=True)
    fingerprint: Mapped[str] = mapped_column(String(64), unique=True)
    title: Mapped[str] = mapped_column(String(300))
    summary: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(120))
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    topics: Mapped[list[str]] = mapped_column(JSONB)
    license_name: Mapped[str] = mapped_column(String(32))
    license_url: Mapped[str] = mapped_column(String(300))
    attribution: Mapped[str] = mapped_column(String(300))
    available: Mapped[bool] = mapped_column(default=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LessonJob(Base):
    __tablename__ = "lesson_jobs"
    __table_args__ = (
        UniqueConstraint("student_id", "key"),
        CheckConstraint("status IN ('queued','running','succeeded','failed')", name="job_status"),
        CheckConstraint("attempts BETWEEN 0 AND 3", name="job_attempts"),
        CheckConstraint("cefr IN ('A1','A2','B1','B2','C1','C2')", name="job_cefr"),
        CheckConstraint("(status = 'running') = (lease_token IS NOT NULL)", name="job_lease"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    student_id: Mapped[UUID] = mapped_column(ForeignKey(Student.id, ondelete="CASCADE"), index=True)
    key: Mapped[UUID] = mapped_column()
    request_hash: Mapped[str] = mapped_column(String(64))
    content_id: Mapped[UUID] = mapped_column(ForeignKey("contents.id"))
    context: Mapped[dict[str, Any]] = mapped_column(JSONB)
    cefr: Mapped[str] = mapped_column(String(2))
    level_reason: Mapped[str] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(16), default="queued", index=True)
    attempts: Mapped[int] = mapped_column(default=0)
    lease_token: Mapped[UUID | None] = mapped_column()
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    error_code: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Lesson(Base):
    """An immutable versioned document; answer keys are never in the learner GET view."""

    __tablename__ = "lessons"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("lesson_jobs.id", ondelete="CASCADE"), unique=True
    )
    student_id: Mapped[UUID] = mapped_column(ForeignKey(Student.id, ondelete="CASCADE"), index=True)
    document: Mapped[dict[str, Any]] = mapped_column(JSONB)
    source_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB)
    prompt_version: Mapped[str] = mapped_column(String(32))
    schema_version: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ExerciseAttempt(Base):
    __tablename__ = "exercise_attempts"
    __table_args__ = (
        UniqueConstraint("student_id", "key"),
        CheckConstraint("total = 5 AND correct BETWEEN 0 AND total", name="attempt_grade"),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    lesson_id: Mapped[UUID] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), index=True
    )
    student_id: Mapped[UUID] = mapped_column(ForeignKey(Student.id, ondelete="CASCADE"), index=True)
    key: Mapped[UUID] = mapped_column()
    request_hash: Mapped[str] = mapped_column(String(64))
    answers: Mapped[list[list[str]]] = mapped_column(JSONB)
    results: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    correct: Mapped[int] = mapped_column()
    total: Mapped[int] = mapped_column(default=5)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GenerationEvent(Base):
    """Operational metadata only: never prompts, answers, provider bodies, or names."""

    __tablename__ = "generation_events"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    job_id: Mapped[UUID] = mapped_column(
        ForeignKey("lesson_jobs.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(32), default="openai")
    model: Mapped[str] = mapped_column(String(100))
    outcome: Mapped[str] = mapped_column(String(32))
    latency_ms: Mapped[int] = mapped_column()
    input_tokens: Mapped[int | None] = mapped_column()
    output_tokens: Mapped[int | None] = mapped_column()
    estimated_cost_microusd: Mapped[int | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
