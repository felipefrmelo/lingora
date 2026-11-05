# 0009 — AI integration boundary

Status: Accepted; implementation scheduled for Milestone 4. Date: 2026-11-04.

Context: Lesson generation must remain replaceable, testable, and subordinate to pedagogy, authorization, and database invariants.

Decision: Introduce provider contracts alongside real generation/evaluation use cases, not empty interfaces in foundation. Validate structured Pydantic outputs. Version prompts and schemas; record provider/model, usage, latency, cost estimates, and validation outcomes. Test with deterministic fakes and evaluation datasets.

Consequences: No AI credentials, model selection, or billable API calls are required now. External content and AI output remain untrusted. Do not store full conversations by default or turn one isolated error into an enduring competency assessment.
