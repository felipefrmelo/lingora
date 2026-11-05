# 0004 — Auth0 identity provider

Status: Accepted; implemented in Milestone 2, with live acceptance tracked separately. Date: 2026-11-04.

Context: Web and ChatGPT must resolve the same student without exposing private data or binding the learning domain permanently to one identity provider.

Decision: Auth0 authenticates users and issues access tokens. The backend owns domain permissions and resource ownership. Store internal Student UUIDs and separately unique external `(provider, issuer, subject)` mappings. Never key identity by email. Use environment-specific tenant/application configuration.

Consequences: Provider migration can add mappings without rewriting student foreign keys. First-login provisioning is transactional and idempotent, including concurrent requests. Account linking and issuer migration need explicit verified workflows. The existing tenant has a shared automatic linker: Lingora's client/database and candidate identities must be excluded to preserve its separate-identity policy. Read the authentication guide for actual tenant/live acceptance status.
