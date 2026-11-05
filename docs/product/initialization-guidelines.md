# Project Initialization — AI English Learning Platform

## Role

You are a Staff Software Engineer, Software Architect, and AI Engineering Lead specializing in Python, FastAPI, React, TypeScript, Domain-Driven Design, OAuth 2.0, OpenID Connect, Auth0, MCP, PostgreSQL, automated testing, security, and agentic software engineering.

Your responsibility is to design and initialize a production-oriented English learning platform.

Optimize for correctness, maintainability, testability, security, developer experience, and incremental delivery.

Make reasonable engineering decisions autonomously and document important trade-offs.

Avoid speculative abstractions and unnecessary infrastructure.

Do not implement the entire product in one iteration.

---

# 1. Product Overview

Build an AI-powered English learning platform combining:

- Personalized English lessons.
- News and interest-based educational content.
- AI-generated exercises.
- Conversational practice through ChatGPT.
- CEFR-based competency tracking.
- Adaptive feedback.
- Pedagogical memory.
- Learning recommendations.
- Spaced repetition.
- MCP integration.

The application manages content, learning plans, exercises, student identity, and progress.

ChatGPT acts as a conversational tutor.

The backend remains the authoritative source of all persistent pedagogical data.

Read `docs/product/PRD.md` before implementing anything.

Treat the PRD as the product requirements source of truth.

Identify assumptions and technical decisions separately from product requirements.

---

# 2. Technology Stack

## Backend

- Python, using a stable supported version.
- uv for dependency and project management.
- FastAPI.
- Pydantic v2.
- pydantic-settings.
- SQLAlchemy 2.
- PostgreSQL.
- psycopg 3.
- Alembic.
- HTTPX.
- Pytest.
- Ruff.
- ty or Pyright.
- OpenTelemetry.

Use explicit typing throughout the application.

Prefer asynchronous I/O when beneficial.

Avoid mixing synchronous and asynchronous execution without clear transaction and concurrency boundaries.

## Frontend

- React with TypeScript.
- Vite.
- TanStack Router.
- TanStack Query.
- Tailwind CSS.
- shadcn/ui.
- React Hook Form.
- Zod.
- Vitest.
- React Testing Library.
- Playwright.

Build a Single Page Application initially.

Do not introduce SSR without a demonstrated requirement.

## Authentication

**Auth0 is the selected and mandatory identity and authorization platform.**

Use:

- Auth0 Universal Login.
- Auth0 React SDK.
- OAuth 2.0 Authorization Code Flow with PKCE.
- OpenID Connect.
- Auth0 API authorization.
- Auth0 Google social connection.
- Auth0-issued access tokens.
- Auth0 JWKS for signature verification.
- Auth0-supported OAuth authorization for MCP.

Do not evaluate alternative identity providers during initial implementation.

Do not create a custom authentication server.

## AI Integration

- Provider-agnostic LLM interfaces.
- Pydantic structured outputs.
- Versioned prompts and schemas.
- Evaluation and validation pipelines.

## MCP

- Official Python MCP SDK.
- Streamable HTTP transport.
- FastAPI/ASGI integration where appropriate.
- Auth0-backed OAuth authorization.
- Explicit tool schemas.

Verify current SDK and protocol compatibility before implementation.

## Infrastructure

- Docker.
- Docker Compose.
- GitHub Actions.
- PostgreSQL.
- Environment-based configuration.

Use a modular monolith.

Do not introduce Kubernetes, Kafka, or microservices prematurely.

---

# 3. Auth0 Architecture

Auth0 is responsible for authenticating users and issuing authorization tokens.

The platform is responsible for application-specific user data, domain permissions, and resource ownership.

Use one Auth0 tenant per environment where practical, with separate applications and APIs.

Document the expected tenant, applications, API identifiers, callback URLs, scopes, and configuration steps.

## 3.1 Auth0 Applications

Create and document the configuration for:

### English Learning Web

Application type:

Single Page Application.

Purpose:

Authenticate users accessing the React frontend.

Requirements:

- Authorization Code Flow with PKCE.
- Auth0 Universal Login.
- Google authentication.
- Login and logout.
- Session recovery.
- Token expiration handling.
- Secure redirect handling.
- No client secrets in the SPA.

Use the official `@auth0/auth0-react` SDK.

Avoid manually implementing the OAuth protocol in React.

### English Learning API

Create an Auth0 API resource server.

Use a stable HTTPS API identifier as the audience.

For example:

`https://api.english-learning.example`

Replace example domains with actual configured environments.

Define application-specific permissions such as:

- `profile:read`
- `profile:write`
- `lessons:read`
- `exercises:write`
- `sessions:read`
- `sessions:write`
- `progress:read`

Use least privilege.

Do not assume that Auth0 permission configuration automatically replaces domain-level ownership checks.

### ChatGPT MCP Client

Configure Auth0 to authorize ChatGPT as an OAuth client for the MCP resource.

Use current Auth0 MCP authorization capabilities and the supported ChatGPT client registration mechanism.

Investigate and configure the supported approach, such as Client ID Metadata Documents, Dynamic Client Registration, or a predefined OAuth client.

Do not assume that the SPA's Auth0 client ID should also be used as the MCP client.

Follow current official Auth0, MCP, and OpenAI authentication specifications.

---

# 4. React Authentication

Integrate Auth0 using `@auth0/auth0-react`.

Implement:

- Auth0Provider configuration.
- Login through Universal Login.
- Google social login.
- Logout.
- Authentication callback handling.
- Protected routes.
- User profile retrieval.
- Access token acquisition.
- Token expiration handling.
- Loading and error states.

Use environment variables such as:

```env
VITE_AUTH0_DOMAIN=
VITE_AUTH0_CLIENT_ID=
VITE_AUTH0_AUDIENCE=
VITE_AUTH0_REDIRECT_URI=
VITE_API_BASE_URL=
```

All `VITE_` variables must be treated as publicly visible build-time configuration.

Never place a client secret in the frontend.

Prefer the SDK's secure default token storage.

Avoid localStorage token persistence unless a documented threat-model decision justifies it.

Use the access token to call protected FastAPI endpoints.

Do not send ID tokens as API authorization credentials.

Frontend route guards are for user experience; authorization must be enforced by the backend.

---

# 5. FastAPI Authentication

FastAPI acts as an OAuth resource server.

Implement a reusable authentication dependency that validates Auth0 access tokens.

Verify:

- Signature using trusted Auth0 JWKS.
- Exact issuer.
- Expected audience.
- Expiration.
- Not-before time where applicable.
- Allowed signing algorithms.
- Required permissions or scopes.

Reject invalid or missing tokens.

Use correct HTTP 401 and 403 responses.

Do not trust unverified JWT payloads.

Cache JWKS safely and support key rotation.

Create a typed authenticated principal that application use cases can consume without depending directly on FastAPI request objects.

Example environment configuration:

```env
AUTH0_DOMAIN=
AUTH0_ISSUER=
AUTH0_API_AUDIENCE=
AUTH0_JWKS_URL=
```

Never hardcode tenant identifiers or production endpoints inside business logic.

## Internal Identity

Maintain a local Student entity.

Use an internal UUID as the primary student identifier.

Create a separate mapping between the internal student and external Auth0 identity.

Recommended relationship:

`Student -> ExternalIdentity(provider, issuer, subject)`

Use a unique constraint on the external identity tuple.

Do not use email as the primary identity key.

Do not assume email addresses are permanent or globally unique.

Resolve the internal student from the verified token identity.

Provision the local student record idempotently.

Never accept a client-submitted student ID as authorization to access private data.

---

# 6. Google Login with Auth0

Configure Google as a social identity provider through Auth0.

Use Auth0 Universal Login.

Do not implement Google OAuth directly inside the application.

Configure:

- Google connection.
- Allowed applications.
- Required scopes.
- Redirect/callback URLs.
- Logout URLs.
- Development and production domains.

Keep Google provider secrets inside Auth0 or an approved secret manager.

Avoid requiring a separate application-specific registration after successful authentication unless onboarding data is missing.

The first successful login should create or resolve the internal student identity.

Onboarding is a separate application workflow.

---

# 7. MCP Authentication with Auth0

The ChatGPT integration must authenticate the same underlying student identity as the web application.

Use Auth0 for authorization and identity.

The MCP server must expose OAuth protected resource metadata at the correct well-known endpoint.

For example:

`/.well-known/oauth-protected-resource`

The metadata must correctly identify:

- The canonical MCP protected resource.
- The Auth0 authorization server.
- Supported scopes.
- Relevant resource documentation.

Use the OAuth authorization flow supported by ChatGPT.

Requirements include:

- Authorization Code with PKCE S256.
- OAuth authorization server discovery.
- Supported client registration.
- Exact redirect URI configuration.
- Proper resource identifier handling.
- Access tokens issued for the intended protected resource.
- Scope validation.
- Token expiration and renewal behavior.
- Authentication challenges through WWW-Authenticate.
- Per-tool authentication metadata where required.

## Auth0 MCP-Specific Requirements

Investigate Auth0's current MCP authorization guidance.

Pay particular attention to the OAuth `resource` parameter and Auth0's Resource Parameter Compatibility Profile.

Configure the appropriate Auth0 API resource and audience behavior.

Do not assume the `audience` and `resource` parameters are interchangeable without verifying the configured Auth0 behavior.

Validate that tokens issued through the ChatGPT MCP flow contain the expected resource audience.

Use exact issuer matching.

Check Auth0's supported client registration mode, authorization metadata, PKCE support, and resource indicator handling.

Do not manually implement OAuth discovery endpoints beyond the responsibilities required of the MCP protected resource.

If Auth0 features or tenant settings are required, document the exact configuration and do not claim the integration works until an end-to-end authorization test succeeds.

## MCP Tool Security

Each MCP tool must:

1. Verify the authenticated principal.
2. Require appropriate scopes.
3. Resolve the internal Student identity.
4. Enforce domain-level authorization.
5. Execute an application use case.
6. Return validated results.

Never trust arbitrary student IDs supplied through MCP parameters.

Never expose data belonging to another student.

Use distinct access permissions for read and write operations when practical.

## OAuth Session Renewal

Verify compatibility with ChatGPT refresh-token requirements.

Configure offline access only when supported and justified.

Document token rotation, revocation, expiration, and reconnect behavior.

Use the MCP Inspector and an actual ChatGPT connection to validate the full authorization flow.

---

# 8. Modular Monolith Architecture

Organize the backend by business modules.

Suggested modules:

- identity
- onboarding
- placement
- competencies
- content
- lessons
- exercises
- learning_plans
- learning_sessions
- pedagogical_memory
- reviews

Keep domain logic independent from FastAPI and MCP.

HTTP routes and MCP tools are adapters to the same application use cases.

Use explicit transaction boundaries and dependency inversion at meaningful integration boundaries.

Avoid a global service layer containing unrelated business logic.

Do not introduce interfaces without practical value.

Keep module dependencies acyclic.

---

# 9. API Design

Expose versioned REST APIs under:

`/api/v1`

Use Pydantic input and output models.

Provide consistent HTTP error responses.

Support pagination where appropriate.

Validate all requests.

Use OpenAPI as the contract source for frontend client generation.

Generate TypeScript clients automatically rather than manually duplicating API types.

Implement authorization at every resource boundary.

Use idempotency keys for retry-sensitive write operations.

Use optimistic concurrency where relevant.

---

# 10. Learning Domain

Implement the PRD's educational domains incrementally.

## Student and Onboarding

- Profile.
- Native language.
- Learning objectives.
- Interests.
- Study preferences.
- Correction preferences.

## Placement Assessment

- External test results.
- CEFR estimates.
- Skill-specific scores.
- Assessment dates.
- Source metadata.

Do not equate different external test scores without validated conversion.

## Content

- News sources.
- Metadata ingestion.
- Deduplication.
- Categorization.
- License-aware storage.
- Content selection.

## Lessons

- Personalized lesson generation.
- Objectives.
- Vocabulary.
- Reading comprehension.
- Structured exercises.
- Lesson versioning.

## Learning Sessions

- READY.
- IN_PROGRESS.
- COMPLETED.
- ABANDONED.

Maintain explicit state transitions.

Session completion must be persisted and confirmed.

## Pedagogical Memory

Maintain:

- Observations.
- Evidence.
- Competency states.
- Confidence levels.
- Learning difficulties.
- Revision history.

Do not infer a persistent deficiency from one isolated mistake.

## Adaptive Learning

Begin with interpretable recommendation rules.

Do not introduce complex recommendation models before sufficient data exists.

---

# 11. AI Engineering

Keep the AI integration separate from domain rules.

Create provider interfaces for:

- Lesson generation.
- Exercise generation.
- Answer evaluation.
- Observation extraction.
- Feedback generation.
- Difficulty estimation.

Use structured, schema-validated outputs.

Track:

- Provider.
- Model.
- Prompt version.
- Schema version.
- Token usage.
- Latency.
- Cost estimates.
- Validation results.

Test AI workflows using deterministic fakes and evaluation datasets.

Treat external content as untrusted.

Protect against prompt injection.

Do not allow AI output to bypass authorization, database constraints, or business invariants.

Avoid storing complete student conversations unless explicitly needed and authorized.

---

# 12. Database Design

Use PostgreSQL, SQLAlchemy 2, and Alembic.

Design explicit entities and relationships.

Use:

- Primary keys.
- Foreign keys.
- Unique constraints.
- Transaction boundaries.
- Appropriate indexes.
- Audit timestamps.
- Version fields where required.

Student-owned educational data must be associated with the internal student ID.

Enforce ownership in backend application logic.

Consider database-level defense-in-depth when justified.

Identity mappings must support future identity-provider migration without rewriting the learning domain.

Do not implement event sourcing or full CQRS without demonstrated need.

---

# 13. Background Jobs

Potential asynchronous tasks include:

- News ingestion.
- Content classification.
- Lesson generation.
- AI evaluations.
- Scheduled reviews.

Distinguish lightweight asynchronous operations from durable background processing.

Do not use FastAPI BackgroundTasks for important jobs that must survive process restarts.

Introduce a durable queue when required.

Jobs must be observable, retryable, and idempotent where appropriate.

Start with the simplest reliable execution architecture.

---

# 14. Frontend Structure

Organize React by features.

Suggested directories:

- app
- routes
- features
- components
- lib
- test

Use TanStack Router for typed routing.

Use TanStack Query for server state.

Use React Hook Form and Zod for forms.

Use Tailwind and shadcn/ui for accessible components.

Avoid duplicating server state in a global store.

Prioritize a responsive UI with clear loading, empty, and error states.

Create a consistent student-facing experience for:

- Onboarding.
- News catalog.
- Lessons.
- Exercises.
- Learning plans.
- Dashboard.
- ChatGPT connection status.

Do not assume SSR is required for the authenticated application.

---

# 15. Testing Strategy

Use pytest for backend testing.

Implement:

- Domain unit tests.
- Application tests with fakes.
- PostgreSQL integration tests.
- HTTP contract tests.
- Auth0 JWT validation tests.
- Authorization tests.
- MCP contract tests.
- MCP OAuth integration tests.
- Concurrency and idempotency tests.

For authentication, cover:

- Valid access token.
- Invalid signature.
- Expired token.
- Incorrect issuer.
- Incorrect audience.
- Missing scope.
- Cross-student access.
- JWKS key rotation.
- Invalid or missing MCP resource audience.
- Unauthenticated MCP requests.
- Invalid session ownership.

Use controlled JWT fixtures and local test keys.

Do not require production Auth0 credentials for the normal CI test suite.

Use a separate opt-in integration test suite for real Auth0 authentication flows.

For the frontend, use Vitest, React Testing Library, and Playwright.

Test important authentication and onboarding journeys.

Never claim a test passed unless it was executed.

---

# 16. Security and Privacy

Follow secure-by-design principles.

Requirements:

- Auth0-based identity.
- Explicit backend authorization.
- Least privilege.
- Input validation.
- Safe CORS configuration.
- Secure token handling.
- IDOR protection.
- Rate limiting.
- Prompt injection protection.
- Secret management.
- Structured audit logs.
- Privacy-aware telemetry.
- LGPD-aligned data minimization.
- Data export and deletion design.

Separate authentication logs from pedagogical records.

Avoid sensitive student information in application logs.

Do not store raw access tokens.

Do not commit real credentials.

Use environment-specific Auth0 tenants/applications or equivalent isolation.

---

# 17. Repository Structure

Create a monorepo.

Suggested structure:

```text
english-learning/
├── AGENTS.md
├── README.md
├── .env.example
├── compose.yaml
│
├── apps/
│   ├── web/
│   │   ├── src/
│   │   │   ├── app/
│   │   │   ├── auth/
│   │   │   ├── routes/
│   │   │   ├── features/
│   │   │   ├── components/
│   │   │   └── lib/
│   │   └── package.json
│   │
│   └── api/
│       ├── pyproject.toml
│       ├── uv.lock
│       ├── src/english_learning/
│       │   ├── main.py
│       │   ├── core/
│       │   ├── modules/
│       │   ├── integrations/
│       │   │   ├── auth0/
│       │   │   ├── mcp/
│       │   │   └── ai/
│       │   └── infrastructure/
│       ├── migrations/
│       └── tests/
│
├── packages/
│   └── api-client/
│
├── docs/
│   ├── product/
│   │   └── PRD.md
│   ├── architecture/
│   ├── auth/
│   │   ├── auth0-setup.md
│   │   └── mcp-oauth.md
│   └── adr/
│
├── .agents/
│   └── skills/
│
├── infra/
│   └── docker/
│
└── .github/
    └── workflows/
```

Adapt the structure if a simpler design is more maintainable.

Avoid empty placeholder modules.

---

# 18. Agentic Engineering

Prepare the repository for human developers and AI coding agents.

Create an AGENTS.md with:

- Project overview.
- Architecture rules.
- Development commands.
- Testing commands.
- Lint and type-check commands.
- Security constraints.
- Auth0 integration guidance.
- MCP implementation guidance.
- Definition of Done.
- Documentation links.

Keep AGENTS.md concise.

Create reusable skills only for meaningful recurring tasks.

Examples:

- implement-feature
- add-fastapi-endpoint
- create-migration
- add-mcp-tool
- integrate-ai-provider
- review-security
- debug-auth0-oauth

Use ADRs for important technical decisions.

At minimum, document:

1. Modular monolith architecture.
2. FastAPI and uv.
3. React SPA and Vite.
4. Auth0 as the identity provider.
5. Auth0 authentication for React.
6. Auth0 authorization for MCP.
7. PostgreSQL persistence.
8. Background processing strategy.
9. AI provider abstraction.

---

# 19. CI/CD and Developer Experience

Create GitHub Actions for:

- Backend tests.
- Backend lint.
- Backend type checks.
- Frontend tests.
- Frontend lint.
- Frontend type checks.
- Frontend build.
- Migration validation.
- Dependency security checks where practical.

Use pinned or locked dependencies.

Use uv.lock and pnpm-lock.yaml.

Do not require live Auth0 credentials for ordinary PR validation.

Provide:

- Docker Compose for PostgreSQL.
- Local backend commands using uv.
- Local frontend commands using pnpm.
- Environment configuration examples.
- Health checks.
- Database migration commands.
- Auth0 tenant setup documentation.

Do not automatically deploy to production.

---

# 20. Implementation Plan

Implement the product incrementally.

## Milestone 1 — Foundation

Deliver:

- Monorepo.
- FastAPI application.
- React SPA.
- PostgreSQL integration.
- Alembic migrations.
- Basic frontend-to-backend communication.
- Tests.
- Lint.
- Type checking.
- GitHub Actions.
- AGENTS.md.
- ADRs.
- Auth0 architecture documentation.

The application must start locally without requiring authentication for its public health check.

Design authentication boundaries but do not hardcode authentication bypasses.

## Milestone 2 — Auth0 Authentication

Deliver:

- Auth0 tenant configuration documentation.
- Auth0 SPA application.
- Auth0 API resource.
- React Auth0 SDK integration.
- Universal Login.
- Google login.
- Protected frontend routes.
- FastAPI JWT validation.
- Internal Student mapping.
- Protected REST endpoints.
- Authorization tests.
- Logout and token expiration handling.

Do not consider this milestone complete without real authentication verification in a nonproduction environment.

## Milestone 3 — Student Onboarding

Deliver:

- Profile.
- Goals.
- Interests.
- Level selection.
- Assessment registration.
- Preferences.

## Milestone 4 — Content and Lessons

Deliver:

- News catalog.
- Content ingestion.
- Structured lesson generation.
- Exercise generation.
- Exercise attempts.

## Milestone 5 — MCP and ChatGPT

Deliver:

- Auth0 MCP authorization.
- OAuth metadata.
- Protected MCP tools.
- ChatGPT account linking.
- Session preparation.
- Session recovery.
- Session feedback.
- Idempotent completion.
- End-to-end authentication tests.

## Milestone 6 — Adaptive Learning

Deliver:

- Pedagogical memory.
- Competency evidence.
- Recommendations.
- Spaced repetition.
- Learning dashboard.

## Milestone 7 — Production Readiness

Deliver:

- Security review.
- E2E tests.
- Observability.
- AI quality evaluations.
- Reliability testing.
- Privacy controls.
- Voice integration validation.

---

# 21. Execution Instructions

Start by inspecting the repository and reading the PRD.

Verify the chosen stack and its currently supported versions.

Produce an architecture proposal covering:

1. Monorepo organization.
2. FastAPI module boundaries.
3. React architecture.
4. Auth0 authentication flow.
5. Auth0 tenant and application configuration.
6. Internal student identity mapping.
7. API token validation.
8. MCP OAuth authorization.
9. Database design.
10. Testing architecture.
11. Security boundaries.
12. Local development workflow.

Document the major decisions using ADRs.

Then implement Milestone 1.

Do not implement all product requirements.

Do not create a custom OAuth server.

Do not replace Auth0 with another identity provider.

Do not introduce unnecessary abstractions.

Do not commit real Auth0 credentials.

Do not claim authentication works before validating a real end-to-end flow.

## Final Report

Provide:

- Architecture overview.
- Files created or modified.
- Important ADRs.
- Auth0 setup instructions.
- Commands to run locally.
- Tests executed and their results.
- Security considerations.
- Known limitations.
- Next recommended development task.

The objective is to establish a reliable, production-oriented foundation that supports continuous development by AI coding agents and human engineers.