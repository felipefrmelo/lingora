# Content and lessons

Milestone 4 adds a licensed news-brief catalog, private generated reading lessons, and persisted exercise attempts. MCP conversations, mastery estimates, adaptive plans, and spaced repetition remain later milestones.

## Running locally

Apply migration 0003 with `make migrate`. Run the API and web app as before, plus `make dev-worker` in a third terminal. `make ingest-content` refreshes the catalog immediately. The long-running worker also ingests on startup and every six hours; `worker --once` processes one eligible job without ingestion. These are operator commands, not public administrative endpoints.

The API and worker load root `.env`. `OPENAI_API_KEY` is server-only; never use a `VITE_` key. The default model is the pinned `gpt-5-mini-2025-08-07` snapshot, configurable through `LESSON_MODEL`. `LESSON_TIMEOUT_SECONDS` defaults to 120. An absent key leaves health, profiles, catalog browsing, and existing lessons available; new preparation returns 503. Ordinary CI uses fake providers and never needs live credentials. A configured key does not prove a worker is running: queued status remains explicit until a worker claims the request.

The development key was provisioned separately into the ignored `.env` through secure setup, with the user-selected 30-day expiration. It is not in the repository. Rotate it through the approved secure flow before expiration.

## Source and license boundary

Initial sources are the fixed GOV.UK Atom feeds for the UK Space Agency and Environment Agency. Only `/government/news/` links on the exact HTTPS `www.gov.uk` host enter the catalog. No learner-supplied feed or URL is fetched. Ingestion has a 15-second timeout, a one-megabyte decompressed limit, safe XML parsing, 30 entries per source, and no redirects. HTML becomes plain text; scripts, styles, images, attachments, and linked article pages are excluded. Briefs explicitly declaring incompatible or third-party copyright are skipped.

GOV.UK permits reuse through its feeds subject to its [content terms](https://www.gov.uk/help/terms-conditions) and [OGL v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). This implementation stores the brief, original URL, source, source date, license, attribution, topics, and fetch time. It does not assume rights over third-party images or article attachments. Add another source only after reviewing its rights and implementing the corresponding adapter. Recheck terms before production use.

Unique canonical URLs and normalized title/brief hashes prevent duplicates. Accepted brief snapshots are immutable; a feed edit does not silently change an existing lesson. Availability is checked with a bounded HEAD request to the allowlisted original host before paid generation. No redirects are followed. Confirmed 404/410 or a redirect hides the entry from new lessons; temporary network/server failures use bounded retries. Operators can hide a problematic entry with `uv run --project apps/api python -m lingora.learning_cli hide --content-id UUID`. Existing lessons retain their attributed snapshot for history.

The catalog shows up to the most recent 100 available briefs, filterable by topic. Matching saved interests to source topic labels ranks candidates first; date and UUID give stable ordering. The rationale is shown plainly. This supplies an initial activity suggestion after onboarding without claiming an adaptive learning plan. Original brief difficulty is explicitly **unrated**; the generated lesson uses a separate CEFR instructional target.

## Generation and privacy

Preparation chooses an explicit lesson-level override, otherwise the profile's self-selected CEFR, otherwise an explained A2 starting point. It never converts assessment scores or writes a new profile level. Goals and interests are snapshotted with the brief and target. Names, email addresses, external identity subjects, assessment scores, and tokens are excluded from the provider request. Custom preferences are learner-entered text, so learners should avoid personal information in them. The catalog explains what is sent to OpenAI.

The official OpenAI Python SDK calls the Responses API with strict structured JSON, `store=false`, no tools, a bounded output budget, and SDK retries disabled. Prompts and schemas are versioned. External briefs and preferences are untrusted data, never instructions. Trusted code prepends the exact source title/brief and an “Imagined practice” label; the model writes a fictional teaching scene inspired by the topic. Source facts and attribution are never reconstructed by the model. Raw structured output is validated, then assembled and revalidated through the final lesson contract before publication: all five exercise types, valid answer keys, a complete matching bijection, a single exact three-underscore gap, one-to-one matching definitions, short distinct accepted phrases, vocabulary in the reading, and verbatim supporting evidence for comprehension. Trusted assembly also shuffles matching definitions when the model supplies them in answer order. Rejected output is never displayed. These checks cannot establish factual accuracy, CEFR fit, or pedagogical quality by themselves; review the opt-in real output and expand evaluation cases before a pilot.

PostgreSQL is the durable queue. A worker claims with `FOR UPDATE SKIP LOCKED`, commits a four-minute lease and random lease token, then calls the provider outside a transaction. Publication rechecks the token under a row lock. An expired lease can be reclaimed; a late worker cannot overwrite the winner. The provider deadline is below the lease. Temporary failures retry after 30/60 seconds, up to three calls. Refusal or invalid output is terminal; learners can explicitly request a new preparation. A process crash can lead to another billable provider call after recovery; exactly-once publication does not imply exactly-once provider billing. Transactions atomically publish the lesson, job status, and telemetry. Worker command failures emit only a fixed operational event, so driver row diagnostics cannot leak private lesson or answer data; a persisted lease remains recoverable.

Two unfinished jobs per student limit accidental repeated preparation. Durable per-student `Idempotency-Key` UUIDs return the same job on retry; differing payload reuse returns 409. The current UI retains a key across uncertain retries in memory. After reload, use lesson history to recover an accepted job. Provider-wide budgets, abuse rate limits, queue monitoring, and production process supervision remain production-readiness work; configure provider project spending limits before exposure.

`generation_events` records provider/model, validation outcome, latency, token counts, and a cost estimate when the model has known pricing. Superseded live results retain usage telemetry. Unknown usage/cost remains null. GPT-5 mini estimates use an uncached-input pricing baseline of $0.25/M input and $2/M output tokens, verified on 2026-11-05 against the [model documentation](https://developers.openai.com/api/docs/models/gpt-5-mini); these are estimates, not invoices. No raw prompts, response bodies, or student answers are logged in these events. A crash before telemetry commit may leave usage unrecorded; provider billing is authoritative.

## Lessons and grading

Lessons are private immutable documents with source/prompt/schema snapshots. They contain objectives, original adapted reading, vocabulary, choice/gap/matching/comprehension/short-answer exercises, and conversation preparation. Answer keys, evidence, and explanations are excluded from lesson GET responses. React renders plain text rather than provider HTML.

Attempts are append-only and return feedback after successful persistence. Each exercise counts equally. Choice/gap/comprehension/short-answer accept one answer. Trusted assembly turns text exercises into precise quotation completions using the model’s short target phrase and exact supporting evidence, with an evidence-derived explanation. Unsupported targets are rejected. This avoids accepting only one of several valid answers to an ambiguous generated question. Matching compares definitions in term order. NFKC normalization, case folding, and collapsed whitespace are applied; spelling and punctuation otherwise count. This is deterministic exact matching, **not semantic grading**. Open discussion questions are ungraded. Learners can leave an answer blank to skip it. Feedback contains accepted answers, explanations, skill labels, original submitted answers, and a timestamp. Exercise results never alter CEFR or establish mastery.

Attempt creation uses a per-student durable UUID key and canonical payload hash including the lesson ID. Concurrent identical submissions produce one record; conflicting key reuse returns 409. A new attempt uses a new key. Reads and writes resolve the authenticated student and return 404 for another student's jobs, lessons, or attempts. Unknown owner fields/selectors are rejected. Existing `profile:read` and `profile:write` scopes are reused; no Auth0 configuration changes are needed.

Private Query keys include the subject. Logout/identity cleanup cancels requests and clears private queries and mutation variables/results; the account boundary unmounts prior forms. Unsaved answers remain in memory, warn on navigation/reload, and survive failed saves on the current page. They are never stored in browser persistence. Durable server jobs intentionally continue after logout.

## API

| Endpoint | Purpose |
| --- | --- |
| `GET /api/v1/me/content?topic=space&offset=0&limit=20` | Attributed available briefs and transparent initial recommendation |
| `POST /api/v1/me/lessons` | Queue `{content_id, cefr?}`; UUID `Idempotency-Key`, returns 202 job |
| `GET /api/v1/me/lessons` | Paginated own preparation/lesson history |
| `GET /api/v1/me/lesson-jobs/{job_id}` | Own queued/running/succeeded/failed status and lesson ID |
| `GET /api/v1/me/lessons/{lesson_id}` | Own lesson without answer keys |
| `POST /api/v1/me/lessons/{lesson_id}/attempts` | Persist `{answers: string[][]}` and deterministic feedback; UUID key |
| `GET /api/v1/me/lessons/{lesson_id}/attempts` | Paginated own saved attempts |

All list endpoints accept bounded offset/limit. Source lists are capped at 100 candidates. Problems use the existing format: 401 invalid credentials, 403 missing scopes, 404 missing/foreign resources, 409 key conflict, 422 invalid input, 429 two active jobs, 503 provider configuration/database unavailable. No public ingestion or arbitrary content-fetch endpoint exists.

## Verification

For an opt-in paid provider evaluation without student data, use `uv run --project apps/api python -m lingora.learning_cli evaluate --content-id UUID --level A2 --output /tmp/lingora-lesson-evaluation.json`. It uses the existing server-side key, verifies the source, validates output, and writes only public source/teaching material to the explicitly selected local file. Inspect factual framing, level fit, keys, and explanations; structured validation alone is insufficient.

Run `make lint typecheck test build`, `make test-integration`, `make test-e2e`, `make api-generate`, and `make audit`. The migration test upgrades a Milestone 3 profile/identity, round-trips 0003, and checks model drift. The deterministic corpus in `tests/learning_support.py` checks all exercise types and rejection cases; provider adapter tests use mocked HTTP, not live OpenAI. Worker tests cover duplicates, isolation, retry bounds, expired leases, late worker fencing, and publication rollback. See [actual Milestone 4 results](lessons-verification.md) for the live acceptance gate.
