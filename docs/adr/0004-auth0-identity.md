# 0004 — Auth0 identity provider

Status: Accepted; implementation scheduled for Milestone 2. Date: 2026-11-04.

Context: Web and ChatGPT must resolve the same student without exposing private data or binding the learning domain permanently to one identity provider.

Decision: Auth0 authenticates users and issues access tokens. The backend owns domain permissions and resource ownership. Store internal Student UUIDs and separately unique external `(provider, issuer, subject)` mappings. Never key identity by email. Use environment-specific tenant/application configuration.

Consequences: Provider migration can add mappings without rewriting student foreign keys. First-login provisioning must be transactional and idempotent. Account linking and issuer migration need explicit verified workflows. No tenant configuration or live flow is claimed by the foundation.
