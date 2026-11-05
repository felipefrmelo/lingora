# MCP authorization for Milestone 5

**Status: documented design only. There is no MCP endpoint, registration, account-linking flow, or verified ChatGPT connection in Milestones 1–2.** Recheck current SDK/provider specifications when implementing it.

## Resource and identity

Mount a Streamable HTTP MCP adapter in the same monolith using the official Python `mcp` SDK. Tools call application use cases directly; do not forward a bearer token to the REST resource. Both adapters resolve the same exact Auth0 issuer/subject mapping to the internal Student UUID.

Create a separate Auth0 API for the canonical MCP URL, for example `https://mcp.lingora.example/mcp`. Set both `MCP_RESOURCE_URL` and `AUTH0_MCP_AUDIENCE` to that actual canonical resource. Do not accept the REST audience at the MCP boundary or reuse the SPA client as the ChatGPT OAuth client. Reject a token issued for another resource even if its issuer and subject are familiar.

## Authorization and discovery

1. Configure Auth0 as the authorization server; do not implement an OAuth server or proxy its discovery endpoints under the application domain.
2. Select **CIMD** as the client registration method. Register/approve the current ChatGPT client metadata document in Auth0 and confirm discovery advertises support. Obtain the metadata URL and exact redirect URIs from the current OpenAI documentation/connection setup; do not guess or reuse an old callback list. If the actual tenant cannot support this selected mode, treat it as a documented compatibility blocker rather than silently opening dynamic registration.
3. Enable Auth0's **Resource Parameter Compatibility Profile**. Confirm the exact API identifier matches the canonical MCP resource. Do not assume OAuth `resource` equals Auth0 `audience` without this configured behavior. Inspect actual issued access tokens and reject a userinfo-only audience. Avoid conflicting audience/resource settings.
4. Use Authorization Code with PKCE S256 and exact redirect URI validation. Verify Auth0 discovery, registration mode, supported token-endpoint authentication methods, and token lifetime with the selected ChatGPT flow.
5. Expose protected-resource metadata at `/.well-known/oauth-protected-resource` and the path-aware `/.well-known/oauth-protected-resource/mcp` for a canonical `/mcp` resource, using the SDK's supported routing. Advertise the canonical metadata URL in `WWW-Authenticate` on 401 responses. Metadata includes the exact resource URL, Auth0 issuer in `authorization_servers`, actual supported scopes, and hosted resource documentation.
6. Include current per-tool OAuth security metadata, least-privilege read/write scopes, and appropriate authorization-required tool challenges. Validate authentication at HTTP and tool execution boundaries.

The Python SDK's current docs include a v2 migration path. Select and lock the stable SDK version during implementation; do not copy old `FastMCP` APIs blindly. Foundation has no unused SDK dependency.

## Token lifecycle

Use refresh tokens only if the selected ChatGPT flow and Auth0 configuration support them. If required, enable API offline access, request `offline_access`, and configure rotation/reuse detection and appropriate absolute/inactivity lifetimes. Verify actual refresh behavior rather than assuming `offline_access` alone is sufficient. Document reconnect after expiration/revocation, consent changes, and disconnect behavior. Never store or log raw access tokens in application records.

## Tool behavior

Implement only tools required for the main lesson handoff first: verified student context, pending/current lesson lookup, start/resume session, correction preferences, evidence-backed observations, and confirmed completion. The source PRD defines the complete proposed names.

Every tool validates input/output, resolves identity, checks scopes and ownership, and executes one application operation. Retry-sensitive writes need idempotency keys and conflict/version handling. Session transitions are explicit: READY, IN_PROGRESS, COMPLETED, ABANDONED. Mark completion synchronized only after commit confirmation. Observations do not directly declare mastery and must not be duplicated on retries. A voice disconnect is not completion.

## Acceptance gate

Test discovery, bearer challenges, valid and missing/wrong-resource tokens, scopes, expiry, key rotation, student isolation, ownership, idempotency, concurrency, and failed persistence using deterministic fixtures. Then validate with MCP Inspector and an actual ChatGPT connection through public HTTPS: login, consent, pending-session recovery, observations, completion confirmation, refresh, revocation, and reconnect. Record tenant settings and observed token audience. Until these pass, the integration is unverified.

## Sources checked during initialization

- [OpenAI plugin authentication](https://developers.openai.com/plugins/build/auth)
- [Auth0 MCP authorization and CIMD](https://auth0.com/blog/auth0-auth-for-mcp-servers-generally-available/)
- [MCP authorization specification](https://modelcontextprotocol.io/specification/latest/basic/authorization)
- [Official Python MCP SDK](https://py.sdk.modelcontextprotocol.io/)
