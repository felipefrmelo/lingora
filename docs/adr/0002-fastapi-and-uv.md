# 0002 — FastAPI and uv

Status: Accepted. Date: 2026-11-04.

Context: The application needs typed HTTP contracts, Python AI tooling, and repeatable agent-friendly setup.

Decision: Python 3.13 with FastAPI, Pydantic v2, pydantic-settings, uv, Ruff, strict Pyright, and pytest. Python 3.13 is supported and already available locally. Commit uv.lock and use locked installs. Use async I/O in requests and separate synchronous Alembic CLI execution.

Consequences: OpenAPI derives from actual DTOs. Future runtime upgrades require compatibility checks and lockfile updates. Operational startup remains independent of Auth0, PostgreSQL connectivity, and AI credentials.
