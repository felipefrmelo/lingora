import asyncio
from collections.abc import AsyncIterator
from typing import cast

from fastapi import Request
from sqlalchemy import MetaData, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from lingora.core.config import Settings


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(table_name)s_%(column_0_name)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


class Database:
    def __init__(self, settings: Settings) -> None:
        self.engine = create_async_engine(
            settings.database_url.get_secret_value(),
            pool_pre_ping=True,
            hide_parameters=True,
            connect_args={"connect_timeout": 3},
        )
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)
        self.ready_timeout = settings.db_ready_timeout_seconds

    async def check(self) -> None:
        async with asyncio.timeout(self.ready_timeout), self.engine.connect() as connection:
            await connection.execute(text("SELECT 1"))

    async def close(self) -> None:
        await self.engine.dispose()


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    database = cast(Database, request.app.state.database)
    # Application use cases own commit boundaries; closing rolls back uncommitted work.
    async with database.sessions() as session:
        yield session
