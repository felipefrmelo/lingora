from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from lingora.infrastructure.database import get_session
from lingora.integrations.auth0.verifier import Auth0TokenVerifier
from lingora.modules.identity.application import ensure_current_student, get_current_student
from lingora.modules.identity.principal import (
    AuthenticatedPrincipal,
    AuthenticationUnavailable,
    AuthorizationDenied,
    InvalidCredentials,
)

router = APIRouter(prefix="/api/v1/me", tags=["identity"])
bearer = HTTPBearer(auto_error=False, scheme_name="Auth0AccessToken")


class StudentAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime


class BootstrapRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


async def verified_principal(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(bearer)],
) -> AuthenticatedPrincipal:
    if credentials is None:
        raise HTTPException(
            401, "A bearer access token is required.", headers={"WWW-Authenticate": "Bearer"}
        )
    verifier = cast(Auth0TokenVerifier, request.app.state.token_verifier)
    try:
        return await verifier.verify(credentials.credentials)
    except InvalidCredentials:
        raise HTTPException(
            401,
            "Invalid access token.",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        ) from None
    except AuthorizationDenied:
        raise HTTPException(403, "A verified email is required.") from None
    except AuthenticationUnavailable:
        raise HTTPException(503, "Sign-in is temporarily unavailable.") from None


def require_scope(
    scope: str,
) -> Callable[[AuthenticatedPrincipal], Awaitable[AuthenticatedPrincipal]]:
    async def authorized(
        principal: Annotated[AuthenticatedPrincipal, Depends(verified_principal)],
    ) -> AuthenticatedPrincipal:
        if scope not in principal.scopes:
            raise HTTPException(
                403,
                "The access token lacks the required permission.",
                headers={"WWW-Authenticate": f'Bearer error="insufficient_scope", scope="{scope}"'},
            )
        return principal

    return authorized


async def reject_identity_parameters(request: Request) -> None:
    # These are self-account operations, never arbitrary student selectors.
    if request.query_params or (request.method == "GET" and await request.body()):
        raise HTTPException(422, "This endpoint accepts no identity parameters.")


ReadPrincipal = Annotated[AuthenticatedPrincipal, Depends(require_scope("profile:read"))]
WritePrincipal = Annotated[AuthenticatedPrincipal, Depends(require_scope("profile:write"))]
Session = Annotated[AsyncSession, Depends(get_session)]


@router.get(
    "",
    operation_id="getCurrentStudent",
    response_model=StudentAccountResponse,
    dependencies=[Depends(reject_identity_parameters)],
)
async def current_student(principal: ReadPrincipal, session: Session) -> StudentAccountResponse:
    student = await get_current_student(session, principal)
    if student is None:
        raise HTTPException(404, "The student account has not been initialized.")
    return StudentAccountResponse.model_validate(student)


@router.post(
    "/bootstrap",
    operation_id="bootstrapCurrentStudent",
    response_model=StudentAccountResponse,
    dependencies=[Depends(reject_identity_parameters)],
)
async def bootstrap_student(
    principal: WritePrincipal, session: Session, payload: BootstrapRequest | None = None
) -> StudentAccountResponse:
    student = await ensure_current_student(session, principal)
    return StudentAccountResponse.model_validate(student)
