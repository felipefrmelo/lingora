import pytest
from pydantic import SecretStr, ValidationError

from lingora.core.config import Settings
from lingora.main import create_app


@pytest.mark.parametrize("url", ["sqlite:///test.db", "postgresql://localhost/db", "not-a-url"])
def test_rejects_unsupported_database_drivers(url: str) -> None:
    with pytest.raises(ValidationError):
        Settings(database_url=SecretStr(url))


@pytest.mark.parametrize(
    "origin", ["*", "https://*.example", "https://app.example/", "https://app.example/path"]
)
def test_rejects_wildcard_or_non_origin_cors_values(origin: str) -> None:
    with pytest.raises(ValidationError):
        Settings(cors_origins=[origin])


def test_ready_timeout_is_bounded() -> None:
    with pytest.raises(ValidationError):
        Settings(db_ready_timeout_seconds=60)


def test_database_credentials_are_redacted_in_settings() -> None:
    settings = Settings(database_url=SecretStr("postgresql+psycopg://u:secret@db/app"))
    assert "secret" not in repr(settings)


def test_openapi_export_has_stable_operations_and_no_external_dependencies() -> None:
    schema = create_app(Settings(otel_exporter_otlp_endpoint="")).openapi()
    assert schema["paths"]["/api/v1/health"]["get"]["operationId"] == "getHealth"
    assert schema["paths"]["/api/v1/ready"]["get"]["operationId"] == "getReadiness"
    responses = schema["paths"]["/api/v1/ready"]["get"]["responses"]
    assert set(responses["503"]["content"]) == {"application/problem+json"}
    assert set(responses["default"]["content"]) == {"application/problem+json"}
