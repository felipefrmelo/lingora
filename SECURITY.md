# Security boundaries

Milestone 1 exposes public operational endpoints and a welcome page only. There are no student-data APIs, login flows, MCP tools, or authentication bypasses. This foundation is not a production-readiness certification.

Secrets belong in environment-specific secret management. `.env` files are ignored; example local database credentials are intentionally disposable. Never use them in hosted environments or put client secrets in Vite configuration. Use environment-specific Auth0 tenants/applications, exact origins, and HTTPS outside local development.

Future private endpoints must verify access-token signature, exact issuer, expected audience, expiration, allowed algorithms, and scopes. Check student ownership separately. A route guard or Auth0 permission claim never replaces resource ownership checks. Use one internal identity mapping for web and MCP; do not merge accounts by email.

Do not store access tokens, recordings, or full conversations by default. The current logger and custom spans exclude arbitrary paths, query values, bodies, and headers. Run Uvicorn with `--no-access-log` as documented to avoid its separate full-URL access logs. Production reverse proxies and exporters require equivalent filtering. Production rate limits and trusted-proxy configuration are part of the later deployment/security milestone; no distributed limiter is claimed here.

Future AI output and ingested news are untrusted data. Schema validation, licensing checks, backend authorization, and database constraints remain authoritative. Student export/deletion, consent, retention, audit events, and pedagogical evidence controls must be implemented before a real learner pilot.

Run `make audit` for dependency advisories. The standard CI suite uses local fixtures and no live Auth0 or AI credentials. Real Auth0/ChatGPT connection testing is a separate nonproduction acceptance gate.
