# Lingora

Lingora organizes English learning; ChatGPT will provide conversational tutoring. The backend is the authoritative source of student data. Read [PRD](docs/product/PRD.md) and [architecture](docs/architecture/overview.md) before implementing features.

## Architecture

- Modular monolith: FastAPI and future MCP adapters call the same application use cases.
- Keep business rules independent of HTTP, MCP, Auth0 SDKs, and AI providers. Add abstractions only at useful integration boundaries.
- Add working modules incrementally. Do not generate empty module trees or implement later milestones incidentally.
- Use PostgreSQL, SQLAlchemy 2, psycopg 3, and Alembic; never use `create_all` as a migration replacement.
- Use explicit transactions. Session dependencies never silently commit.
- OpenAPI is the wire-contract source. Run `make api-generate`; never hand-edit the generated schema or duplicate DTOs in TypeScript.
- Use TanStack Query for server state and TanStack Router for routing. Keep frontend features together.

## Commands (repository root)

Prerequisites: Python 3.13, uv, Node 24, pnpm 11, Docker with Compose; see README for PATH setup.

```sh
make setup
make db-up migrate
make dev-api                 # terminal 1
make dev-web                 # terminal 2
make lint typecheck test build
make test-integration        # isolated PostgreSQL database
pnpm --filter @lingora/web exec playwright install chromium
make test-e2e
make api-generate
make audit
make check                   # all non-audit checks
```

## Security and identity

- Auth0 is mandatory. No custom OAuth server or development authentication bypass.
- Public health endpoints need no credentials. Private endpoints must validate access tokens, scopes, and ownership on the backend.
- Resolve internal Student UUIDs from verified `(provider, issuer, subject)` mappings. Never authorize using an arbitrary student ID or email.
- Never log raw tokens, student content, or conversations. `VITE_` values are public. Do not commit credentials.
- Follow [Auth0 setup](docs/auth/auth0-setup.md) and [MCP OAuth](docs/auth/mcp-oauth.md). Authentication is implemented; real acceptance results must be recorded separately. MCP remains a later milestone.
- Scope tenant Actions to the dedicated Lingora client. The shared legacy linker must exclude Lingora's client and database identities, including candidates reached through other applications; see `infra/auth0/legacy-linker-exclusion.md`.
- For MCP, use the official SDK and business operations; verify scopes and ownership, validate schemas, and make retry-sensitive writes idempotent.
- Onboarding and assessments resolve the authenticated student; never accept client-supplied ownership. Preserve raw scores, keep selected CEFR explicit, and use optimistic versions/durable creation keys. Clear all private queries and pending requests on logout/identity changes. See [onboarding](docs/onboarding.md).
- An observation is evidence, not proof of mastery. One mistake must not establish a persistent deficiency.

## Definition of Done

Document behavior and configuration changes, add meaningful tests for changed behavior, run relevant checks, update migrations/contracts when needed, and report only checks actually executed. Ordinary CI needs no live Auth0 or AI credentials. Real authentication tests are opt-in and gate Milestone 2 completion. Never deploy automatically.

Important decisions: [ADRs](docs/adr/README.md). Roadmap: [milestones](docs/product/milestones.md).
