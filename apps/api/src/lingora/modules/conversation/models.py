from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from lingora.infrastructure.database import Base
from lingora.modules.identity.models import Student
from lingora.modules.learning.models import Lesson


class ConversationSession(Base):
    __tablename__ = "conversation_sessions"
    __table_args__ = (
        CheckConstraint("status IN ('READY','IN_PROGRESS','COMPLETED','ABANDONED')", name="status"),
        CheckConstraint("cefr IN ('A1','A2','B1','B2','C1','C2')", name="cefr"),
        CheckConstraint("correction_mode IN ('free','balanced','intensive')", name="correction"),
        CheckConstraint("version >= 1", name="version"),
        CheckConstraint("(status = 'COMPLETED') = (completed_at IS NOT NULL)", name="completion"),
        Index(
            "uq_conversation_sessions_active_student",
            "student_id",
            unique=True,
            postgresql_where=text("status IN ('READY', 'IN_PROGRESS')"),
        ),
    )
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    student_id: Mapped[UUID] = mapped_column(ForeignKey(Student.id, ondelete="CASCADE"), index=True)
    lesson_id: Mapped[UUID] = mapped_column(ForeignKey(Lesson.id, ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(16), default="READY")
    cefr: Mapped[str] = mapped_column(String(2))
    correction_mode: Mapped[str] = mapped_column(String(16))
    save_examples: Mapped[bool] = mapped_column(default=True)
    version: Mapped[int] = mapped_column(default=1)
    feedback: Mapped[dict[str, Any] | None] = mapped_column(JSONB(none_as_null=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ConversationReceipt(Base):
    __tablename__ = "conversation_receipts"
    __table_args__ = (UniqueConstraint("student_id", "key"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    student_id: Mapped[UUID] = mapped_column(ForeignKey(Student.id, ondelete="CASCADE"), index=True)
    session_id: Mapped[UUID] = mapped_column(ForeignKey(ConversationSession.id, ondelete="CASCADE"))
    key: Mapped[UUID] = mapped_column()
    operation: Mapped[str] = mapped_column(String(32))
    request_hash: Mapped[str] = mapped_column(String(64))
    result: Mapped[dict[str, Any]] = mapped_column(JSONB)


class ConversationEvent(Base):
    __tablename__ = "conversation_events"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        ForeignKey(ConversationSession.id, ondelete="CASCADE"), index=True
    )
    event: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class McpAccess(Base):
    __tablename__ = "mcp_access"
    student_id: Mapped[UUID] = mapped_column(
        ForeignKey(Student.id, ondelete="CASCADE"), primary_key=True
    )
    enabled: Mapped[bool] = mapped_column(default=False)
    revoked_before: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
