from uuid import uuid4

import pytest
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from lingora.modules.identity.models import ExternalIdentity, Student

pytestmark = pytest.mark.integration


def identity(student: Student, *, issuer: str = "https://auth.example/") -> ExternalIdentity:
    return ExternalIdentity(
        student_id=student.id, provider="auth0", issuer=issuer, subject="google-oauth2|123"
    )


async def test_identity_uniqueness_and_issuer_isolation(session: AsyncSession) -> None:
    student = Student()
    async with session.begin():
        session.add(student)
        await session.flush()
        session.add(identity(student))
        session.add(identity(student, issuer="https://other-tenant.example/"))
    with pytest.raises(IntegrityError):
        async with session.begin():
            session.add(identity(student))
    # Rollback expires ORM state even with expire_on_commit=False; refresh explicitly.
    await session.refresh(student)
    assert len((await session.scalars(select(ExternalIdentity))).all()) == 2
    assert student.created_at.tzinfo is not None


async def test_foreign_key_rejects_nonexistent_student(session: AsyncSession) -> None:
    with pytest.raises(IntegrityError):
        async with session.begin():
            session.add(
                ExternalIdentity(
                    student_id=uuid4(),
                    provider="auth0",
                    issuer="https://auth.example/",
                    subject="abc",
                )
            )


async def test_transaction_failure_rolls_back_student(session: AsyncSession) -> None:
    student = Student(id=uuid4())
    with pytest.raises(RuntimeError, match="cancel"):
        async with session.begin():
            session.add(student)
            await session.flush()
            raise RuntimeError("cancel")
    assert await session.get(Student, student.id) is None


async def test_deleting_student_removes_external_identity(session: AsyncSession) -> None:
    student = Student()
    async with session.begin():
        session.add(student)
        await session.flush()
        session.add(identity(student))
    async with session.begin():
        await session.execute(delete(Student).where(Student.id == student.id))
    assert (await session.scalars(select(ExternalIdentity))).all() == []
