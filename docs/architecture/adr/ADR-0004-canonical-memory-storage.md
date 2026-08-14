# ADR-0004: Canonical Memory Storage

- Status: Accepted
- Date: 2026-08-13

## Context

Future memory retrieval may benefit from semantic indexes, but similarity-search systems do not provide an appropriate authoritative record for all durable structured memory.

## Decision

Future durable structured memory will use a canonical structured store. A vector database will be a semantic index, not the authoritative memory database.

No concrete storage product is selected by this decision.

## Consequences

- Durable memory has one authoritative structured representation.
- Semantic indexes must be rebuildable from canonical data.
- Storage selection and memory implementation remain outside M0.
