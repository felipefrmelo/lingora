# Conversation sessions and MCP

Milestone 5 is in progress. Automated local checks do not establish ChatGPT, Auth0, ngrok, or voice interoperability; the real development journey remains a completion gate. See [development verification](auth/mcp-verification.md) for actual configuration and results.

A learner can prepare one unfinished session from a saved lesson, choose whether to retain short examples, and abandon an unfinished session before starting another. The session snapshots its lesson's target level and the profile's correction mode. ChatGPT may change the session correction mode without editing the profile. A conversation is complete only after a feedback write commits. A disconnected chat or voice call does not complete it.

Final feedback contains a summary, up to three strengths and three priorities, and up to six tutor-reported observations. Short examples and suggested corrections are allowed only when the session permits them. Lingora does not store full transcripts or recordings. Observations do not change selected CEFR or establish mastery. Students can find stored feedback in conversation history. Session creation and mutation keys make identical retries safe; changed payloads or stale versions conflict.

MCP access is disabled for each student until explicitly enabled. Disabling blocks subsequent calls and records a token issuance cutoff; re-enabling does not revive access tokens issued before the cutoff. Disconnecting the plugin in ChatGPT and revoking its OAuth authorization are separate actions.

## Development listener

The MCP listener is a separate entry point of the same application, with its own localhost port. It shares application use cases and PostgreSQL with REST, but exposes only `/mcp`, protected-resource metadata, and `/mcp-docs`. Configure the following in the ignored root `.env` after the Auth0 API and approved clients exist:

```dotenv
MCP_RESOURCE_URL=https://exhaustedly-overcultured-jeane.ngrok-free.dev/mcp
MCP_ALLOWED_CLIENTS=["https://chatgpt.com/oauth/client.json"]
```

The exact resource URL is also the Auth0 API audience. `MCP_ALLOWED_CLIENTS` contains the exact approved identifiers present in signed access tokens' `azp` claims, not tokens or client secrets. For the configured Auth0 CIMD flow, ChatGPT's `azp` is its metadata URL above; Auth0's internal `tpc_` identifier is used to configure the client and Actions, but is not the value observed in that token. Verify any additional client's actual identifier before allowing it. Missing configuration makes the listener fail closed. `make dev-mcp` binds port 8080 to localhost. Once Auth0 and the tunnel are ready, a local ngrok process can expose that port using `ngrok http 8080 --url https://exhaustedly-overcultured-jeane.ngrok-free.dev --inspect=false --log=false`. This endpoint is for development only. Neither request bodies nor authorization headers should be retained by local traffic inspection or proxy logging.

The SDK verifies each HTTP bearer token using the existing trusted Auth0 JWKS verifier, a separate audience, verified email, approved client ID, and per-tool scopes. The server publishes metadata and never issues OAuth tokens. No token or learner content belongs in logs. Tunnel availability depends on the local process and ngrok account.

Seven tools support student preferences, pending session and lesson lookup, session status, start, correction preference changes, and final completion. The structured lesson response excludes exercise answer keys. Feedback is not synchronized until the backend confirms its transaction. MCP clients should retry an uncertain write with the same idempotency key and payload.

The actual CIMD client identifiers, connections, Action scoping, refresh behavior, and verified tenant settings must be recorded after configuration. Do not infer compatibility from mock tests. Browser privacy, external client policies, and voice tool availability must be checked in the real environment.
