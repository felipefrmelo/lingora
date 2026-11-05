from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from lingora.infrastructure.database import Base


class StudentProfile(Base):
    __tablename__ = "student_profiles"
    __table_args__ = (
        CheckConstraint("version >= 1", name="ck_profile_version"),
        CheckConstraint("sessions_per_week BETWEEN 1 AND 7", name="ck_profile_frequency"),
        CheckConstraint("session_duration_minutes BETWEEN 5 AND 120", name="ck_profile_duration"),
        CheckConstraint("selected_cefr IN ('A1','A2','B1','B2','C1','C2')", name="ck_profile_cefr"),
        CheckConstraint(
            "correction_mode IN ('free','balanced','intensive')", name="ck_profile_correction"
        ),
        CheckConstraint(
            "onboarding_status IN ('in_progress','skipped','completed')", name="ck_profile_status"
        ),
        CheckConstraint(
            "(onboarding_status = 'completed') = (completed_at IS NOT NULL)",
            name="ck_profile_completion",
        ),
        CheckConstraint(
            "jsonb_typeof(goals) = 'array' AND jsonb_array_length(goals) <= 10",
            name="ck_profile_goals",
        ),
        CheckConstraint(
            "jsonb_typeof(interests) = 'array' AND jsonb_array_length(interests) <= 10",
            name="ck_profile_interests",
        ),
    )

    student_id: Mapped[UUID] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), primary_key=True
    )
    preferred_name: Mapped[str | None] = mapped_column(String(80))
    native_language: Mapped[str | None] = mapped_column(String(80))
    goals: Mapped[list[str]] = mapped_column(JSONB, default=list)
    interests: Mapped[list[str]] = mapped_column(JSONB, default=list)
    selected_cefr: Mapped[str | None] = mapped_column(String(2))
    sessions_per_week: Mapped[int | None] = mapped_column(Integer)
    session_duration_minutes: Mapped[int | None] = mapped_column(Integer)
    correction_mode: Mapped[str] = mapped_column(String(16), default="balanced")
    onboarding_status: Mapped[str] = mapped_column(String(16))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(default=1)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class PlacementAssessment(Base):
    __tablename__ = "placement_assessments"
    __table_args__ = (
        CheckConstraint("version >= 1", name="ck_assessment_version"),
        CheckConstraint(
            "provider IN ('englishscore','ef_set','other')", name="ck_assessment_provider"
        ),
        CheckConstraint(
            "reported_cefr IN ('A1','A2','B1','B2','C1','C2')", name="ck_assessment_cefr"
        ),
        CheckConstraint(
            "jsonb_typeof(component_scores) = 'array' "
            "AND jsonb_array_length(component_scores) <= 20",
            name="ck_assessment_components",
        ),
        CheckConstraint(
            "overall_score IS NOT NULL OR jsonb_array_length(component_scores) > 0 "
            "OR reported_cefr IS NOT NULL",
            name="ck_assessment_result",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    student_id: Mapped[UUID] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(32))
    test_name: Mapped[str] = mapped_column(String(120))
    variant: Mapped[str | None] = mapped_column(String(120))
    taken_on: Mapped[date] = mapped_column(Date)
    overall_score: Mapped[dict[str, Any] | None] = mapped_column(JSONB(none_as_null=True))
    component_scores: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    reported_cefr: Mapped[str | None] = mapped_column(String(2))
    version: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AssessmentCreation(Base):
    """Durable creation receipts survive edits/deletion, preventing retry resurrection."""

    __tablename__ = "assessment_creations"
    student_id: Mapped[UUID] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), primary_key=True
    )
    key: Mapped[UUID] = mapped_column(primary_key=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    assessment_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("placement_assessments.id", ondelete="SET NULL"), index=True
    )
