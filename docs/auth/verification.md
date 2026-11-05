# Milestone 2 verification

Date: 2026-11-04. Branch: `codex/auth0-authentication`.

**Status: implementation and automated verification complete; live acceptance pending.** Do not mark Milestone 2 complete until every required journey below succeeds.

## Automated checks executed

- Backend: 58 unit/configuration/HTTP tests; valid/malformed tokens, signatures, algorithm restrictions, expiry/nbf, issuer/audience/claims/scopes, verification policy, JWKS rotation/outages, problem details, and rejected identity selectors.
- PostgreSQL: 10 integration tests, including eight concurrent first logins, rollback without orphan students, idempotency, unprovisioned reads, and separate subjects sharing email.
- Frontend: 17 unit tests covering guards, callback/error handling, bootstrap failures, token retry, logout cleanup, and identity changes.
- Auth0 Action sources: 8 Node tests covering verification and legacy-linker isolation.
- Playwright: 6 desktop/mobile tests with Auth0 unconfigured; no live credentials in ordinary CI.
- Ruff lint/format, strict Pyright, ESLint, TypeScript, and production build passed.
- Python and production JavaScript dependency audits reported no known vulnerabilities.
- OpenAPI and TypeScript contracts regenerated; repeat generation produced identical SHA-256 hashes; no contract drift.

## Tenant configuration observed

The dedicated SPA, API, and database exist. The SPA callback/logout/web origins are saved, Authorization Code is its only enabled grant, and only the dedicated database plus existing Google connection are enabled. The API has RS256, 300-second tokens, no offline/client access, and exactly two scopes granted only to Lingora. The shared linker exclusion is deployed. **Lingora Require Verified Email** (`5d507a41-a4ae-4a34-b8e4-5fe5bc73f51e`) is deployed; binding it to Post Login is awaiting a manual drag-and-drop handoff because Safari automation did not complete the drop. Its deployed state alone does not enforce verification until bound.

## Opt-in real-tenant acceptance

Run local services with the ignored configuration in [setup](auth0-setup.md), then open `http://localhost:5173`. Use nonproduction test accounts. Never record passwords, access tokens, authorization codes, or verification/reset links in this report. Record outcomes and internal student IDs only as needed to compare stability.

| Journey | Result |
| --- | --- |
| Email/password registration in dedicated database | Pending user password entry |
| Unverified email denied private access with useful feedback | Pending |
| Verification email received and confirmed; sign-in succeeds | Pending |
| Password reset email and user-completed reset; sign-in succeeds | Pending |
| Google sign-in succeeds | Pending |
| Repeat sign-in/bootstrap preserves student UUID | Pending |
| Same-email Google/password identities remain separate | Pending |
| Reload/session recovery, or privacy-blocked recovery requiring interaction | Pending |
| After 300-second token expiry, account request recovers or requests sign-in without a loop | Pending |
| Logout clears account content; direct `/app` requires sign-in | Pending |

Keep API and web running, note the account UUID, refresh, and repeat sign-in. Compare UUIDs within each identity and between distinct providers. Wait beyond the configured token lifetime before retrying an account fetch; do not store a bearer token merely to test expiry. Use the dashboard to resend verification in development if necessary. The user must enter and submit passwords and any provider challenges directly. Document any browser privacy limitation observed rather than weakening privacy settings.
