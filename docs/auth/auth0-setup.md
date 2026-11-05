# Auth0 authentication

Milestone 2 implements registration/sign-in through Universal Login, logout, and protected self-account access. Automated checks and the real development-tenant acceptance journey passed; see [verification](verification.md) for the evidence, user-assisted steps, and shared-tenant limitations.

## Development resources

The existing tenant is `dev-41ngpa0fd1yfxllv.us.auth0.com`. Its dashboard is labeled **PRODUCTION** and contains other applications: Lingora uses dedicated development resources, with no changes to unrelated applications or tenant-wide login branding.

| Resource | Public identifier |
| --- | --- |
| Lingora Web Development (SPA) | `HRkpYwW1ZcxaA5mqq3Zc6dQKcDAkAtYe` |
| Lingora API Development | `6aebe680b6b0539d0d4367f2` |
| API audience | `https://lingora.local/api` |
| Lingora-Users-Development | `con_4LXEnig2wRbDn0CD` |
| Existing Google connection | `google-oauth2` |

An API audience identifies a resource; it needs no hosting or DNS. Preserve the exact issuer, including its trailing slash, across web and future MCP identity resolution. Changing issuer requires an explicit identity migration. Use separate production resources and exact HTTPS URLs before deployment.

## Application and API configuration

The SPA uses Authorization Code with PKCE S256. Only Authorization Code is enabled; implicit, password, client credentials, and refresh-token grants are disabled. The SDK stores tokens in memory and does not request offline access. Configure:

- Allowed Callback URLs: `http://localhost:5173/auth/callback`
- Allowed Logout URLs: `http://localhost:5173`
- Allowed Web Origins: `http://localhost:5173`
- Connections: dedicated Lingora database and existing Google connection. Shared `Username-Password-Authentication` is disabled for Lingora.

The API uses RS256, a 300-second development token lifetime, user-delegated **Per-app authorization**, and client access **No apps allowed**. Offline access and RBAC are disabled. Only `profile:read` and `profile:write` exist; grant exactly these to the Lingora SPA. Do not automatically grant future scopes. Other applications have no grant. Auth0 automatically created an unused API test application; it has no profile grant and cannot obtain client-credentials access to this API.

## Email verification and account linking

Deploy [require-verified-email.js](../../infra/auth0/require-verified-email.js) as a Post-Login Action named **Lingora Require Verified Email**. Set its `LINGORA_CLIENT_ID` configuration value to the public SPA ID above. Bind it without removing or reordering the existing Actions. It returns immediately for other applications, denies unverified Lingora logins with `lingora_email_verification_required`, and adds the boolean access-token claim `https://lingora.local/api/email_verified` only for verified users. The backend independently requires that claim.

The existing shared `account linking` Action (`ad70edfd-4e5f-4aeb-b600-858dd43b1b47`) previously linked accounts by matching email. Its deployed [reviewed exclusion](../../infra/auth0/legacy-linker-exclusion.md) skips Lingora logins/database identities and excludes Lingora database identities from candidates found through other apps. Existing applications keep their previous linking behavior. Matching Google and password email addresses never cause Lingora to merge student identities. Explicit account linking is deferred.

Email/password signup and password reset use Auth0, not Lingora forms. In development, verification resends use the Auth0 dashboard; self-service resends are deferred. Users enter and submit new passwords themselves. Never copy credentials into this repository. Do not replace the existing Google provider credentials; inspect Auth0 warnings and use dedicated provider credentials before a production launch.

## Local configuration

Root `.env` (ignored):

```dotenv
AUTH0_DOMAIN=dev-41ngpa0fd1yfxllv.us.auth0.com
AUTH0_ISSUER=https://dev-41ngpa0fd1yfxllv.us.auth0.com/
AUTH0_API_AUDIENCE=https://lingora.local/api
AUTH0_JWKS_URL=https://dev-41ngpa0fd1yfxllv.us.auth0.com/.well-known/jwks.json
AUTH0_EMAIL_VERIFIED_CLAIM=https://lingora.local/api/email_verified
```

`apps/web/.env.local` (ignored):

```dotenv
VITE_AUTH0_DOMAIN=dev-41ngpa0fd1yfxllv.us.auth0.com
VITE_AUTH0_CLIENT_ID=HRkpYwW1ZcxaA5mqq3Zc6dQKcDAkAtYe
VITE_AUTH0_AUDIENCE=https://lingora.local/api
VITE_AUTH0_REDIRECT_URI=http://localhost:5173/auth/callback
```

These are public identifiers. No SPA client secret is needed. Use `localhost`, consistently, in the browser. Run `make db-up migrate`, then `make dev-api` and `make dev-web` in separate terminals. Ordinary CI blanks frontend Auth0 values and uses test-only signing keys/mocks. No live tenant credential or runtime auth bypass is required.

## Identity and authorization

The API validates signature, RS256, trusted key ID, exact issuer/audience, expiration, issued-at, subject, optional `nbf`, verified-email claim, and endpoint scopes. Trusted JWKS are cached for 300 seconds, with five-second network timeout and bounded unknown-key refresh. Synchronous PyJWT/JWKS work runs outside the event loop. Token-provided key URLs are ignored. Unknown signing keys fail closed; unavailable trusted key retrieval returns 503.

| Endpoint | Scope | Behavior |
| --- | --- | --- |
| `POST /api/v1/me/bootstrap` | `profile:write` | Provision or resolve the current student idempotently. No identity fields. |
| `GET /api/v1/me` | `profile:read` | Retrieve the existing student; 404 before bootstrap. |

Responses contain only internal UUID and creation timestamp. Provider profile information stays in the SDK. The immutable principal is independent of FastAPI. Application transactions resolve `(provider=auth0, issuer, subject)`, never email. Concurrent provisioning rolls back the losing transaction before resolving the winning identity, leaving no orphan student.

Problem details distinguish invalid credentials (401), insufficient authorization (403), unprovisioned account (404), and unavailable auth configuration/key retrieval (503). Health checks remain public without Auth0 configuration. Account, profile, and assessment queries share a private subject-scoped namespace and are removed on logout/SDK subject changes; pending private requests are aborted and keyed forms unmount. Tokens attach only to protected API requests. A 401 allows one silent cache-bypassing token retry; failures requiring interaction show a sign-in control without redirect loops. Browser privacy restrictions may require interactive sign-in after a reload. Logout clears the browser session but does not revoke previously issued JWTs; expiry bounds their remaining validity.

## Reference documentation

- [Auth0 React SDK](https://auth0.github.io/auth0-react/)
- [Access token validation](https://auth0.com/docs/secure/tokens/access-tokens/validate-access-tokens)
- [Google connection](https://auth0.com/docs/authenticate/identity-providers/social-identity-providers/google)

Milestone 3 reuses the existing profile scopes and adds no tenant changes. See [onboarding](../onboarding.md) for new self-resource endpoints, optimistic versions, and creation keys.
