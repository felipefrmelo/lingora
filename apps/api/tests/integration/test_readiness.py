from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr

from lingora.core.config import Settings
from lingora.main import create_app


async def test_readiness_checks_the_actual_postgresql_database(migration_config: Config) -> None:
    app = create_app(
        Settings(
            app_env="test",
            database_url=SecretStr(str(migration_config.attributes["database_url"])),
        )
    )
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client,
    ):
        response = await client.get("/api/v1/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
