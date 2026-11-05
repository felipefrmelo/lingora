import io
import json
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.error import URLError
from urllib.request import Request

import jwt
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from jwt.algorithms import RSAAlgorithm

DOMAIN = "auth.example.test"
ISSUER = f"https://{DOMAIN}/"
AUDIENCE = "https://lingora.local/api"
VERIFIED_CLAIM = AUDIENCE + "/email_verified"


@dataclass
class TokenFactory:
    private_key: RSAPrivateKey

    def __call__(
        self,
        overrides: dict[str, Any] | None = None,
        *,
        omit: tuple[str, ...] = (),
        algorithm: str = "RS256",
        kid: str | None = "key-1",
        key: RSAPrivateKey | str | None = None,
        headers: dict[str, Any] | None = None,
    ) -> str:
        now = int(time.time())
        claims: dict[str, Any] = {
            "iss": ISSUER,
            "aud": AUDIENCE,
            "sub": "auth0|student-one",
            "iat": now,
            "exp": now + 300,
            "scope": "profile:read profile:write",
            VERIFIED_CLAIM: True,
        }
        claims.update(overrides or {})
        for name in omit:
            claims.pop(name, None)
        token_headers = dict(headers or {})
        if kid is not None:
            token_headers["kid"] = kid
        signing_key = self.private_key if key is None else key
        return jwt.encode(claims, signing_key, algorithm=algorithm, headers=token_headers)


def public_jwk(private_key: RSAPrivateKey, kid: str = "key-1") -> dict[str, Any]:
    value: dict[str, Any] = json.loads(RSAAlgorithm.to_jwk(private_key.public_key()))
    return {**value, "kid": kid, "alg": "RS256", "use": "sig"}


@dataclass
class JwksEndpoint:
    keys: list[dict[str, Any]]
    fail: bool = False
    calls: list[tuple[str, float]] = field(default_factory=lambda: list[tuple[str, float]]())

    def open(self, request: Request, *, timeout: float) -> io.BytesIO:
        self.calls.append((request.full_url, timeout))
        if self.fail:
            raise URLError("simulated identity-provider outage")
        return io.BytesIO(json.dumps({"keys": self.keys}).encode())

    def opener(self, *_handlers: object) -> "JwksEndpoint":
        return self
