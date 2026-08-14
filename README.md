# Noema

Local cognitive agent runtime with persistent memory, emotional modeling, multi-LLM intelligence and autonomous capability evolution.

Noema is a local-first runtime intended to host a persistent cognitive agent. The agent is not an LLM: identity, state, memory, cognition, goals, and autonomy belong to the runtime, while model providers are interchangeable cognitive resources.

The V1 is a modular monolith organized by bounded context and protected by ports-and-adapters boundaries. Domain code remains independent from frameworks and infrastructure.

## Status

### Implemented

- M0 project foundation using Python 3.13, `uv`, and a `src` layout
- Official bounded-context package boundaries
- Minimal bootstrap command
- Initial automated domain dependency rule
- Pytest, Ruff, and mypy configuration

### Planned

- Cognitive Runtime components defined by the frozen COGNITION V1 architecture
- Persistent memory and emotional modeling
- Interchangeable model-provider adapters
- Metacognition, autonomy, and capability evolution

Planned items are architectural direction, not currently available functionality.

## Development

Install Python 3.13 and [`uv`](https://docs.astral.sh/uv/), then synchronize the environment:

```console
uv sync
```

Run the bootstrap command:

```console
uv run noema
```

Run all checks:

```console
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
```

Architectural decisions are recorded in [`docs/architecture/adr`](docs/architecture/adr).
