"""Durable PostgreSQL worker; leases fence late results after process recovery."""

import asyncio
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from lingora.modules.learning.contracts import (
    PROMPT_VERSION,
    SCHEMA_VERSION,
    LessonDraft,
    assemble_lesson,
)
from lingora.modules.learning.models import Content, GenerationEvent, Lesson, LessonJob
from lingora.modules.learning.provider import GenerationFailure, LessonProvider


@dataclass(frozen=True)
class Claim:
    id: UUID
    token: UUID
    context: dict[str, Any]


async def claim(sessions: async_sessionmaker[AsyncSession]) -> Claim | None:
    now = datetime.now(UTC)
    async with sessions() as session, session.begin():
        job = await session.scalar(
            select(LessonJob)
            .where(
                or_(
                    and_(LessonJob.status == "queued", LessonJob.available_at <= now),
                    and_(LessonJob.status == "running", LessonJob.lease_until <= now),
                )
            )
            .order_by(LessonJob.available_at, LessonJob.id)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if job is None:
            return None
        if job.attempts >= 3:
            job.status, job.error_code, job.lease_token, job.lease_until = (
                "failed",
                "retry_exhausted",
                None,
                None,
            )
            return None
        job.status = "running"
        job.attempts += 1
        token = uuid4()
        job.lease_token = token
        job.lease_until = now + timedelta(minutes=4)
        return Claim(job.id, token, job.context)


def cost_estimate(model: str, input_tokens: int | None, output_tokens: int | None) -> int | None:
    # USD per million == micro-USD per token. Pricing baseline verified 2026-11-05.
    if (
        model not in {"gpt-5-mini", "gpt-5-mini-2025-08-07"}
        or input_tokens is None
        or output_tokens is None
    ):
        return None
    return round(input_tokens * 0.25 + output_tokens * 2)


async def run_once(
    sessions: async_sessionmaker[AsyncSession], provider: LessonProvider, model: str
) -> bool:
    work = await claim(sessions)
    if work is None:
        return False
    started = time.monotonic()
    document: LessonDraft | None = None
    error: GenerationFailure | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    actual_model = model
    try:
        # The provider's deadline is shorter than the lease. Never hold a DB transaction here.
        async with asyncio.timeout(190):
            generated = await provider.generate(work.context)
        document = LessonDraft.model_validate(generated.document.model_dump())
        document = assemble_lesson(document, work.context)
        actual_model, input_tokens, output_tokens = (
            generated.model,
            generated.input_tokens,
            generated.output_tokens,
        )
    except GenerationFailure as failure:
        error = failure
        input_tokens, output_tokens = failure.input_tokens, failure.output_tokens
    except TimeoutError:
        error = GenerationFailure("provider_timeout", retryable=True)
    except Exception:
        # Never retain provider exceptions, source snippets, or prompts in telemetry.
        error = GenerationFailure("generation_failed")
    latency_ms = round((time.monotonic() - started) * 1000)
    async with sessions() as session, session.begin():
        job = await session.scalar(
            select(LessonJob).where(LessonJob.id == work.id).with_for_update()
        )
        if job is None:
            return True
        event = GenerationEvent(
            job_id=job.id,
            model=actual_model,
            outcome="lease_superseded",
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_microusd=cost_estimate(actual_model, input_tokens, output_tokens),
        )
        session.add(event)
        if job.status != "running" or job.lease_token != work.token:
            return True  # Retain usage but never publish a superseded result.
        content = await session.get(Content, job.content_id)
        if content and error and error.code == "source_unavailable":
            content.available = False
        if not content or not content.available:
            error = GenerationFailure("source_unavailable")
        if document is not None and error is None:
            session.add(
                Lesson(
                    job_id=job.id,
                    student_id=job.student_id,
                    document=document.model_dump(mode="json"),
                    source_snapshot=job.context["source"],
                    prompt_version=PROMPT_VERSION,
                    schema_version=SCHEMA_VERSION,
                )
            )
            job.status, job.error_code = "succeeded", None
        else:
            error = error or GenerationFailure("generation_failed")
            job.status = "queued" if error.retryable and job.attempts < 3 else "failed"
            job.error_code = error.code
            job.available_at = datetime.now(UTC) + timedelta(seconds=30 * 2 ** (job.attempts - 1))
        job.lease_token, job.lease_until = None, None
        event.outcome = error.code if error else "validated"
    return True
