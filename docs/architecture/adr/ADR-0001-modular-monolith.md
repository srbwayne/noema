# ADR-0001: Modular Monolith

- Status: Accepted
- Date: 2026-08-13

## Context

Noema needs strong capability boundaries without the operational complexity of distributed services during V1.

## Decision

Noema V1 uses a Modular Monolith organized by bounded context.

Each context owns its internal model and exposes deliberate contracts. Deployment remains a single runtime unless a later architectural decision changes that boundary.

## Consequences

- Cross-context boundaries remain explicit inside one deployable application.
- Context internals must not become a shared global model.
- Distribution is deferred until evidence justifies it.
