# 0009 — AI integration boundary

Status: Accepted; implemented in Milestone 4; see [ADR 0011](0011-content-lessons-and-worker.md). Date: 2026-11-04.

Context: Lesson generation must remain replaceable, testable, and subordinate to pedagogy, authorization, and database invariants.

Decision: Introduce provider contracts alongside real generation/evaluation use cases, not empty interfaces in foundation. Validate structured Pydantic outputs. Version prompts and schemas; record provider/model, usage, latency, cost estimates, and validation outcomes. Test with deterministic fakes and evaluation datasets.

Consequences: AI credentials are server-only; ordinary CI uses deterministic providers. External content and AI output remain untrusted. Do not store full conversations by default or turn one isolated error into an enduring competency assessment.
