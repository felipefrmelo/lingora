from collections.abc import AsyncIterator
from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request

from lingora.core.config import Settings
from lingora.modules.identity.http import ReadPrincipal, Session, WritePrincipal
from lingora.modules.learning import application
from lingora.modules.learning.contracts import (
    AttemptView,
    Catalog,
    GenerateLesson,
    JobView,
    LearningUnavailable,
    LessonList,
    LessonView,
    QueueFull,
    SubmitAttempt,
)
from lingora.modules.onboarding.http import resource_errors


async def learning_errors() -> AsyncIterator[None]:
    try:
        yield
    except LearningUnavailable:
        raise HTTPException(503, "Lesson generation is unavailable. Try again later.") from None
    except QueueFull:
        raise HTTPException(
            429,
            "Two lessons are already being prepared. Wait for them to finish.",
            headers={"Retry-After": "30"},
        ) from None


async def parameters(request: Request) -> None:
    allowed = (
        {"offset", "limit"}
        if request.method == "GET"
        and (request.url.path.endswith("/attempts") or request.url.path.endswith("/lessons"))
        else {"offset", "limit", "topic"}
        if request.url.path.endswith("/content")
        else set[str]()
    )
    if set(request.query_params) - allowed or (request.method == "GET" and await request.body()):
        raise HTTPException(422, "Unexpected request parameters.")


router = APIRouter(
    prefix="/api/v1/me",
    tags=["learning"],
    dependencies=[Depends(resource_errors), Depends(learning_errors), Depends(parameters)],
)
Limit = Annotated[int, Query(ge=1, le=50)]
Offset = Annotated[int, Query(ge=0)]
Key = Annotated[UUID, Header(alias="Idempotency-Key")]


def configured(request: Request) -> bool:
    return bool(cast(Settings, request.app.state.settings).openai_api_key.get_secret_value())


@router.get("/content", response_model=Catalog, operation_id="listLearningContent")
async def content(
    principal: ReadPrincipal,
    session: Session,
    request: Request,
    topic: Annotated[str | None, Query(pattern="^(space|environment|science)$")] = None,
    offset: Offset = 0,
    limit: Limit = 20,
) -> Catalog:
    return await application.catalog(session, principal, topic, offset, limit, configured(request))


@router.post("/lessons", response_model=JobView, status_code=202, operation_id="prepareLesson")
async def prepare(
    principal: WritePrincipal, session: Session, payload: GenerateLesson, key: Key, request: Request
) -> JobView:
    return await application.enqueue(session, principal, payload, key, configured(request))


@router.get("/lessons", response_model=LessonList, operation_id="listLessons")
async def lessons(
    principal: ReadPrincipal, session: Session, offset: Offset = 0, limit: Limit = 20
) -> LessonList:
    return await application.list_jobs(session, principal, offset, limit)


@router.get("/lesson-jobs/{job_id}", response_model=JobView, operation_id="getLessonJob")
async def job(principal: ReadPrincipal, session: Session, job_id: UUID) -> JobView:
    return await application.get_job(session, principal, job_id)


@router.get("/lessons/{lesson_id}", response_model=LessonView, operation_id="getLesson")
async def lesson(principal: ReadPrincipal, session: Session, lesson_id: UUID) -> LessonView:
    return await application.get_lesson(session, principal, lesson_id)


@router.post(
    "/lessons/{lesson_id}/attempts",
    response_model=AttemptView,
    operation_id="submitExerciseAttempt",
)
async def attempt(
    principal: WritePrincipal, session: Session, lesson_id: UUID, payload: SubmitAttempt, key: Key
) -> AttemptView:
    return await application.submit_attempt(session, principal, lesson_id, payload, key)


@router.get(
    "/lessons/{lesson_id}/attempts",
    response_model=list[AttemptView],
    operation_id="listExerciseAttempts",
)
async def attempts(
    principal: ReadPrincipal,
    session: Session,
    lesson_id: UUID,
    offset: Offset = 0,
    limit: Limit = 20,
) -> list[AttemptView]:
    return await application.list_attempts(session, principal, lesson_id, offset, limit)
