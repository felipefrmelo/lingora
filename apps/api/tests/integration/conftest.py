import os
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import delete
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from lingora.modules.identity.models import ExternalIdentity, Student


@pytest.fixture(scope="session")
def migration_config() -> Config:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to run PostgreSQL integration tests")
    database = make_url(url).database
    if database is None or not database.endswith("_test"):
        pytest.fail("Integration tests require a database name ending in _test")
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    config.attributes["database_url"] = url
    command.upgrade(config, "head")
    return config


@pytest.fixture
async def session(migration_config: Config) -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(str(migration_config.attributes["database_url"]))
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as database_session:
        async with database_session.begin():
            await database_session.execute(delete(ExternalIdentity))
            await database_session.execute(delete(Student))
        yield database_session
    await engine.dispose()
