from typing import Literal, cast

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from lingora.core.errors import ProblemDetails, problem_response
from lingora.infrastructure.database import Database

router = APIRouter(prefix="/api/v1", tags=["system"])


class HealthResponse(BaseModel):
    status: Literal["ok"]


class ReadyResponse(BaseModel):
    status: Literal["ready"]


@router.get("/health", operation_id="getHealth", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get(
    "/ready",
    operation_id="getReadiness",
    response_model=ReadyResponse,
    responses={503: {"model": ProblemDetails, "description": "Database unavailable"}},
)
async def ready(request: Request) -> ReadyResponse | Response:
    database = cast(Database, request.app.state.database)
    try:
        await database.check()
    except (SQLAlchemyError, TimeoutError, OSError):
        return problem_response(
            request,
            status=503,
            title="Service unavailable",
            detail="The service is not ready. Please try again shortly.",
        )
    return ReadyResponse(status="ready")
