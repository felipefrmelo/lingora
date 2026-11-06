import hashlib
import json
from uuid import UUID

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from lingora.modules.identity.application import find_student
from lingora.modules.identity.models import Student
from lingora.modules.identity.principal import AuthenticatedPrincipal
from lingora.modules.learning.contracts import (
    AttemptView,
    Catalog,
    ContentView,
    GenerateLesson,
    JobView,
    LearningUnavailable,
    LessonDraft,
    LessonList,
    LessonView,
    QueueFull,
    SubmitAttempt,
    grade,
)
from lingora.modules.learning.models import Content, ExerciseAttempt, Lesson, LessonJob
from lingora.modules.onboarding.contracts import ResourceNotFound, VersionConflict
from lingora.modules.onboarding.models import StudentProfile


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


async def student_for(
    session: AsyncSession, principal: AuthenticatedPrincipal, lock: bool = False
) -> Student:
    student = await find_student(session, principal)
    if student is None:
        raise ResourceNotFound
    if lock or principal.mcp:
        await session.scalar(select(Student).where(Student.id == student.id).with_for_update())
    if principal.mcp:
        # Serialize the access check with a concurrent disconnect and the ensuing write.
        from lingora.modules.conversation.models import McpAccess
        from lingora.modules.identity.principal import AuthorizationDenied

        access = await session.get(McpAccess, student.id)
        if not access or not access.enabled or principal.issued_at is None:
            raise AuthorizationDenied
        if access.revoked_before and principal.issued_at <= int(access.revoked_before.timestamp()):
            raise AuthorizationDenied
    return student


async def owned[T: (Lesson, LessonJob)](
    session: AsyncSession, model: type[T], identifier: UUID, student_id: UUID
) -> T:
    row = await session.scalar(
        select(model).where(model.id == identifier, model.student_id == student_id)
    )
    if row is None:
        raise ResourceNotFound
    return row


def source_view(content: Content) -> ContentView:
    return ContentView.model_validate(content)


async def catalog(
    session: AsyncSession,
    principal: AuthenticatedPrincipal,
    topic: str | None,
    offset: int,
    limit: int,
    available: bool,
) -> Catalog:
    async with session.begin():
        student = await student_for(session, principal)
        profile = await session.get(StudentProfile, student.id)
        filters: list[ColumnElement[bool]] = [Content.available.is_(True)]
        if topic:
            filters.append(Content.topics.contains([topic]))
        total = await session.scalar(select(func.count()).select_from(Content).where(*filters)) or 0
        # Simple transparent ranking, not an adaptive learning plan.
        rows = list(
            await session.scalars(
                select(Content)
                .where(*filters)
                .order_by(Content.published_at.desc(), Content.id)
                .limit(100)
            )
        )
        interests = [x.casefold() for x in profile.interests] if profile else []

        def matches(row: Content) -> list[str]:
            return [x for x in interests if x in " ".join(row.topics).casefold()]

        rows.sort(key=lambda row: -len(matches(row)))
        items = [
            source_view(row).model_copy(
                update={
                    "recommendation_reason": "Matches your interest in " + ", ".join(matches(row))
                    if matches(row)
                    else "Explore a recent English news brief."
                }
            )
            for row in rows[offset : offset + limit]
        ]
        return Catalog(items=items, total=min(total, 100), generation_available=available)


async def job_view(session: AsyncSession, job: LessonJob) -> JobView:
    lesson_id = await session.scalar(select(Lesson.id).where(Lesson.job_id == job.id))
    return JobView.model_validate(
        {
            **{
                name: getattr(job, name)
                for name in (
                    "id",
                    "content_id",
                    "status",
                    "cefr",
                    "level_reason",
                    "error_code",
                    "created_at",
                )
            },
            "lesson_id": lesson_id,
        }
    )


async def enqueue(
    session: AsyncSession,
    principal: AuthenticatedPrincipal,
    payload: GenerateLesson,
    key: UUID,
    configured: bool,
) -> JobView:
    async with session.begin():
        student = await student_for(session, principal, lock=True)
        request_hash = digest(payload.model_dump(mode="json"))
        existing = await session.scalar(
            select(LessonJob).where(LessonJob.student_id == student.id, LessonJob.key == key)
        )
        if existing:
            if existing.request_hash != request_hash:
                raise VersionConflict
            return await job_view(session, existing)
        if not configured:
            raise LearningUnavailable
        content = await session.get(Content, payload.content_id)
        if not content or not content.available:
            raise ResourceNotFound
        active = (
            await session.scalar(
                select(func.count())
                .select_from(LessonJob)
                .where(
                    LessonJob.student_id == student.id, LessonJob.status.in_(["queued", "running"])
                )
            )
            or 0
        )
        if active >= 2:
            raise QueueFull
        profile = await session.get(StudentProfile, student.id)
        level = payload.cefr or (profile.selected_cefr if profile else None) or "A2"
        reason = (
            "You chose this level for this lesson."
            if payload.cefr
            else "Uses your self-selected profile level."
            if profile and profile.selected_cefr
            else "A2 starting point because no level is selected; you can choose another."
        )
        context = {
            "source": source_view(content).model_dump(mode="json"),
            "cefr": level,
            "goals": profile.goals if profile else [],
            "interests": profile.interests if profile else [],
        }
        job = LessonJob(
            student_id=student.id,
            key=key,
            request_hash=request_hash,
            content_id=content.id,
            context=context,
            cefr=level,
            level_reason=reason,
        )
        session.add(job)
        await session.flush()
        return await job_view(session, job)


async def get_job(
    session: AsyncSession, principal: AuthenticatedPrincipal, identifier: UUID
) -> JobView:
    async with session.begin():
        student = await student_for(session, principal)
        return await job_view(session, await owned(session, LessonJob, identifier, student.id))


async def list_jobs(
    session: AsyncSession, principal: AuthenticatedPrincipal, offset: int, limit: int
) -> LessonList:
    async with session.begin():
        student = await student_for(session, principal)
        rows = await session.scalars(
            select(LessonJob)
            .where(LessonJob.student_id == student.id)
            .order_by(LessonJob.created_at.desc(), LessonJob.id)
            .offset(offset)
            .limit(limit)
        )
        items = [await job_view(session, row) for row in rows]
        total = (
            await session.scalar(
                select(func.count())
                .select_from(LessonJob)
                .where(LessonJob.student_id == student.id)
            )
            or 0
        )
        return LessonList(items=items, total=total)


async def get_lesson(
    session: AsyncSession, principal: AuthenticatedPrincipal, identifier: UUID
) -> LessonView:
    async with session.begin():
        student = await student_for(session, principal)
        lesson = await owned(session, Lesson, identifier, student.id)
        job = await session.get(LessonJob, lesson.job_id)
        if job is None:
            raise ResourceNotFound
        document = LessonDraft.model_validate(lesson.document).model_dump()
        for exercise in document["exercises"]:
            for field in ("correct_answers", "explanation", "evidence"):
                exercise.pop(field)
        count = (
            await session.scalar(
                select(func.count())
                .select_from(ExerciseAttempt)
                .where(ExerciseAttempt.lesson_id == lesson.id)
            )
            or 0
        )
        return LessonView.model_validate(
            {
                **document,
                "id": lesson.id,
                "created_at": lesson.created_at,
                "cefr": job.cefr,
                "level_reason": job.level_reason,
                "source": lesson.source_snapshot,
                "prompt_version": lesson.prompt_version,
                "schema_version": lesson.schema_version,
                "attempt_count": count,
            }
        )


async def submit_attempt(
    session: AsyncSession,
    principal: AuthenticatedPrincipal,
    identifier: UUID,
    payload: SubmitAttempt,
    key: UUID,
) -> AttemptView:
    async with session.begin():
        student = await student_for(session, principal, lock=True)
        lesson = await owned(session, Lesson, identifier, student.id)
        request_hash = digest({"lesson_id": str(identifier), **payload.model_dump()})
        previous = await session.scalar(
            select(ExerciseAttempt).where(
                ExerciseAttempt.student_id == student.id, ExerciseAttempt.key == key
            )
        )
        if previous:
            if previous.request_hash != request_hash:
                raise VersionConflict
            return AttemptView.model_validate(previous)
        draft = LessonDraft.model_validate(lesson.document)
        results = grade(draft, payload)
        attempt = ExerciseAttempt(
            student_id=student.id,
            lesson_id=lesson.id,
            key=key,
            request_hash=request_hash,
            answers=payload.answers,
            results=[x.model_dump() for x in results],
            correct=sum(x.correct for x in results),
            total=len(results),
        )
        session.add(attempt)
        await session.flush()
        return AttemptView.model_validate(attempt)


async def list_attempts(
    session: AsyncSession,
    principal: AuthenticatedPrincipal,
    identifier: UUID,
    offset: int,
    limit: int,
) -> list[AttemptView]:
    async with session.begin():
        student = await student_for(session, principal)
        await owned(session, Lesson, identifier, student.id)
        rows = await session.scalars(
            select(ExerciseAttempt)
            .where(
                ExerciseAttempt.lesson_id == identifier, ExerciseAttempt.student_id == student.id
            )
            .order_by(ExerciseAttempt.created_at.desc(), ExerciseAttempt.id)
            .offset(offset)
            .limit(limit)
        )
        return [AttemptView.model_validate(row) for row in rows]
