# Milestone 4 verification

Date: 2026-11-05. Status: implementation under verification; real acceptance is not yet complete.

Completed so far:

- 119 backend unit/configuration/HTTP/adapter tests passed.
- 29 PostgreSQL integration tests passed, including Milestone 3 migration preservation and a 0003 downgrade/upgrade round trip, queue/attempt idempotency, cross-student 404s, worker recovery, stale worker fencing, and atomic publication rollback.
- 38 frontend tests passed, including lesson loading, creation/submission retry keys, preserved unsaved answers, account switching, and expired credentials.
- Backend lint/format, strict Pyright, frontend lint/TypeScript, and production build passed.
- Python and production JavaScript dependency audits found no known vulnerabilities.
- Live selected-feed ingestion inserted 35 available attributed briefs; a subsequent refresh inserted zero duplicates.

- Six desktop/mobile Playwright checks passed, covering anonymous protection of the new pages/endpoints and existing health/recovery behavior.
- Repeated OpenAPI/TypeScript generation produced identical hashes.
- A paid OpenAI adapter evaluation succeeded. Human review of the early result caught unsupported news elaboration and brittle answer formatting. The final design assembles the exact brief in trusted code, labels generated practice as fictional, and rejects long/duplicate text keys and malformed gaps, and shuffles matching definitions in trusted code. A stricter intermediate evaluation was correctly rejected and never published.

Pending: live real-account generation/exercises/recovery/privacy, final documentation review, and a published reviewable PR. No merge or deployment has been performed.

The existing main JavaScript bundle warning remains around 704 KB minified. Lesson/catalog/job pages are separate chunks. No production performance or educational-quality guarantee is inferred from these checks.
