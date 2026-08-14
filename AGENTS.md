# Noema Development Guide

## Purpose and architectural invariants

Noema is a local cognitive agent runtime. **Agent != LLM**: agent identity, memory, cognitive and emotional state, goals, autonomy, metacognition, and capabilities belong to the runtime and must remain independent of every model provider. LLMs are interchangeable cognitive resources.

V1 is a **Modular Monolith** using **Clean/Hexagonal Architecture**, organized by bounded context. The official contexts are `identity`, `cognition`, `memory`, `emotions`, `model_router`, `metacognition`, `autonomy`, and `self_improvement`. External capabilities belong in `capabilities`; public boundaries belong in `presentation`; only proven cross-context abstractions belong in `shared`.

Do not turn `shared` into a generic utilities package. Do not introduce abstractions before a concrete use demonstrates that they are shared.

## Package structure

When implementation requires it, a bounded context may contain:

```text
<bounded_context>/
├── domain/
├── application/
├── ports/
└── infrastructure/
```

Create only layers that contain real code. Do not add empty directories or speculative interfaces.

## Dependency rules

1. Domain code is framework-independent and never depends on infrastructure.
2. Domain code must not import FastAPI, SQLAlchemy, Pydantic, provider SDKs, database adapters, HTTP clients, or agent frameworks.
3. Application code may depend on its domain and ports.
4. Infrastructure implements ports and points inward; it is never imported by domain code.
5. Presentation calls application services rather than domain internals or infrastructure directly.
6. Bounded contexts avoid direct dependencies on one another's internals.
7. Context integration uses explicit public contracts.
8. Prefer absolute imports from `noema`; relative imports are acceptable only within a tightly cohesive package when they improve clarity.
9. Never manipulate `sys.path` to make imports work.

The initial AST architecture test enforces the prohibited domain imports. Extend it when a new external dependency or architectural rule is approved.

## Python conventions

- Target Python `>=3.13,<3.14` and use `uv` for project management.
- Use strong, explicit typing and keep mypy strict checks passing.
- Prefer dataclasses for domain models, frozen dataclasses for value objects, and `Enum` for finite states.
- Avoid `Any` and `dict[str, Any]`; model meaningful data with explicit types.
- Do not base domain entities on Pydantic. Boundary code may use Pydantic only after an explicit dependency decision.
- Favor async APIs where I/O or concurrency warrants them; do not make pure domain behavior async without reason.
- Keep modules focused and public APIs deliberate.

## Testing policy

- Put focused behavior tests in `tests/unit`, adapter/composition tests in `tests/integration`, and dependency-boundary tests in `tests/architecture`.
- Test observable behavior and architecture rules; avoid tests coupled to private implementation details.
- Every bug fix receives a regression test when practical.
- Keep tests deterministic, isolated, offline, and free of external service requirements unless an approved integration test explicitly requires otherwise.

Before completing every task, run and fix all failures from:

```console
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
```

Run `uv run noema` when entry-point behavior is affected.

## Scope and architectural governance

- Do not introduce LangChain, LangGraph, CrewAI, AutoGen, or another agent framework without an explicit architectural decision. They are not part of the V1 core.
- COGNITION V1 is frozen. Never silently alter its structure; structural changes require an explicit ADR before implementation. See ADR-0005.
- Do not implement functionality outside the stated scope of the current task, even when it appears adjacent or useful.
- Preserve the modular-monolith boundary and use ports and adapters for every external technology.
- Do not couple the runtime to an avatar application. Avatars are separate clients of public Noema interfaces.
