# MCP development verification

Status: **in progress**. No real ChatGPT conversation or voice session has been verified. These notes do not claim Milestone 5 completion.

On 2026-11-05, the existing development tenant was inspected. A separate API named **Lingora MCP Development** was created with identifier `https://exhaustedly-overcultured-jeane.ngrok-free.dev/mcp`, RS256, per-application user-delegated authorization, and no machine-to-machine access. The API defines `profile:read`, `lessons:read`, `sessions:read`, and `sessions:write`. Its maximum and implicit/hybrid access-token lifetimes were set to 900 seconds and offline access enabled; the SPA policy was not changed.

Resource-parameter compatibility was already enabled on the shared tenant. CIMD discovery and issuer responses were enabled after approval. Dynamic CIMD registration remains disabled; the existing tenant-wide DCR setting was not changed. Public discovery advertises CIMD and issuer support. The public ChatGPT metadata document advertises `private_key_jwt`, authorization-code and refresh-token grants, and its stable callback. A manually registered ChatGPT third-party client exists with public Auth0 client ID `tpc_u4W4Bp3PuBdTUiRXZHNsPu`. It has not been granted access to the Lingora MCP API.

The existing Lingora verification Action has an undeployed draft with resource/client-scoped MCP checks. A matching legacy account-linker exclusion has been reviewed and tested in the repository but is not yet deployed. Do not grant API access until both deployed Actions are verified. ChatGPT client refresh-token rotation and lifetime settings remain unverified.

The isolated MCP-only development listener was exposed through the ngrok development hostname with local request inspection and logging disabled. Public discovery returned the exact MCP resource; unauthenticated `/mcp` returned 401 and `/api/v1/me` returned 404 through the tunnel. No real OAuth client was authorized during this check. The ngrok authtoken appeared in a browser automation output; the user reported rotating and locally configuring a replacement before the tunnel was started. Never include that token in repository files or logs.

Local automated tests cover protected MCP calls using test-signed tokens, wrong audiences and clients, JWKS outages, scope challenges, ownership, disabled access, session transitions, durable feedback retries, migration round trips, and browser guards. Tests use mocks and do not prove real Auth0/ChatGPT compatibility. CI status is recorded on the draft PR; checks must pass on the final revision.

Remaining acceptance: complete scoped Auth0 Actions, approved client grant and refresh policy; verify Inspector and ChatGPT authorization, same-student lesson recovery, write confirmation and replay, account isolation, expiration, refresh, disable/reconnect, and separate real text and voice conversations. Record failures and actual outcomes rather than assuming success.
