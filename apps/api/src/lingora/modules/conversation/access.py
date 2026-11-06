from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from lingora.modules.conversation.models import McpAccess
from lingora.modules.identity.principal import AuthenticatedPrincipal, AuthorizationDenied
from lingora.modules.learning.application import student_for


async def status(db: AsyncSession, principal: AuthenticatedPrincipal) -> bool:
    async with db.begin():
        student = await student_for(db, principal)
        row = await db.get(McpAccess, student.id)
        return bool(row and row.enabled)


async def set_enabled(db: AsyncSession, principal: AuthenticatedPrincipal, enabled: bool) -> bool:
    async with db.begin():
        student = await student_for(db, principal, lock=True)
        row = await db.get(McpAccess, student.id)
        if row is None:
            row = McpAccess(student_id=student.id, enabled=False)
            db.add(row)
        if not enabled:
            row.revoked_before = datetime.now(UTC)
        row.enabled = enabled
        return enabled


async def authorize(db: AsyncSession, principal: AuthenticatedPrincipal) -> None:
    async with db.begin():
        student = await student_for(db, principal, lock=True)
        row = await db.get(McpAccess, student.id)
        if not row or not row.enabled or principal.issued_at is None:
            raise AuthorizationDenied
        if row.revoked_before and principal.issued_at <= int(row.revoked_before.timestamp()):
            raise AuthorizationDenied
