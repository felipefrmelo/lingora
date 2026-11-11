"""Store the learner's MCP access setting.

Revision ID: 0005
Revises: e7f759551d7f
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "e7f759551d7f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "mcp_access",
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("revoked_before", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["students.id"],
            name=op.f("fk_mcp_access_student_id_students"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("student_id", name=op.f("pk_mcp_access")),
    )


def downgrade() -> None:
    op.drop_table("mcp_access")
