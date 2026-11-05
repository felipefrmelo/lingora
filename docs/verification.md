# Milestone 1 completion report

Verified locally on **2026-11-04**, using Python 3.13.17, uv 0.13.7, Node 24.22.1, pnpm 11.25.0, Docker 29.9.2, Compose 5.6.1, and PostgreSQL 18.6.

## Delivered

The repository is initialized as a pnpm monorepo with a uv-managed FastAPI modular monolith, React/Vite SPA, and generated OpenAPI client. The welcome page communicates with the real public API and handles loading, failure, and recovery. Development PostgreSQL and isolated test PostgreSQL run through Docker Compose.

The initial Alembic migration creates internal students and separately unique external identity mappings. The development migration was applied. No login, student provisioning endpoint, or learner-data endpoint exists yet. Operational endpoints expose liveness and bounded database readiness with consistent, schema-described problem responses.

### Main files

| Area | Files |
| --- | --- |
| Repository and workflow | Root package/workspace manifests, lockfiles, Makefile, Compose configuration, environment examples, ignore/editor settings |
| Backend | `apps/api/pyproject.toml`, `uv.lock`, `src/lingora/`, Alembic configuration/migrations, OpenAPI export script, tests |
| Frontend | `apps/web/` application, feature/component structure, Tailwind tokens, shadcn configuration, Vitest and Playwright suites |
| API contracts | `packages/api-client/` OpenAPI JSON, generated TypeScript definitions, typed HTTP client |
| CI | `.github/workflows/ci.yml`, with official actions pinned to verified commit hashes |
| Engineering guidance | README, AGENTS.md, SECURITY.md, architecture overview, nine ADRs, Auth0/MCP guides, roadmap |
| Product requirements | Original Portuguese PRD and supplied initialization guidelines, preserved under `docs/product/` |

### Architectural decisions

The [nine ADRs](adr/README.md) cover modular monolith boundaries, FastAPI/uv, React/Vite and generated contracts, mandatory Auth0 identity, React authentication, separate MCP authorization, PostgreSQL, deferred durable background processing, and future AI provider boundaries. [Architecture overview](architecture/overview.md) describes transaction ownership, module dependencies, and the shared REST/MCP application layer.

## Executed verification

| Check | Result |
| --- | --- |
| Locked setup: `make setup` | Passed; local environment files created without overwriting existing files |
| Python lint and formatting: Ruff | Passed |
| Frontend lint: ESLint | Passed |
| Strict backend typing: Pyright | Passed; zero errors/warnings |
| Frontend and client typing: TypeScript | Passed |
| Backend unit/HTTP/configuration tests | **20 passed** |
| Real PostgreSQL integration tests | **6 passed** |
| Frontend component tests | **3 passed** |
| Desktop/mobile Chromium journeys | **4 passed** |
| Production frontend build | Passed |
| OpenAPI and generated TypeScript regeneration | Passed; consecutive generated hashes are identical |
| Complete root command: `make check` | Passed |
| Python dependency audit | No known vulnerabilities; local editable project intentionally skipped |
| Production JavaScript dependency audit | No known vulnerabilities |
| Frontend peer dependencies | No reported conflicts |
| Repository documentation links | All local links resolved |
| Live API readiness against development PostgreSQL | `200 {"status":"ready"}` |
| Desktop/mobile visual inspection | Reviewed at 1440px desktop and Pixel 7 viewport; no clipping/overflow observed |

The database suite exercises identity uniqueness across issuers, foreign-key rejection, rollback, cascade deletion, migration downgrade/upgrade, schema drift, and actual API readiness. Browser tests exercise the real API plus failed-request recovery on desktop and mobile.

The GitHub Actions workflow is configured to run checks and dependency audits with frozen installs and no Auth0/AI secrets. The results above were executed locally. Current hosted runs are available in [GitHub Actions](https://github.com/felipefrmelo/lingora/actions). No production deployment was performed.

## Local usage

Follow [README](../README.md) for tool PATH setup and environment details. From the repository root:

```sh
make setup
make db-up migrate
make dev-api   # terminal 1
make dev-web   # terminal 2
```

Open `http://127.0.0.1:5173`. API docs are available at `http://127.0.0.1:8000/docs` in development. To rerun all checks, install Chromium once with `pnpm --filter @lingora/web exec playwright install chromium`, then run `make check` and `make audit`. Browser tests start their own servers, so stop development servers first.

## Security and limitations

- Auth0 tenant/application setup is documented in the [Auth0 guide](auth/auth0-setup.md). No tenant has been changed, no credentials are committed, and no real authentication flow is implemented or verified.
- MCP is a documented later integration; the [MCP guide](auth/mcp-oauth.md) records resource/audience isolation, CIMD, PKCE, metadata, scopes, and end-to-end acceptance requirements. No MCP server or ChatGPT linking is claimed operational.
- The backend currently exposes public operational endpoints only. Private resource authorization, JWKS validation, and student provisioning are mandatory Milestone 2 work.
- Telemetry uses allowlisted fields; custom spans omit query strings, bodies, headers, and raw URLs. OTLP export is optional and has not been tested against a live collector.
- Compose credentials are disposable local development values. Production hosting, rate limits, export/deletion/retention controls, educational workflows, and AI evaluations remain later milestones. See [security boundaries](../SECURITY.md).
- Source repository: [felipefrmelo/lingora](https://github.com/felipefrmelo/lingora). Temporary visual-review servers were stopped; the local PostgreSQL containers remain available.

## Next development task

Implement **Milestone 2 — Auth0 Authentication**: SDK-based Universal Login and Google login, trusted JWT/JWKS validation, transactional student identity resolution, protected endpoints/routes, scope and ownership tests, and real nonproduction login/logout/token-renewal verification. Follow the [roadmap](product/milestones.md) and do not mark authentication complete based only on mocked tokens.
