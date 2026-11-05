from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AuthenticatedPrincipal:
    issuer: str
    subject: str
    scopes: frozenset[str]


class InvalidCredentials(Exception):
    """A bearer credential is absent or invalid."""


class AuthorizationDenied(Exception):
    """The verified identity lacks permission or a verified email."""


class AuthenticationUnavailable(Exception):
    """Authentication configuration or trusted signing keys are unavailable."""
