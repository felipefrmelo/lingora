# 0011 — Licensed briefs, validated lessons, and durable generation

Status: Accepted. Date: 2026-11-05.

Context: Milestone 4 needs reliable generation from selected news sources, independently testable grading, privacy, licensing provenance, and persistent exercise history.

Decision: Start with selected GOV.UK Atom text briefs under OGL-3.0, exact-host link validation, bounded requests, canonical/hash deduplication, and visible attribution. Do not ingest images or arbitrary linked pages. Keep original source difficulty unrated; target lessons at explicit/profile CEFR or a disclosed A2 default. Use topic-interest matching for the initial activity recommendation.

Introduce the `learning` business module and a narrow lesson-provider protocol. The OpenAI adapter uses the official SDK and strict structured Responses, versioned prompts/schema, bounded calls, and `store=false`. Deterministic validators gate publication; they do not claim full factual or pedagogical verification. Grade five exercise types through accepted exact answers; open discussion remains ungraded. Persist immutable private lesson documents and append-only idempotent attempts without changing proficiency estimates.

Use PostgreSQL as the first durable job mechanism rather than add a separate queue service. Claim with skip-locked row locks, four-minute leases, fencing tokens, and three bounded attempts. Call the provider outside transactions. Commit publication/status/telemetry atomically; stale results retain operational usage but cannot publish. Job creation and attempt submission serialize on the owning student and use durable request keys. Provider calls are at-least-once during crash recovery; billing may repeat even though lesson publication does not.

Consequences: A separate worker process is required. It refreshes selected feeds every six hours while running. Ordinary CI uses fake providers and test-only Auth0 mocks. Existing profile scopes authorize self-owned learning operations without tenant edits. Telemetry excludes prompt/response bodies. Stronger source review workflows, production budgets/rate limits/process supervision, semantic grading, mastery estimates, MCP conversations, and adaptive plans are deferred to their respective milestones. See [the implementation guide](../lessons.md) for contracts and limitations.
