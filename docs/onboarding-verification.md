# Milestone 3 verification

Date: 2026-11-05. Branch: `codex/student-onboarding`, based on merged Milestone 2 (PR #1).

**Status: Milestone 3 implementation and real development acceptance complete on 2026-11-05.** Published in [PR #2](https://github.com/felipefrmelo/lingora/pull/2) for review.

## Automated checks executed

- 80 backend unit/configuration/HTTP tests, including sanitized retryable database-outage responses.
- 20 PostgreSQL integration tests, including default reads without writes, state transitions, empty completion, skipped-profile edits, stale/concurrent writes, row constraints/rollback, idempotent concurrent creation without orphan records, assessment CRUD, deleted-receipt replay, raw scores, and cross-student isolation.
- Migration upgrade from 0001 preserves an existing student/external mapping; head-to-base-to-head round trip and Alembic model-drift check passed.
- 31 frontend tests covering first-visit routing, custom choices, draft/skip/resume behavior, empty completion, failed saves/retry, conflicts/reload, dirty navigation and assessment drafts, CRUD, original scores, account switching, query cleanup, and pending-request cancellation, including Strict Mode replay and SDK identity changes.
- 8 Auth0 Action regression tests.
- 6 desktop/mobile Playwright checks against the real API; all private routes and new resource endpoints reject anonymous access.
- Ruff lint/format, strict Pyright, ESLint, TypeScript, production build, and both dependency audits passed. No known dependency vulnerabilities were reported.
- [GitHub CI run 6](https://github.com/felipefrmelo/lingora/actions/runs/42034205761) passed verification and dependency-audit jobs for the initial implementation.
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
| A second Auth0 account cannot see the first account's profile or assessments | Passed: the user signed in with the separate password account. Setup fields/chips were empty; skipping showed an empty own overview and no assessments. Database readback confirmed two original identities, two separate profiles, and the sole test assessment owned only by the Google student. The first profile remained completed with its selected B1 and saved 20-minute duration. |
| Review real desktop form/error behavior | Desktop forms and overview inspected in Safari; keyboard/segmented date control worked. Live input-error check passed: 3 minutes remained visible with “Choose 5 to 120 minutes”; cancelling required discard confirmation and preserved the saved 20-minute value. |

The real journey above passed with the existing Google and dedicated password identities. The user entered the password directly; no credentials were handled or recorded. Both sessions were signed out after acceptance. Only clearly labeled development profile/assessment values were created; the assessment is not evidence of a real examination. Automated CI does not contact the live tenant. No merge or production deployment was performed.
