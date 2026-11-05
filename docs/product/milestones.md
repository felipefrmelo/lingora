# Technical milestones

| Milestone | Delivery and completion gate |
| --- | --- |
| 1. Foundation | Monorepo, public operational API, SPA, database/identity baseline, migrations, generated client, tests, CI, architecture/Auth0 docs. No authentication claim. |
| 2. Auth0 authentication | SPA SDK, Universal Login, Google, JWT/JWKS validation and rotation, internal student provisioning, protected routes/endpoints, scope/ownership tests, and real nonproduction login/logout/token-expiry verification. |
| 3. Student onboarding | Editable preferences, native language, goals, interests, manual CEFR and external test results. Preserve test-specific scores without unvalidated conversions. |
| 4. Content and lessons | License-aware metadata ingestion/deduplication, validated generated lessons/exercises, recorded attempts, provider telemetry, and deterministic evaluations. |
| 5. MCP and ChatGPT | Real Auth0 authorization, account linking, session preparation/recovery, preference changes, observations, idempotent confirmed completion, and Inspector/ChatGPT E2E tests. |
| 6. Adaptive learning | Evidence and confidence, interpretable recommendations, versioned plans, spaced repetition, and learning dashboard. |
| 7. Production readiness | Observability, rate limits, security/reliability review, export/deletion/retention, educational quality evaluation, pilot, and voice-session validation. |

Milestone 2 implementation and [development acceptance](../auth/verification.md) are complete as of 2026-11-05; the changes are published in [PR #1](https://github.com/felipefrmelo/lingora/pull/1) for review. Milestone 3 (student onboarding) is implemented with automated checks passing; its [real acceptance](../onboarding-verification.md) remains pending. Authentication is complete only after a real nonproduction Auth0 flow is verified; fixtures passing in CI are not sufficient. Likewise, MCP availability requires actual account linking and persisted session feedback. Closing voice is not pedagogical completion.
