# 0012 — Conversation sessions and MCP access

Status: implementation in progress; real Auth0 and ChatGPT acceptance pending.

Conversation sessions reference immutable student-owned lessons and retain explicit state, target level, correction preference, and an opt-in for short feedback examples. Completion atomically stores structured tutor-reported feedback and an audit event. Idempotency receipts and optimistic versions make retries and concurrent changes visible. A voice disconnect does not complete a session, and feedback does not establish mastery.

The Streamable HTTP adapter uses the official MCP SDK and calls the same application operations as REST. It runs through a separate MCP-only listener to keep the website API off the development tunnel. Tokens require the dedicated resource audience, approved Auth0 client, verified email, and operation scopes. Access is disabled by default per student and can be revoked without waiting for token expiry; JWT issuance cutoffs prevent old access tokens from reactivating on reconnection.

Consequences: the website must enable access before tool use, and a separate OAuth connection is needed in ChatGPT. Full transcripts are not retained. Identity remains the verified Auth0 issuer/subject mapping, never email. Actual tenant compatibility, token refresh, account isolation, and both text and voice journeys remain completion gates. See [conversation sessions](../conversation.md).
