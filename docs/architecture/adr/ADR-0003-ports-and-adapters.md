# ADR-0003: Ports and Adapters

- Status: Accepted
- Date: 2026-08-13

## Context

The runtime will eventually interact with model providers, persistence systems, and external capabilities while keeping its domain stable.

## Decision

External technologies must integrate through ports and adapters.

Application-owned contracts define required behavior. Infrastructure adapters implement those contracts and depend inward toward the application and domain.

## Consequences

- External SDK types do not enter the domain.
- Integrations are replaceable and independently testable.
- Ports are introduced only when an actual integration boundary needs them.
