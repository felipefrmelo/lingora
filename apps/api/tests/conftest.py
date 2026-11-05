from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr

from lingora.core.config import Settings
from lingora.main import create_app
from tests.auth_support import AUDIENCE, DOMAIN, ISSUER, JwksEndpoint, TokenFactory, public_jwk


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    for name in (
        "OPENAI_API_KEY",
        "LESSON_MODEL",
        "LESSON_TIMEOUT_SECONDS",
        "DATABASE_URL",
        "CORS_ORIGINS",
        "DB_READY_TIMEOUT_SECONDS",
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "AUTH0_DOMAIN",
        "AUTH0_ISSUER",
        "AUTH0_API_AUDIENCE",
        "AUTH0_JWKS_URL",
        "AUTH0_EMAIL_VERIFIED_CLAIM",
        "AUTH0_JWKS_CACHE_SECONDS",
        "AUTH0_JWKS_TIMEOUT_SECONDS",
    ):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def app() -> FastAPI:
    return create_app(
        Settings(
            app_env="test",
            database_url=SecretStr("postgresql+psycopg://test:test@127.0.0.1:1/test"),
            otel_exporter_otlp_endpoint="",
        )
    )


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http,
    ):
        yield http


@pytest.fixture(scope="session")
def signing_key() -> RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def token_factory(signing_key: RSAPrivateKey) -> TokenFactory:
    return TokenFactory(signing_key)


@pytest.fixture
def auth_settings() -> Settings:
    return Settings(
        app_env="test",
        auth0_domain=DOMAIN,
        auth0_issuer=ISSUER,
        auth0_api_audience=AUDIENCE,
        auth0_jwks_url=ISSUER + ".well-known/jwks.json",
    )


@pytest.fixture
def jwks_endpoint(monkeypatch: pytest.MonkeyPatch, signing_key: RSAPrivateKey) -> JwksEndpoint:
    endpoint = JwksEndpoint([public_jwk(signing_key)])
    monkeypatch.setattr("jwt.jwks_client.urllib.request.build_opener", endpoint.opener)
    return endpoint


@pytest.fixture
def authenticated_app(auth_settings: Settings, jwks_endpoint: JwksEndpoint) -> FastAPI:
    return create_app(auth_settings)
