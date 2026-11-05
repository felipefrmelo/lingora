"""content lessons and durable generation

Revision ID: 0003
Revises: 0002
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "contents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=120), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("topics", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("license_name", sa.String(length=32), nullable=False),
        sa.Column("license_url", sa.String(length=300), nullable=False),
        sa.Column("attribution", sa.String(length=300), nullable=False),
        sa.Column("available", sa.Boolean(), nullable=False),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("license_name = 'OGL-3.0'", name=op.f("ck_contents_content_license")),
        sa.CheckConstraint(
            "length(summary) BETWEEN 40 AND 8000", name=op.f("ck_contents_content_summary")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_contents")),
        sa.UniqueConstraint("fingerprint", name=op.f("uq_contents_fingerprint")),
        sa.UniqueConstraint("url", name=op.f("uq_contents_url")),
    )
    op.create_table(
        "lesson_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.Uuid(), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("content_id", sa.Uuid(), nullable=False),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("cefr", sa.String(length=2), nullable=False),
        sa.Column("level_reason", sa.String(length=300), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("lease_token", sa.Uuid(), nullable=True),
        sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "available_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("error_code", sa.String(length=32), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(status = 'running') = (lease_token IS NOT NULL)",
            name=op.f("ck_lesson_jobs_job_lease"),
        ),
        sa.CheckConstraint(
            "cefr IN ('A1','A2','B1','B2','C1','C2')", name=op.f("ck_lesson_jobs_job_cefr")
        ),
        sa.CheckConstraint(
            "status IN ('queued','running','succeeded','failed')",
            name=op.f("ck_lesson_jobs_job_status"),
        ),
        sa.CheckConstraint("attempts BETWEEN 0 AND 3", name=op.f("ck_lesson_jobs_job_attempts")),
        sa.ForeignKeyConstraint(
            ["content_id"], ["contents.id"], name=op.f("fk_lesson_jobs_content_id_contents")
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["students.id"],
            name=op.f("fk_lesson_jobs_student_id_students"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lesson_jobs")),
        sa.UniqueConstraint("student_id", "key", name=op.f("uq_lesson_jobs_student_id")),
    )
    op.create_index(op.f("ix_lesson_jobs_status"), "lesson_jobs", ["status"], unique=False)
    op.create_index(op.f("ix_lesson_jobs_student_id"), "lesson_jobs", ["student_id"], unique=False)
    op.create_table(
        "generation_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("estimated_cost_microusd", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["lesson_jobs.id"],
            name=op.f("fk_generation_events_job_id_lesson_jobs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_generation_events")),
    )
    op.create_index(
        op.f("ix_generation_events_job_id"), "generation_events", ["job_id"], unique=False
    )
    op.create_table(
        "lessons",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("document", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("prompt_version", sa.String(length=32), nullable=False),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["lesson_jobs.id"],
            name=op.f("fk_lessons_job_id_lesson_jobs"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["students.id"],
            name=op.f("fk_lessons_student_id_students"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lessons")),
        sa.UniqueConstraint("job_id", name=op.f("uq_lessons_job_id")),
    )
    op.create_index(op.f("ix_lessons_student_id"), "lessons", ["student_id"], unique=False)
    op.create_table(
        "exercise_attempts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("lesson_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.Uuid(), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("answers", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("results", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("correct", sa.Integer(), nullable=False),
        sa.Column("total", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "total = 5 AND correct BETWEEN 0 AND total",
            name=op.f("ck_exercise_attempts_attempt_grade"),
        ),
        sa.ForeignKeyConstraint(
            ["lesson_id"],
            ["lessons.id"],
            name=op.f("fk_exercise_attempts_lesson_id_lessons"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["students.id"],
            name=op.f("fk_exercise_attempts_student_id_students"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_exercise_attempts")),
        sa.UniqueConstraint("student_id", "key", name=op.f("uq_exercise_attempts_student_id")),
    )
    op.create_index(
        op.f("ix_exercise_attempts_lesson_id"), "exercise_attempts", ["lesson_id"], unique=False
    )
    op.create_index(
        op.f("ix_exercise_attempts_student_id"), "exercise_attempts", ["student_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_exercise_attempts_student_id"), table_name="exercise_attempts")
    op.drop_index(op.f("ix_exercise_attempts_lesson_id"), table_name="exercise_attempts")
    op.drop_table("exercise_attempts")
    op.drop_index(op.f("ix_lessons_student_id"), table_name="lessons")
    op.drop_table("lessons")
    op.drop_index(op.f("ix_generation_events_job_id"), table_name="generation_events")
    op.drop_table("generation_events")
    op.drop_index(op.f("ix_lesson_jobs_student_id"), table_name="lesson_jobs")
    op.drop_index(op.f("ix_lesson_jobs_status"), table_name="lesson_jobs")
    op.drop_table("lesson_jobs")
    op.drop_table("contents")
