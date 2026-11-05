# 0006 — Auth0 authorization for MCP

Status: Accepted design; integration unverified until Milestone 5. Date: 2026-11-04.

Context: ChatGPT must access the same learner with resource-scoped tokens and supported OAuth discovery/registration.

Decision: Use the official Python MCP SDK, Streamable HTTP, and Auth0 as authorization server. The canonical MCP URL identifies a separate Auth0 API/audience. Select CIMD registration and PKCE S256. Configure Auth0 resource-parameter compatibility and validate the actual token audience. The application serves protected-resource metadata and challenges, not a custom authorization server. MCP calls shared use cases directly rather than passing MCP tokens to REST.

Consequences: REST and MCP share identity/authorization rules while token audiences remain distinct. Exact current client metadata, redirect URIs, SDK capabilities, refresh behavior, and tenant settings require verification. Inspector plus actual ChatGPT account linking and confirmed persistence are required before claiming interoperability. See the MCP OAuth guide.
