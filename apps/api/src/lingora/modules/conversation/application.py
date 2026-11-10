"""Conversation operations shared by HTTP and MCP adapters."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lingora.modules.conversation import summary_only
from lingora.modules.conversation.contracts import (
    CompleteSession,
    PrepareSession,
    SessionPreferences,
    SessionView,
)
from lingora.modules.conversation.models import (
    ConversationEvent,
    ConversationReceipt,
    ConversationSession,
)
from lingora.modules.identity.principal import AuthenticatedPrincipal
from lingora.modules.learning.application import digest, owned, student_for
from lingora.modules.learning.models import Lesson, LessonJob
from lingora.modules.onboarding.contracts import ResourceNotFound, VersionConflict
from lingora.modules.onboarding.models import StudentProfile


class SummaryOnlyPolicyError(Exception):
    pass


def valid_summary_only_feedback(completion: CompleteSession) -> bool:
    return (
        completion.summary in summary_only.SUMMARIES
        and all(value in summary_only.STRENGTHS for value in completion.strengths)
        and all(value in summary_only.PRIORITIES for value in completion.priorities)
        and not completion.observations
    )


async def session_owned(
    db: AsyncSession, student_id: UUID, identifier: UUID
) -> ConversationSession:
    row = await db.scalar(
        select(ConversationSession)
        .where(ConversationSession.student_id == student_id, ConversationSession.id == identifier)
        .with_for_update()
    )
    if row is None:
        raise ResourceNotFound
    return row


async def receipt(
    db: AsyncSession, student_id: UUID, key: UUID, operation: str, request_hash: str
) -> SessionView | None:
    previous = await db.scalar(
        select(ConversationReceipt).where(
            ConversationReceipt.student_id == student_id, ConversationReceipt.key == key
        )
    )
    if previous:
        if previous.operation != operation or previous.request_hash != request_hash:
            raise VersionConflict
        return SessionView.model_validate(previous.result)
    return None


def record(
    db: AsyncSession,
    student_id: UUID,
    row: ConversationSession,
    key: UUID,
    operation: str,
    request_hash: str,
    result: SessionView,
) -> None:
    db.add(
        ConversationReceipt(
            student_id=student_id,
            session_id=row.id,
            key=key,
            operation=operation,
            request_hash=request_hash,
            result=result.model_dump(mode="json"),
        )
    )


async def prepare(
    db: AsyncSession, principal: AuthenticatedPrincipal, payload: PrepareSession, key: UUID
) -> SessionView:
    async with db.begin():
        student = await student_for(db, principal, lock=True)
        request_hash = digest(payload.model_dump(mode="json"))
        previous = await receipt(db, student.id, key, "prepare", request_hash)
        if previous:
            return previous
        lesson = await owned(db, Lesson, payload.lesson_id, student.id)
        active = await db.scalar(
            select(ConversationSession).where(
                ConversationSession.student_id == student.id,
                ConversationSession.status.in_(["READY", "IN_PROGRESS"]),
            )
        )
        if active:
            if active.lesson_id != lesson.id or active.save_examples != payload.save_examples:
                raise VersionConflict
            result = SessionView.model_validate(active)
            record(db, student.id, active, key, "prepare", request_hash, result)
            return result
        job = await db.get(LessonJob, lesson.job_id)
        if job is None:
            raise ResourceNotFound
        profile = await db.get(StudentProfile, student.id)
        row = ConversationSession(
            student_id=student.id,
            lesson_id=lesson.id,
            status="READY",
            cefr=job.cefr,
            correction_mode=profile.correction_mode if profile else "balanced",
            save_examples=payload.save_examples,
            version=1,
        )
        db.add(row)
        await db.flush()
        result = SessionView.model_validate(row)
        record(db, student.id, row, key, "prepare", request_hash, result)
        db.add(ConversationEvent(session_id=row.id, event="prepared"))
        return result


async def get(db: AsyncSession, principal: AuthenticatedPrincipal, identifier: UUID) -> SessionView:
    async with db.begin():
        student = await student_for(db, principal)
        return SessionView.model_validate(await session_owned(db, student.id, identifier))


async def list_sessions(db: AsyncSession, principal: AuthenticatedPrincipal) -> list[SessionView]:
    async with db.begin():
        student = await student_for(db, principal)
        rows = await db.scalars(
            select(ConversationSession)
            .where(ConversationSession.student_id == student.id)
            .order_by(ConversationSession.created_at.desc(), ConversationSession.id)
            .limit(100)
        )
        return [SessionView.model_validate(row) for row in rows]


async def change(
    db: AsyncSession,
    principal: AuthenticatedPrincipal,
    identifier: UUID,
    expected_version: int,
    action: str,
    key: UUID,
    preferences: SessionPreferences | None = None,
    completion: CompleteSession | None = None,
) -> SessionView:
    if (preferences and preferences.expected_version != expected_version) or (
        completion and completion.expected_version != expected_version
    ):
        raise VersionConflict
    async with db.begin():
        student = await student_for(db, principal, lock=True)
        body = {
            "session_id": str(identifier),
            "expected_version": expected_version,
            "preferences": preferences.model_dump(mode="json") if preferences else None,
            "completion": completion.model_dump(mode="json") if completion else None,
        }
        request_hash = digest(body)
        previous = await receipt(db, student.id, key, action, request_hash)
        if previous:
            return previous
        row = await session_owned(db, student.id, identifier)
        if row.version != expected_version or row.status not in ("READY", "IN_PROGRESS"):
            raise VersionConflict
        if action == "start":
            row.status = "IN_PROGRESS"
        elif action == "abandon":
            row.status = "ABANDONED"
        elif action == "preferences" and preferences:
            row.correction_mode = preferences.correction_mode
        elif action == "complete" and completion:
            if not row.save_examples and not valid_summary_only_feedback(completion):
                raise SummaryOnlyPolicyError
            row.feedback = completion.model_dump(mode="json", exclude={"expected_version"})
            row.status = "COMPLETED"
            row.completed_at = datetime.now(UTC)
        else:
            raise ValueError("Unknown conversation operation")
        row.version += 1
        await db.flush()
        result = SessionView.model_validate(row)
        record(db, student.id, row, key, action, request_hash, result)
        db.add(ConversationEvent(session_id=row.id, event=action))
        return result
