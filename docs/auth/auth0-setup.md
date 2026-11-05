# Auth0 setup for Milestone 2

**Status: architecture and manual setup instructions only. No tenant was changed, no login was implemented, and no real flow has been verified.** Ordinary foundation startup and CI need no Auth0 values.

## Environment isolation

Use separate development and production tenants where practical. Record real environment-specific issuer, SPA client ID, API identifier, origins, and callback URLs in deployment configuration; do not embed tenant identifiers in application code. Use one exact issuer consistently across web and MCP identity resolution, including the trailing slash. Moving between tenant/custom-domain issuers needs an explicit identity migration.

## Configure the web application

1. Create an Auth0 **Single Page Application** named `Lingora Web`.
2. Enable Universal Login with Authorization Code and PKCE S256. The future frontend uses `@auth0/auth0-react`, not a hand-built OAuth client. Request `openid profile email` for identity and only the application scopes required by implemented endpoints; do not request offline access in the SPA by default.
3. Set Allowed Callback URLs to `http://localhost:5173/auth/callback`, Allowed Logout URLs to `http://localhost:5173`, and Allowed Web Origins to `http://localhost:5173` for local development. Use that hostname consistently. Add exact HTTPS production URLs to the separate production application, not broad wildcards.
4. Under Authentication > Social, configure the Google connection and enable it for this application. Use Google credentials stored in Auth0; configure Google's redirect URI using the callback shown by Auth0. A stable hosted environment requires your own Google provider credentials rather than relying on development keys.
5. Populate `VITE_AUTH0_DOMAIN`, `VITE_AUTH0_CLIENT_ID`, `VITE_AUTH0_AUDIENCE`, and `VITE_AUTH0_REDIRECT_URI` in the frontend environment. These are public identifiers; never add a client secret.

## Configure the REST resource server

1. Create an Auth0 API named `Lingora API` with a stable HTTPS identifier, for example `https://api.lingora.example`. `.example` values are documentation only and must be replaced with your own environment identifiers. An audience identifier need not be an HTTP endpoint, but it must remain stable.
2. Select RS256 signing. Define `profile:read`, `profile:write`, `lessons:read`, `exercises:write`, `sessions:read`, `sessions:write`, and `progress:read`. The first implementation requests only the scopes its actual endpoints need.
3. Configure grants and consent so intended learner applications can request their permitted scopes; do not grant management permissions. If using Auth0 RBAC, enable permissions in tokens as appropriate and test their actual `scope`/`permissions` contents. Dashboard permission definitions alone do not grant access or enforce ownership.
4. Set `AUTH0_DOMAIN`, `AUTH0_ISSUER` (`https://<domain>/`), `AUTH0_API_AUDIENCE` (the exact identifier), and `AUTH0_JWKS_URL` (`https://<domain>/.well-known/jwks.json`). Pin trusted endpoints to configuration, not unverified token fields.

## Backend implementation requirements

Verify signature, allowed algorithm, exact issuer, intended audience, expiration, `nbf` when present, and endpoint scopes. Missing/invalid access tokens receive 401 with a bearer challenge; valid tokens without required permission receive 403. ID tokens are not API credentials. Cache trusted JWKS, allow bounded refresh for a new key ID, and reject unknown keys if refresh fails.

Create a typed verified principal independent of FastAPI. Resolve `(provider='auth0', issuer, subject)` into an internal Student UUID. Provision in one transaction with database uniqueness and conflict recovery so concurrent first logins resolve one student. Do not identify or merge students by email or accept a request student ID as authorization.

The React SDK owns login, callback, token acquisition, expiry recovery, and logout. Keep its memory-based token-storage default. Use an allowlisted local return path after login. There is no separate registration step; missing onboarding data leads to the later onboarding workflow. Logout clears the SDK session; document access-token lifetime separately from immediate revocation assumptions.

## Acceptance gate

Use local signing keys and a controlled JWKS server for normal CI: valid, expired, invalid-signature, wrong issuer/audience, missing-scope, key rotation, and cross-student tests. Then use the development tenant for real login, Google login, callback, reload/session recovery, protected endpoint access, expiry, and logout tests. Record actual results and required tenant settings. Do not mark authentication complete based on mocks.

## Sources

- [Auth0 React quickstart](https://auth0.com/docs/quickstart/spa/react)
- [Auth0 access-token validation](https://auth0.com/docs/secure/tokens/access-tokens/validate-access-tokens)
- [Auth0 Google connection](https://auth0.com/docs/authenticate/identity-providers/social-identity-providers/google)
