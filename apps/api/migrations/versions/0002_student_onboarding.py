"""student_onboarding

Revision ID: 0002
Revises: 0001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "placement_assessments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("test_name", sa.String(length=120), nullable=False),
        sa.Column("variant", sa.String(length=120), nullable=True),
        sa.Column("taken_on", sa.Date(), nullable=False),
        sa.Column(
            "overall_score",
            postgresql.JSONB(none_as_null=True, astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("component_scores", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("reported_cefr", sa.String(length=2), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "jsonb_typeof(component_scores) = 'array' "
            "AND jsonb_array_length(component_scores) <= 20",
            name=op.f("ck_placement_assessments_ck_assessment_components"),
        ),
        sa.CheckConstraint(
            "provider IN ('englishscore','ef_set','other')",
            name=op.f("ck_placement_assessments_ck_assessment_provider"),
        ),
        sa.CheckConstraint(
            "reported_cefr IN ('A1','A2','B1','B2','C1','C2')",
            name=op.f("ck_placement_assessments_ck_assessment_cefr"),
        ),
        sa.CheckConstraint(
            "overall_score IS NOT NULL OR jsonb_array_length(component_scores) > 0 "
            "OR reported_cefr IS NOT NULL",
            name=op.f("ck_placement_assessments_ck_assessment_result"),
        ),
        sa.CheckConstraint(
            "version >= 1", name=op.f("ck_placement_assessments_ck_assessment_version")
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["students.id"],
            name=op.f("fk_placement_assessments_student_id_students"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_placement_assessments")),
    )
    op.create_index(
        op.f("ix_placement_assessments_student_id"),
        "placement_assessments",
        ["student_id"],
        unique=False,
    )
    op.create_table(
        "student_profiles",
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("preferred_name", sa.String(length=80), nullable=True),
        sa.Column("native_language", sa.String(length=80), nullable=True),
        sa.Column("goals", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("interests", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("selected_cefr", sa.String(length=2), nullable=True),
        sa.Column("sessions_per_week", sa.Integer(), nullable=True),
        sa.Column("session_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("correction_mode", sa.String(length=16), nullable=False),
        sa.Column("onboarding_status", sa.String(length=16), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(onboarding_status = 'completed') = (completed_at IS NOT NULL)",
            name=op.f("ck_student_profiles_ck_profile_completion"),
        ),
        sa.CheckConstraint(
            "correction_mode IN ('free','balanced','intensive')",
            name=op.f("ck_student_profiles_ck_profile_correction"),
        ),
        sa.CheckConstraint(
            "jsonb_typeof(goals) = 'array' AND jsonb_array_length(goals) <= 10",
            name=op.f("ck_student_profiles_ck_profile_goals"),
        ),
        sa.CheckConstraint(
            "jsonb_typeof(interests) = 'array' AND jsonb_array_length(interests) <= 10",
            name=op.f("ck_student_profiles_ck_profile_interests"),
        ),
        sa.CheckConstraint(
            "onboarding_status IN ('in_progress','skipped','completed')",
            name=op.f("ck_student_profiles_ck_profile_status"),
        ),
        sa.CheckConstraint(
            "selected_cefr IN ('A1','A2','B1','B2','C1','C2')",
            name=op.f("ck_student_profiles_ck_profile_cefr"),
        ),
        sa.CheckConstraint(
            "session_duration_minutes BETWEEN 5 AND 120",
            name=op.f("ck_student_profiles_ck_profile_duration"),
        ),
        sa.CheckConstraint(
            "sessions_per_week BETWEEN 1 AND 7",
            name=op.f("ck_student_profiles_ck_profile_frequency"),
        ),
        sa.CheckConstraint("version >= 1", name=op.f("ck_student_profiles_ck_profile_version")),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["students.id"],
            name=op.f("fk_student_profiles_student_id_students"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("student_id", name=op.f("pk_student_profiles")),
    )
    op.create_table(
        "assessment_creations",
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.Uuid(), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("assessment_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(
            ["assessment_id"],
            ["placement_assessments.id"],
            name=op.f("fk_assessment_creations_assessment_id_placement_assessments"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["students.id"],
            name=op.f("fk_assessment_creations_student_id_students"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("student_id", "key", name=op.f("pk_assessment_creations")),
    )
    op.create_index(
        op.f("ix_assessment_creations_assessment_id"),
        "assessment_creations",
        ["assessment_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_assessment_creations_assessment_id"), table_name="assessment_creations")
    op.drop_table("assessment_creations")
    op.drop_table("student_profiles")
    op.drop_index(op.f("ix_placement_assessments_student_id"), table_name="placement_assessments")
    op.drop_table("placement_assessments")
