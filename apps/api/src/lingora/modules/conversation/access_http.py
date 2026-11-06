from fastapi import APIRouter, Depends

from lingora.modules.conversation import access
from lingora.modules.conversation.contracts import McpAccessView
from lingora.modules.identity.http import ReadPrincipal, Session, WritePrincipal
from lingora.modules.onboarding.http import reject_unknown_parameters, resource_errors

router = APIRouter(
    prefix="/api/v1/me/mcp-access",
    tags=["conversation"],
    dependencies=[Depends(resource_errors), Depends(reject_unknown_parameters)],
)


@router.get("", response_model=McpAccessView, operation_id="getMcpAccess")
async def get_access(principal: ReadPrincipal, db: Session) -> McpAccessView:
    return McpAccessView(enabled=await access.status(db, principal))


@router.put("", response_model=McpAccessView, operation_id="setMcpAccess")
async def put_access(
    principal: WritePrincipal, db: Session, payload: McpAccessView
) -> McpAccessView:
    return McpAccessView(enabled=await access.set_enabled(db, principal, payload.enabled))
