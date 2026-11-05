from uuid import uuid4

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


def test_upgrade_downgrade_and_no_model_drift(migration_config: Config) -> None:
    engine = create_engine(str(migration_config.attributes["database_url"]))
    command.downgrade(migration_config, "base")
    assert "students" not in inspect(engine).get_table_names()
    command.upgrade(migration_config, "0001")
    student_id, identity_id = uuid4(), uuid4()
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO students (id) VALUES (:id)"), {"id": student_id})
        connection.execute(
            text(
                "INSERT INTO external_identities (id, student_id, provider, issuer, subject) "
                "VALUES (:id, :student_id, 'auth0', "
                "'https://auth.example.test/', 'migration-student')"
            ),
            {"id": identity_id, "student_id": student_id},
        )
    command.upgrade(migration_config, "0002")
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO student_profiles "
                "(student_id, goals, interests, correction_mode, "
                "onboarding_status, version, selected_cefr) "
                "VALUES (:id, '[]', '[]', 'balanced', 'skipped', 1, 'B1')"
            ),
            {"id": student_id},
        )
    command.upgrade(migration_config, "head")
    tables = inspect(engine).get_table_names()
    assert "students" in tables
    assert "external_identities" in tables
    assert "student_profiles" in tables
    assert "placement_assessments" in tables
    with engine.connect() as connection:
        assert (
            connection.scalar(
                text("SELECT student_id FROM external_identities WHERE id = :id"),
                {"id": identity_id},
            )
            == student_id
        )
        assert connection.scalar(text("SELECT count(*) FROM student_profiles")) == 1
        assert (
            connection.scalar(
                text("SELECT onboarding_status FROM student_profiles WHERE student_id = :id"),
                {"id": student_id},
            )
            == "skipped"
        )
    assert {
        "contents",
        "lessons",
        "lesson_jobs",
        "exercise_attempts",
        "generation_events",
    }.issubset(tables)
    command.downgrade(migration_config, "0002")
    assert "lessons" not in inspect(engine).get_table_names()
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM student_profiles")) == 1
    command.upgrade(migration_config, "head")
    command.check(migration_config)
    engine.dispose()
