# Student onboarding

Milestone 3 adds skippable setup, an editable learning profile, and self-reported assessment history. See [verification](onboarding-verification.md) for current acceptance status. Onboarding ends with a profile overview. Milestone 4 now adds an attributed news catalog and an initial activity suggestion at the chosen lesson level; see [content and lessons](lessons.md). Competency estimates and MCP remain later milestones. The historical Milestone 3 report records RF-02 as deferred at that delivery boundary.

## Learner flow

After verified Auth0 sign-in and the existing student bootstrap, `/app` reads the learning profile. A missing profile returns defaults without inserting a row. `not_started` and `in_progress` lead to `/app/onboarding`; `skipped` and `completed` show the overview. `/app/profile` edits preferences. Completed learners visiting the wizard return to the overview.

The three steps are About you, Your English, and Your routine. Every learning field is optional. Save and continue persists a draft before moving on. Skip keeps previously saved values and confirms before discarding current input. Back also warns before discarding unsaved current-step input, including an unfinished assessment. Refresh or sign-in later loads saved values; resumed setup starts at its first step. Drafts are not written to local/session storage.

Profile fields: optional preferred name and native-language text (80 characters each), up to 10 goals and 10 interests (100 characters each), selected CEFR A1–C2 or unknown, 1–7 sessions per week or unset, 5–120 minutes per session or unset, and free/balanced/intensive corrections (balanced default). Suggested chips and custom entries use the same bounded text representation. Auth0 name/email are not edited; preferred name is a Lingora display value with SDK-name fallback.

Onboarding intent is explicit: `save` preserves an existing state or starts `in_progress`; `resume` sets an unfinished profile to `in_progress`; `skip` sets `skipped`; `finish` sets `completed` with a server timestamp. Completion is preserved during later edits and repeated finishes retain the first completion timestamp. Editing a skipped profile does not force setup again. Successful server responses determine displayed progress; failed writes retain input.

## REST contract

All routes require verified email and resolve the student from the existing Auth0 issuer/subject mapping. They accept no student identifier. An authenticated but unbootstrapped student receives 404. Existing `/me` and `/me/bootstrap` responses are unchanged.

| Route | Scope | Behavior |
| --- | --- | --- |
| `GET /api/v1/me/profile` | `profile:read` | Current profile; version 0 and `not_started` defaults when absent, without writes. |
| `PUT /api/v1/me/profile` | `profile:write` | Full profile values, `expected_version`, and intent; returns saved profile/version. |
| `GET /api/v1/me/assessments` | `profile:read` | Own history, newest assessment date first; limit 20 by default (maximum 100), offset 0. Returns items and total. |
| `POST /api/v1/me/assessments` | `profile:write` | Create with required UUID `Idempotency-Key`; 201 new, 200 replay. |
| `PUT /api/v1/me/assessments/{assessment_id}` | `profile:write` | Replace own assessment with `expected_version`. |
| `DELETE /api/v1/me/assessments/{assessment_id}?expected_version=…` | `profile:write` | Version-checked delete; 204 on success. |

Unknown body/query fields are rejected. Known database failures produce sanitized, retryable 503 problem details; SQL parameter values are hidden from engine diagnostics. Stale versions or conflicting creation-key reuse return 409 problem details. Another student's assessment returns 404. Profile writes and assessment edits/deletes check versions while holding a database row lock inside an explicit transaction. Concurrent first profile inserts have one winner. No session dependency commits implicitly.

Assessment creation receipts have a unique `(student_id, key)` and SHA-256 fingerprint of the validated original creation payload. A concurrent losing transaction rolls back both assessment and receipt, then resolves the winner. Replaying the same payload returns the existing assessment, including any subsequent edits. A changed payload with the same key returns 409. Receipts survive deletion with a null assessment reference: replay returns 410, never recreating deleted evidence. Keep the same key when retrying an uncertain creation; review records before deliberately starting another entry.

## Assessment integrity

Record provider (`englishscore`, `ef_set`, `other`), test name, optional variant, assessment date, original overall/component values and scale labels, and optional CEFR explicitly reported by the provider. Test name/date and at least one result are required; future dates and duplicate component labels are rejected. Up to 20 components can be recorded.

Scores remain strings, preserving leading zeroes, ranges, and original formatting. Test variants distinguish, for example, receptive-only and four-skill results. Records are labeled self-reported. No provider verification, certificate upload, remote URL fetch, cross-test conversion, averaging, missing-skill inference, or automatic selected-level change occurs. Learners change selected CEFR explicitly in their profile.

Optional resources: [EnglishScore](https://www.britishcouncil.org/english/learn-online/englishscore) and [EF SET](https://www.efset.org/). Taking a test or buying a certificate is not required for Lingora setup.

## Persistence and browser privacy

Alembic revision `0002` adds `student_profiles`, `placement_assessments`, and durable `assessment_creations` receipts. Existing student and external-identity rows remain unchanged; no profiles are backfilled. Register domain models with Alembic metadata and apply `make migrate` explicitly before using the new endpoints. Downgrading 0002 removes onboarding/assessment data but preserves identity tables.

Profile and assessment queries share the `['private', subject, …]` namespace with account data. Logout/identity changes cancel pending private requests and purge previous-account queries; keyed authenticated content unmounts old forms. Access tokens remain in SDK memory. Save errors keep input, 409 offers explicit reload, and expired credentials request interactive sign-in. Private form values are not sent to logs or persisted in browser storage. Ordinary CI uses test-only mocks/local signing keys and has no runtime auth bypass.
