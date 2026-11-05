# Milestone 3 verification

Date: 2026-11-05. Branch: `codex/student-onboarding`, based on merged Milestone 2 (PR #1).

**Status: implementation and automated checks passed; real onboarding acceptance pending.**

## Automated checks executed

- 79 backend unit/configuration/HTTP tests.
- 20 PostgreSQL integration tests, including default reads without writes, state transitions, empty completion, skipped-profile edits, stale/concurrent writes, row constraints/rollback, idempotent concurrent creation without orphan records, assessment CRUD, deleted-receipt replay, raw scores, and cross-student isolation.
- Migration upgrade from 0001 preserves an existing student/external mapping; head-to-base-to-head round trip and Alembic model-drift check passed.
- 31 frontend tests covering first-visit routing, custom choices, draft/skip/resume behavior, empty completion, failed saves/retry, conflicts/reload, dirty navigation and assessment drafts, CRUD, original scores, account switching, query cleanup, and pending-request cancellation, including Strict Mode replay and SDK identity changes.
- 8 Auth0 Action regression tests.
- 6 desktop/mobile Playwright checks against the real API; all private routes and new resource endpoints reject anonymous access.
- Ruff lint/format, strict Pyright, ESLint, TypeScript, production build, and both dependency audits passed. No known dependency vulnerabilities were reported.
- Private feature chunks are lazy-loaded. The existing main bundle warning remains (702 KB minified); no production performance claim.
- OpenAPI/TypeScript regenerated; repeat generation produced identical SHA-256 hashes; no generated-contract drift.

## Real Auth0 acceptance

Use the existing dedicated development SPA/API, with no additional Auth0 scopes/configuration. Use only explicitly marked development profile/assessment values. Never record passwords, tokens, authorization codes, verification/reset links, or personal assessment evidence in this report.

| Journey | Result |
| --- | --- |
| Existing verified student reaches setup without a new identity | Passed via real Google/Auth0 sign-in: two original student/identity rows preserved; the existing Google student received the new setup. |
| Save first-step draft, reload/sign in, and recover saved values | Passed: preferred-name/native-language values, selected chips, and a pending custom goal survived reload and Safari interactive sign-in. |
| Skip setup and resume saved choices | Passed: skip displayed the overview with saved choices; Resume restored the fields and continued setup. |
| Finish setup and see saved profile overview | Passed: selected B1, 3 sessions/week, 15 minutes, and balanced mode were saved with Setup complete. |
| Edit preferences and reload; SDK identity remains unchanged | Edits passed: preferred name, duration (20 minutes), and free correction mode saved while SDK email/identity stayed unchanged. Post-edit sign-in restored the edited name, duration, free mode, selected level, and assessment. |
| Register a clearly marked self-reported assessment; original scores persist and selected level stays unchanged | Passed: Development acceptance test / Manual entry — not an actual exam retained overall `005.50` on `0–10` and Reading `125–135` on Original range. Test-reported C1 left selected B1 unchanged. |
| Sign out/in and recover the same profile/student | Passed with the Google identity: completed setup and exact test-score strings survived sign-out/in; student count stayed at two. |
| A second Auth0 account cannot see the first account's profile or assessments | Pending |
| Review real desktop form/error behavior | Desktop forms and overview inspected in Safari; keyboard/segmented date control worked. Live input-error check passed: 3 minutes remained visible with “Choose 5 to 120 minutes”; cancelling required discard confirmation and preserved the saved 20-minute value. |

Milestone 3 remains incomplete until the real journey above succeeds and is documented. Automated CI does not contact the live tenant. No merge or production deployment is authorized by this report.
