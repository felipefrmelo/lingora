from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_upgrade_downgrade_and_no_model_drift(migration_config: Config) -> None:
    engine = create_engine(str(migration_config.attributes["database_url"]))
    command.downgrade(migration_config, "base")
    assert "students" not in inspect(engine).get_table_names()
    command.upgrade(migration_config, "head")
    tables = inspect(engine).get_table_names()
    assert "students" in tables
    assert "external_identities" in tables
    command.check(migration_config)
    engine.dispose()
