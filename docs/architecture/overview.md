# Architecture

## Delivery boundary

This is a modular monolith with a React SPA and one Python deployment. Milestone 2 adds Auth0 authentication and self-account provisioning to the operational foundation. The PRD defines the full product; the initialization guidelines split it into seven technical milestones. Onboarding, learning workflows, and MCP remain outside this delivery.

## Runtime and dependency flow

```text
React routes/features -> TanStack Query -> generated API client -> FastAPI
                                                               |
Future ChatGPT -> OAuth-protected MCP adapter ------------------+-> application use cases
                                                                    |
                                                               business modules
                                                                    |
                                                          PostgreSQL / provider adapters
```

REST and MCP adapt the same application operations. MCP does not forward its incoming bearer token to REST, and business rules do not depend on ChatGPT conversation memory. Avoid circular imports between modules; integrations depend on narrow application contracts when actual integrations exist.

Create modules incrementally for identity, onboarding, placement, competencies, content, lessons, exercises, learning plans/sessions, pedagogical memory, and reviews. The identity module currently implements authenticated self-account operations. An immutable principal carries verified issuer, subject, and scopes independently of FastAPI. The Auth0 adapter performs synchronous JWT/JWKS work in a worker thread; HTTP dependencies enforce endpoint scopes and the identity application use case resolves the internal Student UUID.

## Persistence and transactions

SQLAlchemy 2 uses psycopg 3 async I/O in request workflows. Application use cases own `session.begin()` boundaries. Dependencies supply sessions but never commit automatically. Alembic uses synchronous connections in its separate CLI process; it does not block the request event loop. Migrations are explicit release/development operations and never run at application startup.

`students` contains internal UUIDs and timestamps. `external_identities` maps `(provider, issuer, subject)` uniquely to a student, indexes the foreign key, and cascades mappings on student deletion. Email is not an identity key. One student may have multiple intentionally linked mappings; account linking needs a verified future workflow. `updated_at` updates through SQLAlchemy ORM writes; raw SQL callers must maintain it explicitly. Provider names and email remain in the Auth0 SDK profile; the database stores no profile, token, or transcript. Concurrent first logins roll back a losing student insert before resolving the winning identity.

Add student ownership foreign keys, resource-level authorization, version fields, idempotency keys, and audit events with the first business operations that require them. Do not build the entire PRD schema in advance. Database row-level security is a future defense-in-depth decision, not a replacement for backend checks.

## Frontend and contracts

Typed TanStack routes organize navigation; Query owns server state. Components live with their features. The foundation has no forms yet, but React Hook Form, Zod, and resolvers are available for onboarding. Tailwind tokens and a minimal shadcn-style Button establish accessible component conventions. No global state store or SSR is needed.

FastAPI/Pydantic define wire contracts. Export OpenAPI without executing lifespan connections, then generate types with `openapi-typescript`. `openapi-fetch` provides a typed client. CI regenerates both artifacts and rejects drift. Do not manually mirror backend request/response types.

## Configuration and observability

Settings read environment variables, plus optional root `.env` in local commands. Auth0 configuration is optional as a complete group; partial or inconsistent issuer/JWKS settings are rejected. Private operations fail closed when the group is absent. Database credentials use `SecretStr`. CORS accepts exact origins only. Tracing is opt-in through an OTLP HTTP collector; operational logging uses an explicit field allowlist and server-generated request IDs.

Liveness has no dependencies. Readiness performs a bounded PostgreSQL probe, not a guarantee that every future migration or provider is ready. Public readiness failures are sanitized. `GET /api/v1/me` retrieves the verified student; `POST /api/v1/me/bootstrap` provisions it idempotently. Both require verified email and their respective profile scopes.

## Development and delivery

Root Make commands orchestrate uv, pnpm, and Docker. PostgreSQL has separate development and test services; tests refuse non-test database names. CI uses service-container PostgreSQL and deterministic tests, with no tenant or AI credentials. Docker Compose currently runs database services only; production application containers and hosting are deferred until deployment requirements are known.

Important jobs will use a durable worker/queue once required. FastAPI BackgroundTasks must not be used for generation, reviews, or writes that must survive restart. The AI boundary will use structured outputs, versioned prompts, deterministic fakes, and evaluation data when lesson generation is implemented.
