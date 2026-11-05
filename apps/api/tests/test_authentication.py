import asyncio
import time

import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from lingora.core.config import Settings
from lingora.integrations.auth0.verifier import Auth0TokenVerifier
from lingora.modules.identity.principal import (
    AuthenticationUnavailable,
    AuthorizationDenied,
    InvalidCredentials,
)
from tests.auth_support import ISSUER, VERIFIED_CLAIM, JwksEndpoint, TokenFactory, public_jwk


async def test_verifies_signature_and_uses_only_trusted_jwks(
    auth_settings: Settings, jwks_endpoint: JwksEndpoint, token_factory: TokenFactory
) -> None:
    verifier = Auth0TokenVerifier(auth_settings)
    principal = await verifier.verify(
        token_factory(headers={"jku": "https://attacker.example/keys"})
    )
    assert principal.subject == "auth0|student-one"
    assert principal.issuer == ISSUER
    assert principal.scopes == frozenset({"profile:read", "profile:write"})
    assert jwks_endpoint.calls == [(auth_settings.auth0_jwks_url, 5)]
    await verifier.verify(token_factory())
    assert len(jwks_endpoint.calls) == 1


@pytest.mark.parametrize(
    "overrides",
    [
        {"iss": "https://other.example/"},
        {"aud": "different-api"},
        {"exp": 1},
        {"nbf": int(time.time()) + 3600},
        {"iat": int(time.time()) + 3600},
        {"sub": ""},
        {"sub": 123},
        {"scope": ["profile:read"]},
        {"gty": "client-credentials"},
        {"sub": "client-id@clients"},
    ],
)
async def test_rejects_invalid_claims(
    auth_settings: Settings,
    jwks_endpoint: JwksEndpoint,
    token_factory: TokenFactory,
    overrides: dict[str, object],
) -> None:
    with pytest.raises(InvalidCredentials):
        await Auth0TokenVerifier(auth_settings).verify(token_factory(overrides))


@pytest.mark.parametrize("claim", ["iss", "aud", "sub", "exp", "iat"])
async def test_requires_identity_and_time_claims(
    auth_settings: Settings, jwks_endpoint: JwksEndpoint, token_factory: TokenFactory, claim: str
) -> None:
    with pytest.raises(InvalidCredentials):
        await Auth0TokenVerifier(auth_settings).verify(token_factory(omit=(claim,)))


@pytest.mark.parametrize("verified", [False, None, "true", 1])
async def test_verification_must_be_a_true_boolean(
    auth_settings: Settings,
    jwks_endpoint: JwksEndpoint,
    token_factory: TokenFactory,
    verified: object,
) -> None:
    with pytest.raises(AuthorizationDenied):
        await Auth0TokenVerifier(auth_settings).verify(token_factory({VERIFIED_CLAIM: verified}))


async def test_missing_verification_claim_is_denied(
    auth_settings: Settings, jwks_endpoint: JwksEndpoint, token_factory: TokenFactory
) -> None:
    with pytest.raises(AuthorizationDenied):
        await Auth0TokenVerifier(auth_settings).verify(token_factory(omit=(VERIFIED_CLAIM,)))


async def test_rejects_invalid_signature_and_unknown_keys(
    auth_settings: Settings, jwks_endpoint: JwksEndpoint, token_factory: TokenFactory
) -> None:
    wrong_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    verifier = Auth0TokenVerifier(auth_settings)
    for token in [token_factory(key=wrong_key), token_factory(kid="not-trusted")]:
        with pytest.raises(InvalidCredentials):
            await verifier.verify(token)
    # Unknown IDs cannot cause unlimited forced refreshes during the cooldown.
    assert len(jwks_endpoint.calls) == 1


@pytest.mark.parametrize("algorithm", ["HS256", "none"])
async def test_rejects_disallowed_algorithms_before_fetching_keys(
    auth_settings: Settings,
    jwks_endpoint: JwksEndpoint,
    token_factory: TokenFactory,
    algorithm: str,
) -> None:
    with pytest.raises(InvalidCredentials):
        await Auth0TokenVerifier(auth_settings).verify(
            token_factory(
                algorithm=algorithm,
                key="" if algorithm == "none" else "local-test-key-that-is-long-enough-for-hs256",
            )
        )
    assert jwks_endpoint.calls == []


@pytest.mark.parametrize("token", ["garbage", "a.b.c", "", "Bearer token"])
async def test_rejects_malformed_tokens(auth_settings: Settings, token: str) -> None:
    with pytest.raises(InvalidCredentials):
        await Auth0TokenVerifier(auth_settings).verify(token)


async def test_missing_kid_is_rejected_before_network(
    auth_settings: Settings, jwks_endpoint: JwksEndpoint, token_factory: TokenFactory
) -> None:
    with pytest.raises(InvalidCredentials):
        await Auth0TokenVerifier(auth_settings).verify(token_factory(kid=None))
    assert jwks_endpoint.calls == []


async def test_outage_does_not_wipe_valid_cached_keys(
    auth_settings: Settings, jwks_endpoint: JwksEndpoint, token_factory: TokenFactory
) -> None:
    verifier = Auth0TokenVerifier(auth_settings)
    await verifier.verify(token_factory())
    jwks_endpoint.fail = True
    await verifier.verify(token_factory())
    with pytest.raises(AuthenticationUnavailable):
        await Auth0TokenVerifier(auth_settings).verify(token_factory())


async def test_rotation_after_cache_expiry(
    auth_settings: Settings, jwks_endpoint: JwksEndpoint, token_factory: TokenFactory
) -> None:
    verifier = Auth0TokenVerifier(auth_settings.model_copy(update={"auth0_jwks_cache_seconds": 1}))
    await verifier.verify(token_factory())
    rotated_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwks_endpoint.keys = [public_jwk(rotated_key, "key-2")]
    await asyncio.sleep(1.05)
    principal = await verifier.verify(token_factory(key=rotated_key, kid="key-2"))
    assert principal.subject == "auth0|student-one"
    assert len(jwks_endpoint.calls) == 2


async def test_missing_and_wrong_authentication_use_401(client: AsyncClient) -> None:
    for headers in [{}, {"Authorization": "Basic abc"}]:
        response = await client.get("/api/v1/me", headers=headers)
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"


async def test_unconfigured_private_endpoint_fails_closed(client: AsyncClient) -> None:
    response = await client.get("/api/v1/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 503
    assert (await client.get("/api/v1/health")).status_code == 200


async def test_scope_and_verification_errors_use_403(
    authenticated_app: FastAPI, token_factory: TokenFactory
) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=authenticated_app), base_url="http://test"
    ) as client:
        for claims in [{"scope": "profile:write"}, {VERIFIED_CLAIM: False}]:
            response = await client.get(
                "/api/v1/me", headers={"Authorization": "Bearer " + token_factory(claims)}
            )
            assert response.status_code == 403


async def test_invalid_token_uses_bearer_challenge(
    authenticated_app: FastAPI, token_factory: TokenFactory
) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=authenticated_app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/me", headers={"Authorization": "Bearer " + token_factory({"exp": 1})}
        )
    assert response.status_code == 401
    assert 'error="invalid_token"' in response.headers["www-authenticate"]


async def test_rejects_client_supplied_identity_fields(
    authenticated_app: FastAPI, token_factory: TokenFactory
) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=authenticated_app), base_url="http://test"
    ) as client:
        headers = {"Authorization": "Bearer " + token_factory()}
        response = await client.post(
            "/api/v1/me/bootstrap", headers=headers, json={"student_id": "someone-else"}
        )
        assert response.status_code == 422
        response = await client.get("/api/v1/me?student_id=someone-else", headers=headers)
        assert response.status_code == 422


async def test_authentication_outage_is_not_invalid_login(
    authenticated_app: FastAPI, jwks_endpoint: JwksEndpoint, token_factory: TokenFactory
) -> None:
    jwks_endpoint.fail = True
    async with AsyncClient(
        transport=ASGITransport(app=authenticated_app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/me", headers={"Authorization": "Bearer " + token_factory()}
        )
    assert response.status_code == 503


def test_partial_authentication_configuration_is_rejected() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Settings(auth0_domain="auth.example.test")
