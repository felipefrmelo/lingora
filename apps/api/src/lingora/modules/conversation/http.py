from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from lingora.modules.conversation import application
from lingora.modules.conversation.contracts import PrepareSession, SessionVersion, SessionView
from lingora.modules.identity.http import ReadPrincipal, Session, WritePrincipal
from lingora.modules.onboarding.http import resource_errors


async def reject_parameters(request: Request) -> None:
    if request.query_params or (request.method == "GET" and await request.body()):
        raise HTTPException(422, "Unexpected request parameters.")


router = APIRouter(
    prefix="/api/v1/me/conversation-sessions",
    tags=["conversation"],
    dependencies=[Depends(resource_errors), Depends(reject_parameters)],
)
Key = Annotated[UUID, Header(alias="Idempotency-Key")]


@router.post("", response_model=SessionView, operation_id="prepareConversationSession")
async def prepare(
    principal: WritePrincipal, session: Session, payload: PrepareSession, key: Key
) -> SessionView:
    return await application.prepare(session, principal, payload, key)


@router.get("", response_model=list[SessionView], operation_id="listConversationSessions")
async def list_sessions(principal: ReadPrincipal, session: Session) -> list[SessionView]:
    return await application.list_sessions(session, principal)


@router.get("/{identifier}", response_model=SessionView, operation_id="getConversationSession")
async def get_session(principal: ReadPrincipal, session: Session, identifier: UUID) -> SessionView:
    return await application.get(session, principal, identifier)


@router.post(
    "/{identifier}/abandon", response_model=SessionView, operation_id="abandonConversationSession"
)
async def abandon(
    principal: WritePrincipal, session: Session, identifier: UUID, payload: SessionVersion, key: Key
) -> SessionView:
    return await application.change(
        session, principal, identifier, payload.expected_version, "abandon", key
    )
