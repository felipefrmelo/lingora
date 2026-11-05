# Milestone 4 verification

Date: 2026-11-05. Status: development implementation and real acceptance passed. Published in [PR #3](https://github.com/felipefrmelo/lingora/pull/3); no automatic merge or deployment.

## Automated checks

| Check | Actual result |
| --- | --- |
| Backend unit/configuration/HTTP/provider tests | 122 passed |
| PostgreSQL integration tests | 29 passed |
| Frontend tests | 38 passed |
| Auth0 Action regression tests | 8 passed |
| Desktop/mobile Playwright checks | 6 passed |
| Total | **203 tests passed** |
| Ruff lint/format, strict Pyright, ESLint, TypeScript | Passed |
| Production build | Passed; existing main chunk warning around 704 KB remains |
| Python and production JavaScript dependency audits | No known vulnerabilities found |
| Migration 0003 upgrade/downgrade and Milestone 3 preservation | Passed; existing identity/profile survives |
| Alembic metadata drift | Passed |
| Repeated generated OpenAPI/TypeScript contracts | Identical hashes; CI contract drift check passed |

The [code CI run 42088795836](https://github.com/felipefrmelo/lingora/actions/runs/42088795836) passed both `verify` and `dependency-audit` on commit `5793a4f1508005f5e9db660c0ecaaf4a8f7bc3d7`. Final acceptance-documentation/public-copy changes trigger another full PR check; inspect the latest PR status before merging.

Tests cover source-host allowlisting, redirects, bounded feed parsing and XML entity rejection, duplicate ingestion, invalid generated shapes/keys/evidence, all five grading types, endpoint scopes, self-owned resources, conflicting retry keys, concurrent writes, bounded retries, lease recovery, late worker fencing, publication rollback, and private worker-error diagnostics. A fresh-process regression covers standalone worker model initialization. Frontend tests cover routing, safe retries, failure retention, unsaved changes, account switching, expired credentials, and query/request/form/mutation cleanup. Ordinary CI uses test-only Auth0 and provider mocks; no runtime bypass exists.

## Live source and provider checks

The selected GOV.UK feeds imported 35 attributed briefs; repeat refreshes inserted zero duplicates. The final public-only OpenAI evaluation passed with 1,035 input and 1,110 output tokens. Manual review checked attribution, fictional framing, precise text prompts, answer keys, and supported explanations. This is a development sample, not a broad educational benchmark.

Review of early generated output caught unsupported news elaboration and ambiguous exact-match questions. Trusted code now prepends the exact source brief, labels imagined practice, shuffles matching definitions when necessary, and constructs text prompts/feedback from quoted evidence. Unsupported targets fail validation. Intermediate evaluations and two early real-account jobs were rejected without publishing partial lessons. The successful journey used prompt `lesson-v2` and schema `1`.

## Real Auth0 journey

Existing Lingora Auth0 applications, API audience, scopes, verification policy, and identity mappings were retained. No tenant configuration changes were made.

| Journey | Observed result |
| --- | --- |
| Initial activity from a skipped profile with unknown level | Profile overview led to attributed catalog; A2 fallback was explained, with an explicit lesson-level choice |
| Prepare selected space-news brief | Queued/running status led to a persisted private lesson with objectives, reading, vocabulary, five exercise types, and conversation starters |
| First exercise submission | All matching definitions and the other supplied answers were accepted; leaving comprehension blank produced saved **4/5** feedback |
| Case/whitespace handling | The original `  DEBRIS  ` response was retained and graded correctly against `debris` |
| Second exercise submission | Completing the missing phrase produced saved **5/5** feedback; the earlier attempt remained in history |
| Unsaved input | Cancel kept a changed draft; confirming discard removed only unsaved input; reopening retained both persisted attempts |
| Sign-out | Private lesson/profile content cleared and the public page returned |
| Sign back in and reload with the password account | User confirmed both saved attempts remained after reloading and completing any required interactive authentication |
| Switch to the Google account | Agent observed an empty own lesson history and its unchanged original B1 profile and assessment; the password account's lesson did not appear |
| Final sign-out | Agent observed the public page with sign-in controls |

Safari session recovery can require interactive consent because tokens are memory-only and browser privacy settings prevent silent recovery. The development API token lifetime remains five minutes. Expired sessions requested sign-in; credentials and browser privacy protections were not weakened for testing.

Read-only PostgreSQL verification confirmed **2 students, 2 external identities, 2 profiles, 1 assessment, 35 content records, 1 lesson, and 2 exercise attempts**. Both attempts belong to that lesson's owner; the other account has no lessons. The owning profile remains skipped with no selected CEFR, and original answer whitespace remains stored. No account identifiers, credentials, or bearer tokens are included in this report.

Generation events retained two rejected calls and the successful call. The successful persisted lesson recorded 1,035 input and 1,015 output tokens, a validation outcome, and an estimated 2,289 micro-USD using the documented pricing baseline. These are operational estimates, not billing records.

## Delivery boundary

MCP conversations/account linking, adaptive plans, mastery estimates, spaced repetition, a full source-review admin workflow, production rate limits/budgets/supervision, and pilot-scale educational evaluation remain later work. Original news-brief difficulty stays unrated. CEFR is an instructional target; practice results do not change it or prove proficiency. The existing main-bundle warning remains; lesson/catalog/job pages use separate chunks. Development test lessons and attempts remain in the local database; no production deployment occurred.
