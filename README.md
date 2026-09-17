# Noema

Local cognitive agent runtime with persistent memory, emotional modeling, multi-LLM intelligence and autonomous capability evolution.

Noema is a local-first runtime intended to host a persistent cognitive agent. The agent is not an LLM: identity, state, memory, cognition, goals, and autonomy belong to the runtime, while model providers are interchangeable cognitive resources.

The V1 is a modular monolith organized by bounded context and protected by ports-and-adapters boundaries. Domain code remains independent from frameworks and infrastructure.

## Status

### Implemented

- M0 project foundation using Python 3.13, `uv`, and a `src` layout
- Official bounded-context package boundaries
- The first-DIRECT reasoning object graph (`src/noema/bootstrap.py`)
- A first-DIRECT CLI process entrypoint supporting one or more sequential
  operations within one runtime invocation (`uv run noema`, below)
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

Run one or more sequential first-DIRECT reasoning operations:

```console
uv run noema --config PATH "PROBLEM" ["PROBLEM" ...]
```

- `--config` is required: an explicit path to a first-DIRECT process configuration TOML file (see
  [Configuration](#configuration) below). There is no default path, no environment-variable
  fallback, and no configuration search.
- `PROBLEM` accepts one or more positional arguments. One problem remains a fully valid
  invocation. Given more than one, the process opens a single runtime instance and executes each
  problem's operation sequentially, in the exact order given, against the configured Ollama
  endpoint and model, then exits. Noema does not auto-discover or auto-pull models -- the Ollama
  endpoint and model named in the configuration must already be available.
- Multiple problems share the same runtime instance and canonical state continuity, but each
  model call still receives only its current problem statement; this does not add
  conversational-history materialization -- no problem observes any earlier problem or response.
- On success, each problem's outcome is rendered in order, separated by exactly one blank line;
  a single problem's output is unchanged from a one-problem invocation. The first raised
  exception aborts the remaining problems immediately: no output is rendered for a failed
  invocation, and problems after the failing one are never attempted.
- Exit code `0` means every attempted operation produced a valid reasoning outcome (regardless of
  its semantic completeness); `1` means an attempted operation's underlying model execution
  failed technically; `2` means the CLI invocation, the configuration file, or the resolved
  configuration values were invalid.

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
context_max_content_size = <integer>

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
