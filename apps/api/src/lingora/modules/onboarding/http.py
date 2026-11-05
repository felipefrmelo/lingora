from collections.abc import AsyncIterator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from sqlalchemy.exc import SQLAlchemyError

from lingora.modules.identity.http import ReadPrincipal, Session, WritePrincipal
from lingora.modules.onboarding import application
from lingora.modules.onboarding.contracts import (
    AssessmentFields,
    AssessmentList,
    AssessmentResponse,
    AssessmentWrite,
    CreationGone,
    ProfileResponse,
    ProfileWrite,
    ResourceNotFound,
    VersionConflict,
)


async def resource_errors() -> AsyncIterator[None]:
    try:
        yield
    except ResourceNotFound:
        raise HTTPException(404, "The requested student resource was not found.") from None
    except VersionConflict:
        raise HTTPException(
            409, "This record changed or the creation key was reused. Reload before saving."
        ) from None
    except CreationGone:
        raise HTTPException(
            410, "This assessment was deleted. Start a new entry to create another."
        ) from None
    except SQLAlchemyError:
        # Do not expose/log SQL parameters or PostgreSQL row-detail diagnostics.
        raise HTTPException(
            503, "Learning records are temporarily unavailable. Try again shortly."
        ) from None


async def reject_unknown_parameters(request: Request) -> None:
    allowed = (
        {"limit", "offset"}
        if request.method == "GET" and request.url.path.endswith("/assessments")
        else set[str]()
    )
    if request.method == "DELETE":
        allowed = {"expected_version"}
    if set(request.query_params) - allowed or (
        request.method in {"GET", "DELETE"} and await request.body()
    ):
        raise HTTPException(422, "Unexpected request parameters.")


router = APIRouter(
    prefix="/api/v1/me",
    tags=["onboarding"],
    dependencies=[Depends(resource_errors), Depends(reject_unknown_parameters)],
)


@router.get("/profile", operation_id="getLearningProfile", response_model=ProfileResponse)
async def get_profile(principal: ReadPrincipal, session: Session) -> ProfileResponse:
    return await application.read_profile(session, principal)


@router.put("/profile", operation_id="saveLearningProfile", response_model=ProfileResponse)
async def put_profile(
    principal: WritePrincipal, session: Session, payload: ProfileWrite
) -> ProfileResponse:
    return await application.write_profile(session, principal, payload)


@router.get("/assessments", operation_id="listAssessments", response_model=AssessmentList)
async def get_assessments(
    principal: ReadPrincipal,
    session: Session,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AssessmentList:
    return await application.list_assessments(session, principal, limit, offset)


@router.post(
    "/assessments",
    operation_id="createAssessment",
    response_model=AssessmentResponse,
    status_code=201,
    responses={200: {"model": AssessmentResponse, "description": "Replayed creation"}},
)
async def post_assessment(
    principal: WritePrincipal,
    session: Session,
    payload: AssessmentFields,
    response: Response,
    key: Annotated[UUID, Header(alias="Idempotency-Key")],
) -> AssessmentResponse:
    result, created = await application.create_assessment(session, principal, payload, key)
    response.status_code = 201 if created else 200
    return result


@router.put(
    "/assessments/{assessment_id}",
    operation_id="updateAssessment",
    response_model=AssessmentResponse,
)
async def put_assessment(
    principal: WritePrincipal, session: Session, assessment_id: UUID, payload: AssessmentWrite
) -> AssessmentResponse:
    return await application.update_assessment(session, principal, assessment_id, payload)


@router.delete("/assessments/{assessment_id}", operation_id="deleteAssessment", status_code=204)
async def remove_assessment(
    principal: WritePrincipal,
    session: Session,
    assessment_id: UUID,
    expected_version: Annotated[int, Query(ge=1)],
) -> Response:
    await application.delete_assessment(session, principal, assessment_id, expected_version)
    return Response(status_code=204)
