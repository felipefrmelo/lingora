# Milestone 4 verification

Date: 2026-11-05. Status: implementation under verification; real acceptance is not yet complete.

Completed so far:

- 122 backend unit/configuration/HTTP/adapter tests passed.
- 29 PostgreSQL integration tests passed, including Milestone 3 migration preservation and a 0003 downgrade/upgrade round trip, queue/attempt idempotency, cross-student 404s, worker recovery, stale worker fencing, and atomic publication rollback.
- 38 frontend tests passed, including mutation-variable/result cleanup on logout/account changes, including lesson loading, creation/submission retry keys, preserved unsaved answers, account switching, and expired credentials.
- Backend lint/format, strict Pyright, frontend lint/TypeScript, and production build passed.
- Python and production JavaScript dependency audits found no known vulnerabilities.
- Live selected-feed ingestion inserted 35 available attributed briefs; a subsequent refresh inserted zero duplicates.

- Six desktop/mobile Playwright checks passed, covering anonymous protection of the new pages/endpoints and existing health/recovery behavior.
- Repeated OpenAPI/TypeScript generation produced identical hashes.
- A paid OpenAI adapter evaluation succeeded. Human review of the early result caught unsupported news elaboration and brittle answer formatting. The final design assembles the exact brief in trusted code, labels generated practice as fictional, and rejects long/duplicate text keys and malformed gaps, shuffles matching definitions in trusted code, and derives precise text prompts/feedback from exact quoted evidence (prompt lesson-v2). Intermediate evaluations and two early real-account preparations were correctly rejected and never published. The final lesson-v2 public-only evaluation passed, using 1,035 input and 1,110 output tokens; manual review confirmed precise answerable text prompts, factual brief attribution, fictional framing, and supported explanations. This is one development sample, not a broad educational benchmark. A fresh-process worker metadata issue found during that journey was corrected and regression-tested.

PR [#3](https://github.com/felipefrmelo/lingora/pull/3) is published as a draft. Pending: successful final real-account generation/exercises/recovery/privacy and final acceptance documentation. The initial CI run is [42086919995](https://github.com/felipefrmelo/lingora/actions/runs/42086919995); confirm its final status and the latest commit before treating CI as complete. No merge or deployment has been performed.

The existing main JavaScript bundle warning remains around 704 KB minified. Lesson/catalog/job pages are separate chunks. No production performance or educational-quality guarantee is inferred from these checks.
