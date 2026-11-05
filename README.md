# Lingora

English practice inspired by your world. Lingora will organize personalized lessons, exercises, learning evidence, and progress; ChatGPT will provide conversational practice through MCP.

**Current delivery: Milestone 4 — Content and Lessons (under acceptance verification).** Learners can explore attributed licensed news briefs, prepare private lessons with five exercise types, and save deterministically graded practice. Auth0 and onboarding remain intact. Run a separate worker for generation; see the [lesson guide](docs/lessons.md) and [verification report](docs/lessons-verification.md). MCP conversation and adaptive learning are later milestones.

## Prerequisites

- Python 3.13 and [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Node 24 and pnpm 11 (the exact pnpm version is recorded in `package.json`)
- Docker Desktop or another Docker engine with Docker Compose

On macOS, ensure installed tools are on your shell's PATH:

```sh
export PATH="$HOME/.local/bin:$HOME/.docker/bin:$PATH"
uv --version
docker compose version
docker info
```

Docker Desktop also ships its CLI at `/Applications/Docker.app/Contents/Resources/bin`. If needed, add that directory to PATH. Root Make commands accept `UV`, `PNPM`, and `DOCKER` executable overrides.

## Start locally

Run from the repository root:

```sh
make setup                  # locked installs; creates local env files if absent
make db-up                  # PostgreSQL at localhost:5432
make migrate                # apply Alembic migrations explicitly
make dev-api                # terminal 1: http://127.0.0.1:8000
make dev-web                # terminal 2: http://localhost:5173
```

The local credentials in `.env.example` and Compose are disposable development values. Set `DATABASE_URL` and `CORS_ORIGINS` for your environment. Compose binds PostgreSQL to loopback only. It uses a named volume for development and a separate ephemeral service/database on port 5433 for tests. `make db-down` stops both services and preserves the development volume.

The frontend uses same-origin `/api` calls, proxied by Vite to `127.0.0.1:8000`. `VITE_API_BASE_URL` can point to a separately hosted API; add that frontend origin to backend CORS. Vite environment variables are public build-time values. Production hosting must serve the SPA entry point for client routes and proxy `/api` or configure the API base URL. No deployment is configured.

The API and welcome screen can start without PostgreSQL or Auth0. Liveness remains healthy; readiness returns 503 until PostgreSQL is available. Private requests fail closed when authentication is unavailable. Starting the app does not run migrations or provision students. Follow the [Auth0 guide](docs/auth/auth0-setup.md) to configure login, and use `localhost:5173` consistently with its registered callback URL.

## API

| Endpoint | Behavior |
| --- | --- |
| `GET /api/v1/health` | Liveness: `200 {"status":"ok"}`; no external dependencies |
| `GET /api/v1/ready` | PostgreSQL probe: `200 {"status":"ready"}` or sanitized 503 problem details |
| `GET /openapi.json` | Generated contract source |
| `GET /docs` | Interactive development docs; disabled in production |
| `POST /api/v1/me/bootstrap` | Idempotently create/resolve the verified student; requires `profile:write` |
| `GET /api/v1/me` | Read the verified student's existing account; requires `profile:read` |
| `GET` / `PUT /api/v1/me/profile` | Read/save own learning profile, draft/skip/resume/finish intent, and optimistic version |
| `GET` / `POST /api/v1/me/assessments` | List/create own self-reported assessments with durable creation keys |
| `PUT` / `DELETE /api/v1/me/assessments/{assessment_id}` | Version-checked edits/deletion of an owned assessment |
| `GET /api/v1/me/content` | Licensed topic-filtered briefs with initial activity suggestions |
| `GET` / `POST /api/v1/me/lessons` | Own history / idempotent lesson preparation |
| `GET /api/v1/me/lesson-jobs/{job_id}` | Durable preparation status |
| `GET /api/v1/me/lessons/{lesson_id}` | Own immutable lesson without answer keys |
| `GET` / `POST /api/v1/me/lessons/{lesson_id}/attempts` | Own attempts / confirmed deterministic feedback |

Self-account endpoints accept no student selector. The bootstrap body is empty, and unknown fields are rejected. Responses contain only the internal student UUID and creation timestamp. Login requires a verified-email claim issued by Lingora's scoped Auth0 Action. Auth0 profile information is displayed through the SDK, without using email as the database identity key. Tokens stay in memory; browser privacy settings may require explicit sign-in after a reload. Logout clears private query data and the Auth0 session; existing access tokens expire according to their configured lifetime.

Errors use `application/problem+json` with a request ID. Logs include only a request ID, method, route template, status, and latency. Set `OTEL_EXPORTER_OTLP_ENDPOINT` to an OTLP HTTP collector base URL to enable trace export; no collector is required locally. Query strings, headers, and bodies are excluded from custom telemetry.

## Checks

```sh
make lint typecheck test build
make test-integration
pnpm --filter @lingora/web exec playwright install chromium
make test-e2e
make audit
make check
```

Backend tests use pytest; frontend tests use Vitest and React Testing Library. Playwright starts its own API and Vite servers on ports 8000 and 5173, so stop existing development servers before running it. It checks desktop/mobile layouts, real HTTP communication, and failure recovery. Integration tests refuse to run unless the configured database name ends in `_test` and never target the development database. Without `TEST_DATABASE_URL`, direct pytest integration runs are skipped; `make test-integration` starts the dedicated service and supplies the URL.

```sh
make api-generate
git diff --exit-code -- packages/api-client/openapi.json packages/api-client/src/schema.d.ts
uv run --project apps/api alembic -c apps/api/alembic.ini revision --autogenerate -m "describe change"
uv run --project apps/api alembic -c apps/api/alembic.ini check
```

Review autogenerated migrations before applying them. Never edit generated TypeScript contracts directly. Revision 0003 adds licensed briefs, durable lesson jobs, immutable lessons, attempts, and provider metadata. It preserves the identities and learning records from revisions 0001/0002. Run `make migrate` before using learning endpoints.

## Documentation

- [Content and lesson guide](docs/lessons.md) and [Milestone 4 verification](docs/lessons-verification.md)

- [Onboarding guide](docs/onboarding.md) and [Milestone 3 verification](docs/onboarding-verification.md)
- [Original PRD](docs/product/PRD.md) and [initialization guidelines](docs/product/initialization-guidelines.md)
- [Architecture](docs/architecture/overview.md), [ADRs](docs/adr/README.md), and [roadmap](docs/product/milestones.md)
- [Milestone 1 completion and verification report](docs/verification.md)
- [Auth0 setup](docs/auth/auth0-setup.md), [Milestone 2 verification](docs/auth/verification.md), and [MCP OAuth plan](docs/auth/mcp-oauth.md)
- [Agent instructions](AGENTS.md) and [security boundaries](SECURITY.md)
