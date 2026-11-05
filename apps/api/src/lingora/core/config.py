from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", frozen=True)

    app_env: Literal["development", "test", "production"] = "development"
    database_url: SecretStr = SecretStr(
        "postgresql+psycopg://lingora:lingora_local@localhost:5432/lingora"
    )
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    db_ready_timeout_seconds: float = Field(default=2, gt=0, le=10)
    otel_exporter_otlp_endpoint: str = ""
    auth0_domain: str = ""
    auth0_issuer: str = ""
    auth0_api_audience: str = ""
    auth0_jwks_url: str = ""
    auth0_email_verified_claim: str = "https://lingora.local/api/email_verified"
    auth0_jwks_cache_seconds: int = Field(default=300, ge=1, le=3600)
    auth0_jwks_timeout_seconds: float = Field(default=5, gt=0, le=10)

    @property
    def auth0_configured(self) -> bool:
        return bool(
            self.auth0_domain
            and self.auth0_issuer
            and self.auth0_api_audience
            and self.auth0_jwks_url
        )

    @model_validator(mode="after")
    def validate_auth0(self) -> "Settings":
        from urllib.parse import urlsplit

        values = (
            self.auth0_domain,
            self.auth0_issuer,
            self.auth0_api_audience,
            self.auth0_jwks_url,
        )
        if not any(values):
            return self
        if not all(values):
            raise ValueError(
                "Auth0 domain, issuer, API audience, and JWKS URL must be configured together"
            )
        expected = f"https://{self.auth0_domain}/"
        if self.auth0_issuer != expected:
            raise ValueError(
                "AUTH0_ISSUER must match the HTTPS tenant domain with a trailing slash"
            )
        if self.auth0_jwks_url != expected + ".well-known/jwks.json":
            raise ValueError("AUTH0_JWKS_URL must be the configured issuer's trusted JWKS endpoint")
        parsed = urlsplit(expected)
        if (
            parsed.hostname != self.auth0_domain
            or parsed.username
            or parsed.password
            or parsed.port
        ):
            raise ValueError("AUTH0_DOMAIN must be a hostname")
        if not self.auth0_api_audience.startswith("https://"):
            raise ValueError("AUTH0_API_AUDIENCE must be an HTTPS resource identifier")
        return self

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: SecretStr) -> SecretStr:
        try:
            url = make_url(value.get_secret_value())
        except Exception:
            raise ValueError("DATABASE_URL must be a PostgreSQL connection URL") from None
        if url.drivername != "postgresql+psycopg":
            raise ValueError("DATABASE_URL must use the postgresql+psycopg driver")
        return value

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, value: list[str]) -> list[str]:
        from urllib.parse import urlsplit

        for origin in value:
            parsed = urlsplit(origin)
            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.netloc
                or "*" in origin
                or parsed.path
                or parsed.query
                or parsed.fragment
                or parsed.username
                or parsed.password
            ):
                raise ValueError("CORS origins must be exact HTTP(S) origins without paths")
        return value
