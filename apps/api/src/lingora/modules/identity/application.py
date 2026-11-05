from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from lingora.modules.identity.models import ExternalIdentity, Student
from lingora.modules.identity.principal import AuthenticatedPrincipal


@dataclass(frozen=True, slots=True)
class StudentAccount:
    id: UUID
    created_at: datetime


def account(student: Student) -> StudentAccount:
    return StudentAccount(id=student.id, created_at=student.created_at)


async def find_student(session: AsyncSession, principal: AuthenticatedPrincipal) -> Student | None:
    statement = (
        select(Student)
        .join(ExternalIdentity, ExternalIdentity.student_id == Student.id)
        .where(
            ExternalIdentity.provider == "auth0",
            ExternalIdentity.issuer == principal.issuer,
            ExternalIdentity.subject == principal.subject,
        )
    )
    return await session.scalar(statement)


async def get_current_student(
    session: AsyncSession, principal: AuthenticatedPrincipal
) -> StudentAccount | None:
    async with session.begin():
        student = await find_student(session, principal)
        return account(student) if student is not None else None


async def ensure_current_student(
    session: AsyncSession, principal: AuthenticatedPrincipal
) -> StudentAccount:
    try:
        async with session.begin():
            student = await find_student(session, principal)
            if student is None:
                student = Student()
                session.add(student)
                await session.flush()
                session.add(
                    ExternalIdentity(
                        student_id=student.id,
                        provider="auth0",
                        issuer=principal.issuer,
                        subject=principal.subject,
                    )
                )
                await session.flush()
            result = account(student)
        return result
    except IntegrityError:
        # A concurrent first login may win the unique external-identity tuple.
        # The whole losing transaction (including its new student) was rolled back.
        async with session.begin():
            winner = await find_student(session, principal)
            if winner is None:
                raise
            return account(winner)
