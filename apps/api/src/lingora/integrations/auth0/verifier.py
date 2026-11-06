from typing import Any

import jwt
from anyio import to_thread
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientConnectionError, PyJWKClientError, PyJWTError

from lingora.core.config import Settings
from lingora.modules.identity.principal import (
    AuthenticatedPrincipal,
    AuthenticationUnavailable,
    AuthorizationDenied,
    InvalidCredentials,
)


class Auth0TokenVerifier:
    def __init__(
        self,
        settings: Settings,
        *,
        jwks: PyJWKClient | None = None,
        audience: str | None = None,
        allowed_clients: frozenset[str] | None = None,
    ) -> None:
        self.settings = settings
        self.audience = audience or settings.auth0_api_audience
        self.allowed_clients = allowed_clients
        self.jwks = jwks
        if self.jwks is None and settings.auth0_configured:
            self.jwks = PyJWKClient(
                settings.auth0_jwks_url,
                cache_keys=False,
                cache_jwk_set=True,
                lifespan=settings.auth0_jwks_cache_seconds,
                timeout=settings.auth0_jwks_timeout_seconds,
                cooldown_duration=30,
            )

    async def verify(self, token: str) -> AuthenticatedPrincipal:
        # PyJWKClient performs synchronous HTTPS I/O; keep it off the event loop.
        return await to_thread.run_sync(self._verify, token)

    def _verify(self, token: str) -> AuthenticatedPrincipal:
        if not self.settings.auth0_configured or self.jwks is None:
            raise AuthenticationUnavailable
        try:
            header = jwt.get_unverified_header(token)
            if (
                header.get("alg") != "RS256"
                or not isinstance(header.get("kid"), str)
                or not header["kid"]
            ):
                raise InvalidCredentials
            key = self.jwks.get_signing_key_from_jwt(token)
            claims: dict[str, Any] = jwt.decode(
                token,
                key.key,
                algorithms=["RS256"],
                issuer=self.settings.auth0_issuer,
                audience=self.audience,
                options={"require": ["exp", "iss", "aud", "sub", "iat"]},
            )
        except PyJWKClientConnectionError:
            raise AuthenticationUnavailable from None
        except (PyJWKClientError, PyJWTError, ValueError, TypeError):
            raise InvalidCredentials from None

        subject = claims["sub"]
        if not isinstance(subject, str) or not subject or len(subject) > 255:
            raise InvalidCredentials
        if claims.get("gty") == "client-credentials" or subject.endswith("@clients"):
            raise InvalidCredentials
        if claims.get(self.settings.auth0_email_verified_claim) is not True:
            raise AuthorizationDenied
        client_id = claims.get("azp")
        issued_at = claims.get("iat")
        if self.allowed_clients is not None and (
            not isinstance(client_id, str)
            or client_id not in self.allowed_clients
            or type(issued_at) is not int
        ):
            raise InvalidCredentials
        scope = claims.get("scope", "")
        if not isinstance(scope, str):
            raise InvalidCredentials
        return AuthenticatedPrincipal(
            issuer=self.settings.auth0_issuer,
            subject=subject,
            scopes=frozenset(scope.split()),
            issued_at=issued_at if type(issued_at) is int else None,
            client_id=client_id if isinstance(client_id, str) else None,
        )
