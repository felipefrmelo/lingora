# 0005 — React authentication

Status: Accepted; implementation scheduled for Milestone 2. Date: 2026-11-04.

Context: A browser SPA cannot safely store client secrets or replace backend authorization with route guards.

Decision: Use the official Auth0 React SDK with Universal Login, Google through Auth0, Authorization Code with PKCE, memory-based token storage, and allowlisted callback/return paths. Send access tokens for the REST audience, never ID tokens, to protected APIs. Keep onboarding separate from identity registration.

Consequences: The SDK handles authentication lifecycle; backend JWT/scopes/ownership checks remain mandatory. Real login, renewal, and logout verification is a nonproduction acceptance gate. No login button or fake authentication is shipped in Milestone 1.
