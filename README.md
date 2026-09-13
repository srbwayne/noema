# Noema

Local cognitive agent runtime with persistent memory, emotional modeling, multi-LLM intelligence and autonomous capability evolution.

Noema is a local-first runtime intended to host a persistent cognitive agent. The agent is not an LLM: identity, state, memory, cognition, goals, and autonomy belong to the runtime, while model providers are interchangeable cognitive resources.

The V1 is a modular monolith organized by bounded context and protected by ports-and-adapters boundaries. Domain code remains independent from frameworks and infrastructure.

## Status

### Implemented

- M0 project foundation using Python 3.13, `uv`, and a `src` layout
- Official bounded-context package boundaries
- The first-DIRECT reasoning object graph (`src/noema/bootstrap.py`)
- A one-shot first-DIRECT CLI process entrypoint (`uv run noema`, below)
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

Run one first-DIRECT reasoning operation:

```console
uv run noema --config PATH "PROBLEM"
```

- `--config` is required: an explicit path to a first-DIRECT process configuration TOML file (see
  [Configuration](#configuration) below). There is no default path, no environment-variable
  fallback, and no configuration search.
- `PROBLEM` is one required positional argument: the problem statement for this one reasoning
  operation.
- The command performs exactly one reasoning operation against the configured Ollama endpoint and
  model, then exits. Noema does not auto-discover or auto-pull models -- the Ollama endpoint and
  model named in the configuration must already be available.
- Exit code `0` means a valid reasoning outcome was produced (regardless of its semantic
  completeness); `1` means the underlying model execution failed technically; `2` means the CLI
  invocation, the configuration file, or the resolved configuration values were invalid.

Run `uv run noema --help` for the exact CLI usage text.

### Configuration

The configuration file is a TOML document with exactly five tables and 20 required keys. **No
process configuration value has a repository default -- every key below is required**, and any
missing key, unknown key, or unknown table is a configuration error. The values shown here are
placeholders illustrating shape and type only, not recommended or default values:

```toml
[runtime.workspace]
max_active_items = <integer>
max_working_items = <integer>
max_peripheral_items = <integer>

[runtime.ollama]
host = "<ollama endpoint URL>"

[runtime.model]
resource_ref = "<opaque resource identifier>"
provider_ref = "<opaque provider identifier>"
model_ref = "<opaque model identifier>"
capabilities = ["<capability>", ...]  # any of: text_generation | structured_output | tool_calling

[direct.policy]
role = "<string>"
mode = "<mode>"                    # one of: reflex | fast | deliberate | deep
max_sensitivity = "<sensitivity>"  # one of: public | internal | private | secret
minimum_trust = "<trust level>"    # one of: trusted | unverified | untrusted
context_max_tokens = <integer>

[direct.budget]
max_time_ms = <integer>       # milliseconds
max_steps = <integer>
max_llm_calls = <integer>
max_tool_calls = <integer>
max_cost = "<decimal string>"  # e.g. "1.50" -- a string, not a TOML float
max_tokens = <integer>
max_search_depth = <integer>
```

`mode`, `max_sensitivity`, `minimum_trust`, and `capabilities` accept only the exact contract
values listed above (case-sensitive, no aliases). `capabilities` may be an empty list.

Run all checks:

```console
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src
```

Architectural decisions are recorded in [`docs/architecture/adr`](docs/architecture/adr).
