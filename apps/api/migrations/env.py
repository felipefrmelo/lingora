from alembic import context
from sqlalchemy import create_engine, pool

from lingora.core.config import Settings
from lingora.modules.identity.models import Student
from lingora.modules.onboarding import models as models  # noqa: F401

config = context.config
target_metadata = Student.metadata


def database_url() -> str:
    return config.attributes.get("database_url") or Settings().database_url.get_secret_value()


def run_migrations_offline() -> None:
    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(database_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
