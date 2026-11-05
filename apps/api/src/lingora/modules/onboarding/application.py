import hashlib
import json
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from lingora.modules.identity.application import find_student
from lingora.modules.identity.principal import AuthenticatedPrincipal
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
from lingora.modules.onboarding.models import (
    AssessmentCreation,
    PlacementAssessment,
    StudentProfile,
)


async def student_id(session: AsyncSession, principal: AuthenticatedPrincipal) -> UUID:
    student = await find_student(session, principal)
    if student is None:
        raise ResourceNotFound
    return student.id


async def read_profile(session: AsyncSession, principal: AuthenticatedPrincipal) -> ProfileResponse:
    async with session.begin():
        owner = await student_id(session, principal)
        row = await session.get(StudentProfile, owner)
        return ProfileResponse.model_validate(row) if row else ProfileResponse()


async def write_profile(
    session: AsyncSession, principal: AuthenticatedPrincipal, data: ProfileWrite
) -> ProfileResponse:
    try:
        async with session.begin():
            owner = await student_id(session, principal)
            row = await session.scalar(
                select(StudentProfile).where(StudentProfile.student_id == owner).with_for_update()
            )
            if data.expected_version != (row.version if row else 0):
                raise VersionConflict
            if row is None:
                row = StudentProfile(student_id=owner, version=0)
                session.add(row)
            for key, value in data.model_dump(exclude={"expected_version", "intent"}).items():
                setattr(row, key, value)
            if row.onboarding_status != "completed":
                row.onboarding_status = {
                    "save": row.onboarding_status or "in_progress",
                    "resume": "in_progress",
                    "skip": "skipped",
                    "finish": "completed",
                }[data.intent]
                if data.intent == "finish":
                    row.completed_at = datetime.now(UTC)
            row.version += 1
            await session.flush()
            await session.refresh(row)
            return ProfileResponse.model_validate(row)
    except IntegrityError:
        # Two first profile writes cannot both insert the one-to-one row.
        raise VersionConflict from None


async def list_assessments(
    session: AsyncSession, principal: AuthenticatedPrincipal, limit: int, offset: int
) -> AssessmentList:
    async with session.begin():
        owner = await student_id(session, principal)
        query = select(PlacementAssessment).where(PlacementAssessment.student_id == owner)
        rows = await session.scalars(
            query.order_by(
                PlacementAssessment.taken_on.desc(),
                PlacementAssessment.created_at.desc(),
                PlacementAssessment.id,
            )
            .limit(limit)
            .offset(offset)
        )
        total = await session.scalar(
            select(func.count())
            .select_from(PlacementAssessment)
            .where(PlacementAssessment.student_id == owner)
        )
        return AssessmentList(
            items=[AssessmentResponse.model_validate(row) for row in rows], total=total or 0
        )


async def replay_creation(
    session: AsyncSession, owner: UUID, key: UUID, fingerprint: str
) -> AssessmentResponse | None:
    receipt = await session.get(AssessmentCreation, (owner, key))
    if receipt is None:
        return None
    if receipt.request_hash != fingerprint:
        raise VersionConflict
    if receipt.assessment_id is None:
        raise CreationGone
    row = await session.get(PlacementAssessment, receipt.assessment_id)
    if row is None:
        raise CreationGone
    return AssessmentResponse.model_validate(row)


async def create_assessment(
    session: AsyncSession, principal: AuthenticatedPrincipal, data: AssessmentFields, key: UUID
) -> tuple[AssessmentResponse, bool]:
    values = data.model_dump(mode="json")
    fingerprint = hashlib.sha256(
        json.dumps(values, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    try:
        async with session.begin():
            owner = await student_id(session, principal)
            previous = await replay_creation(session, owner, key, fingerprint)
            if previous is not None:
                return previous, False
            row = PlacementAssessment(**{**values, "taken_on": data.taken_on}, student_id=owner)
            session.add(row)
            await session.flush()
            session.add(
                AssessmentCreation(
                    student_id=owner, key=key, request_hash=fingerprint, assessment_id=row.id
                )
            )
            await session.flush()
            await session.refresh(row)
            return AssessmentResponse.model_validate(row), True
    except IntegrityError:
        # Roll back the whole losing creation, not just its receipt.
        async with session.begin():
            owner = await student_id(session, principal)
            winner = await replay_creation(session, owner, key, fingerprint)
            if winner is None:
                raise
            return winner, False


async def owned_assessment(
    session: AsyncSession, owner: UUID, assessment_id: UUID
) -> PlacementAssessment:
    row = await session.scalar(
        select(PlacementAssessment)
        .where(PlacementAssessment.id == assessment_id, PlacementAssessment.student_id == owner)
        .with_for_update()
    )
    if row is None:
        raise ResourceNotFound
    return row


async def update_assessment(
    session: AsyncSession,
    principal: AuthenticatedPrincipal,
    assessment_id: UUID,
    data: AssessmentWrite,
) -> AssessmentResponse:
    async with session.begin():
        row = await owned_assessment(session, await student_id(session, principal), assessment_id)
        if row.version != data.expected_version:
            raise VersionConflict
        values = data.model_dump(mode="json", exclude={"expected_version"})
        values["taken_on"] = data.taken_on
        for key, value in values.items():
            setattr(row, key, value)
        row.version += 1
        await session.flush()
        await session.refresh(row)
        return AssessmentResponse.model_validate(row)


async def delete_assessment(
    session: AsyncSession,
    principal: AuthenticatedPrincipal,
    assessment_id: UUID,
    expected_version: int,
) -> None:
    async with session.begin():
        row = await owned_assessment(session, await student_id(session, principal), assessment_id)
        if row.version != expected_version:
            raise VersionConflict
        await session.delete(row)
