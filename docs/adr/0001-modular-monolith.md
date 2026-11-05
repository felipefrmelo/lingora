# 0001 — Modular monolith

Status: Accepted. Date: 2026-11-04.

Context: REST and MCP must share pedagogical rules and persistence without distributed-system overhead.

Decision: One Python application, organized by business capability, with thin transport adapters invoking shared application use cases. Create only modules with implemented behavior. Avoid cyclic module dependencies, global unrelated services, event sourcing, and full CQRS.

Consequences: Transactions and local development stay simple. HTTP and MCP can evolve independently of domain rules. Extract a service only after a measured scaling or ownership need appears.
