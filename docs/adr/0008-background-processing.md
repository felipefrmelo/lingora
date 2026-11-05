# 0008 — Background processing

Status: Accepted. Date: 2026-11-04.

Context: Generation, ingestion, and scheduled reviews will need reliable asynchronous work, but foundation has no such jobs.

Decision: Add no queue, worker, or scheduler now. When work must survive restarts, introduce the simplest durable job mechanism with persisted status, bounded retries, observability, and idempotency. FastAPI BackgroundTasks is unsuitable for important persistent learning operations.

Consequences: Initial operations are straightforward request/response work. Choose and document a concrete durable mechanism when the first qualifying job is implemented; this is intentionally deferred rather than a missing foundation dependency.
