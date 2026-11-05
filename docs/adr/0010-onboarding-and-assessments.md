# 0010 — Optional onboarding and original assessment evidence

Status: Accepted; implemented in Milestone 3, with live acceptance tracked separately. Date: 2026-11-05.

Decision: Keep the existing authenticated Student mapping authoritative. Add a one-to-one learning profile and student-owned self-reported assessments. All profile fields are optional, setup can be skipped, and explicit server-confirmed intent controls onboarding state. Editing a skipped profile preserves that state; resuming guided setup is explicit. Completion is preserved during later edits.

The learner's selected CEFR changes only through profile edits. External results retain provider/test variant, assessment date, original string scores/scales, tested components, and any explicitly reported CEFR. They do not imply verified scores, equivalent tests, missing skills, or demonstrated mastery. Lessons and initial practice suggestions are deferred to Milestone 4.

Use explicit transactions, database constraints, optimistic versions, and durable per-student creation receipts. Stale edits return 409; replay after deletion returns 410 instead of resurrecting evidence. Private browser queries share one identity-scoped namespace and pending requests are cancelled on logout/account changes. Forms retain unsaved input after failures and require confirmation before replacing it.

Consequences: Existing identities/contracts need no migration or Auth0 scope changes. The profile remains suitable for future application/MCP use cases without relying on Auth0 user metadata. Provider imports, score conversions, adaptive placement, and account linking require later explicit designs. See [onboarding](../onboarding.md) and [verification](../onboarding-verification.md).
