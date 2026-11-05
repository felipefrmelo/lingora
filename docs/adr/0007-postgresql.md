# 0007 — PostgreSQL persistence

Status: Accepted. Date: 2026-11-04.

Context: Identity uniqueness, student ownership, concurrency, and dependable migrations need relational constraints and real database tests.

Decision: PostgreSQL 18 with SQLAlchemy 2, psycopg 3, and Alembic. Use internal UUIDs, foreign keys, appropriate indexes, timestamps, and explicit transactions. The initial schema contains students and external identities only. Use optimistic versions and idempotency records when retry-sensitive operations are introduced.

Consequences: Integration tests run against PostgreSQL, not SQLite. Development data uses a named Compose volume; integration tests use a separate ephemeral service and require a database name ending in `_test`. Migrations are explicit commands, never implicit application startup side effects.
