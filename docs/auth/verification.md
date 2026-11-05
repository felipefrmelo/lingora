# Milestone 2 verification

Dates: 2026-11-04–05 (America/Sao_Paulo). Branch: `codex/auth0-authentication`.

**Status: Milestone 2 implementation and development acceptance complete on 2026-11-05.** The implementation is published in [PR #1](https://github.com/felipefrmelo/lingora/pull/1) for review. No production application deployment is claimed.

## Automated checks executed

- Backend: 58 unit/configuration/HTTP tests; valid/malformed tokens, signatures, algorithm restrictions, expiry/nbf, issuer/audience/claims/scopes, verification policy, JWKS rotation/outages, problem details, and rejected identity selectors.
- PostgreSQL: 10 integration tests, including eight concurrent first logins, rollback without orphan students, idempotency, unprovisioned reads, and separate subjects sharing email.
- Frontend: 17 unit tests covering guards, callback/error handling, bootstrap failures, token retry, logout cleanup, and identity changes.
- Auth0 Action sources: 8 Node tests covering verification and legacy-linker isolation.
- Playwright: 6 desktop/mobile tests with Auth0 unconfigured; no live credentials in ordinary CI.
- Ruff lint/format, strict Pyright, ESLint, TypeScript, and production build passed. The build reports a 700 KB JavaScript chunk-size warning; no production performance certification is claimed.
- Python and production JavaScript dependency audits reported no known vulnerabilities.
- [GitHub CI run 3](https://github.com/felipefrmelo/lingora/actions/runs/41957651645) passed both verification and dependency-audit jobs on the published implementation.
- OpenAPI and TypeScript contracts regenerated; repeat generation produced identical SHA-256 hashes; no contract drift.

## Tenant configuration observed

The dedicated SPA, API, and database exist. The SPA callback/logout/web origins are saved, Authorization Code is its only enabled grant, and only the dedicated database plus existing Google connection are enabled. The API has RS256, 300-second tokens, no offline/client access, and exactly two scopes granted only to Lingora. The shared linker exclusion is deployed. **Lingora Require Verified Email** (`5d507a41-a4ae-4a34-b8e4-5fe5bc73f51e`) is deployed and bound first in Post Login. The dashboard confirms all changes live, followed by the unchanged relative order: account linking, Add Owner Sub Claim, Add email. The user completed the drag-and-drop handoff, and the saved sequence was read back.

## Opt-in real-tenant acceptance

Run local services with the ignored configuration in [setup](auth0-setup.md), then open `http://localhost:5173`. Use nonproduction test accounts. Never record passwords, access tokens, authorization codes, or verification/reset links in this report. Record outcomes and internal student IDs only as needed to compare stability.

| Journey | Result |
| --- | --- |
| Email/password registration in dedicated database | Passed: Success Signup in Lingora-Users-Development at 02:39:08 UTC. Password entered/submitted by the user. |
| Unverified email denied private access with useful feedback | Passed: two failed logins with `lingora_email_verification_required` before verification. The user confirmed on 2026-11-05 that Lingora displayed “Check your email” and blocked private access until verification. |
| Verification email received and confirmed; sign-in succeeds | Passed: verification link consumed at 02:40:09 UTC, login/code exchange at 02:40:19–20 UTC, then protected account page and a new internal student. |
| Password reset email and user-completed reset; sign-in succeeds | Passed per user confirmation on 2026-11-05: “done works” after the reset-and-sign-in handoff. Both existing local student identities remain unchanged. No password or reset link was handled by the agent. |
| Google sign-in succeeds | Passed on 2026-11-05: Continue with Google reached the protected account. Auth0 records Success Login via `google-oauth2` at 11:48:00 UTC and code exchange at 11:48:01. |
| Repeat sign-in/bootstrap preserves student UUID | Passed with the existing verified password identity; initially retained the original student; subsequent dedicated-database sign-in/recovery also preserved its separate UUID. |
| Same-email Google/password identities remain separate | Passed for the dedicated Lingora database: Google resolves the original student; the newly registered Lingora password identity with the same email retains its different student UUID. No new student or mapping appeared during Google login. |
| Reload/session recovery, or privacy-blocked recovery requiring interaction | Passed in Safari: memory cache cleared on reload; `/app` required interactive sign-in, which recovered the same student without a redirect loop. |
| After 300-second token expiry, account request recovers or requests sign-in without a loop | Passed in Safari: latest exchange at 02:40:20 UTC; after 02:45:20 the account page required sign-in, interactive consent restored private access, and both existing student UUIDs remained stable. No raw token was retained. |
| Denied consent and retry | Passed on 2026-11-05: declining Auth0 consent returned to `/auth/callback` with “Access was not granted,” no private account content, and a working sign-in retry. |
| Logout clears account content; direct `/app` requires sign-in | Passed: public home after Auth0 logout, no previous account content, direct `/app` shows the sign-in guard. |

Keep API and web running, note the account UUID, refresh, and repeat sign-in. Compare UUIDs within each identity and between distinct providers. Wait beyond the configured token lifetime before retrying an account fetch; do not store a bearer token merely to test expiry. Use the dashboard to resend verification in development if necessary. The user must enter and submit passwords and any provider challenges directly. Document any browser privacy limitation observed rather than weakening privacy settings.

The shared tenant shows Ozix branding on Auth0 consent. The user explicitly approved this Lingora consent after seeing that wording; tenant-wide branding was left unchanged. The initial session resolved a verified `auth0` password identity, so this result does not establish fresh registration or Google login.

The scoped Auth0 log sequence confirms signup in the dedicated database at 02:39:08 UTC, verification denials at 02:39:09 and 02:39:15, successful verification at 02:40:09, and login/code exchange at 02:40:19–20 on 2026-11-05 UTC (2026-11-04 local time). No raw token, code, verification link, email, or password is retained in this report.

The tested Google account was already linked to a legacy shared-tenant identity before Lingora configuration, so its Auth0 subject has the `auth0` prefix even though the observed login connection is `google-oauth2`. That existing relationship was preserved. It remains separate from the dedicated Lingora database student. This is not evidence of a new link or a newly created Google-only identity.
