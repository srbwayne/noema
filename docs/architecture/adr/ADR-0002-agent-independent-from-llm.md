# ADR-0002: Agent Independent from LLM

- Status: Accepted
- Date: 2026-08-13

## Context

Noema uses language models as cognitive resources, but a provider or model must not define the agent itself.

## Decision

Agent identity and cognitive state are independent from model providers.

Provider changes must not replace or redefine the agent's identity, persistent state, goals, or runtime-owned cognitive processes.

## Consequences

- Provider integrations require replaceable adapters.
- Domain models cannot inherit from or depend on provider SDK types.
- The runtime remains meaningful when no model provider is active.
