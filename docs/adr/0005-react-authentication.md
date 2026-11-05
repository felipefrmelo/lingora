# 0005 — React authentication

Status: Accepted; implemented in Milestone 2, with development acceptance verified on 2026-11-05. Decision date: 2026-11-04.

Context: A browser SPA cannot safely store client secrets or replace backend authorization with route guards.

Decision: Use the official Auth0 React SDK with Universal Login, Google through Auth0, Authorization Code with PKCE, memory-based token storage, and allowlisted callback/return paths. Send access tokens for the REST audience, never ID tokens, to protected APIs. Keep onboarding separate from identity registration.

Consequences: The SDK handles authentication lifecycle; backend JWT/scopes/ownership checks remain mandatory. The signed-in account page bootstraps the internal student before fetching private account data. Private queries are keyed by verified SDK subject and purged on logout/identity changes. One cache-bypassing token acquisition may retry a 401 for the read/idempotent bootstrap operations; 403/503 do not trigger renewal or logout. Real login, renewal, and logout verification is a nonproduction acceptance gate. No runtime fake-auth provider is shipped.
