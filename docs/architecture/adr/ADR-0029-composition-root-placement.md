# ADR-0029: Composition Root Placement

- Status: Accepted
- Date: 2026-09-09

> Status `Accepted` records approval of the architectural decision by its decision review. Repository
> `main` authority is established by repository history and merge state, independently of this status
> label; it is `NO` until this record is merged.

## Context

Noema V1 is a modular monolith organized by bounded context (ADR-0001), integrating external
technology exclusively through ports and adapters (ADR-0003).

The first DIRECT runtime composition (Reasoning → `ModelExecutionEngine` → Ollama) requires a
production object graph that spans at least two bounded contexts — `cognition` and `model_router` —
and that binds application-owned port contracts to concrete infrastructure adapters, including a
provider SDK client for the Ollama adapter.

The current repository state:

- `src/noema/main.py` is the CLI/process entrypoint (`pyproject.toml` `[project.scripts]`
  `noema = "noema.main:main"`). It prints runtime status and performs no object-graph assembly.
- No production composition root exists anywhere in `src/`. No production code constructs the
  reasoning/model-execution graph; the components are exercised only by tests with test doubles.
- `presentation/` contains no code and, by AGENTS.md, calls application services rather than domain
  internals or infrastructure directly.
- The architecture dependency test (`tests/architecture/test_domain_dependencies.py`) enforces
  per-package allow-lists: `cognition/application` may not import `model_router` or any
  infrastructure; `cognition/infrastructure` may not import `model_router/infrastructure` or a
  provider SDK; `model_router/infrastructure` may not import `cognition`. No bounded-context-internal
  layer may legally assemble the full first-runtime graph.

ADR-0028 established the runtime-instance lifetime and ownership semantics for `CognitiveWorkspace`
and `SituationModel`, and explicitly deferred composition-root placement
(`COMPOSITION_ROOT_PLACEMENT = UNRESOLVED`). ADR-0027's `ContextStamp` representation is settled
(`B1`), and ADR-0028's lifecycle semantics are accepted repository-main authority (`B2`); neither is
reopened here. The remaining open question is strictly *where* the outer runtime object graph is
assembled and runtime-instance scoped. This ADR resolves that question (`B3`).

## Decision

### Core placement

```text
COMPOSITION_ROOT_PLACEMENT = TOP_LEVEL_DEDICATED_BOOTSTRAP_MODULE
COMPOSITION_ROOT_PATH = src/noema/bootstrap.py
```

The production object graph for one Noema runtime instance is assembled at a dedicated top-level
module, `src/noema/bootstrap.py`, that sits outside all bounded-context internals.

### Bounded-context ownership

```text
COMPOSITION_ROOT_BOUNDED_CONTEXT_OWNERSHIP = NONE
```

`cognition` does not own whole-runtime composition. `model_router` does not own whole-runtime
composition. `presentation` does not own whole-runtime composition. The bootstrap module is an outer
assembly edge, not a new bounded context and not another deployable service.

### `main.py` role

```text
MAIN_PY_ROLE = THIN_PROCESS_ENTRYPOINT
PROCESS_ENTRYPOINT != COMPOSITION_ROOT_IMPLEMENTATION
```

`noema.main:main` remains the CLI/process entrypoint and delegates graph construction to the
composition root:

```text
main.py
    │ delegates graph construction
    ▼
bootstrap.py
```

This ADR does not design CLI parsing or execution flow, and does not fix the concrete
function/class API of the bootstrap module.

### Composition-root responsibilities

```text
COMPOSITION_ROOT_RESPONSIBILITIES = (
    CONSTRUCT_CONCRETE_OBJECT_GRAPH,
    SELECT_CONCRETE_INFRASTRUCTURE_ADAPTERS,
    CONSTRUCT_PROVIDER_CLIENTS_FOR_ADAPTER_WIRING,
    SCOPE_ONE_RUNTIME_INSTANCE_GRAPH,
    RECEIVE_RESOLVED_RUNTIME_CONFIGURATION,
    WIRE_MULTIPLE_BOUNDED_CONTEXT_PUBLIC_OR_APPLICATION_BOUNDARIES
)
```

### Infrastructure visibility

```text
COMPOSITION_ROOT_MAY_IMPORT_INFRASTRUCTURE = YES
```

This permission belongs to the outer composition edge only. It does not relax:

```text
domain       -> infrastructure   (prohibited)
application  -> infrastructure   (prohibited)
presentation -> infrastructure   (prohibited)
```

### Provider-SDK construction

The outer composition root may instantiate provider SDK clients when required to construct concrete
infrastructure adapters. This is composition only. It does not authorize provider behavior in
`domain` or `application`, and does not authorize provider-specific decision policy inside the
bootstrap module.

### Cross-context wiring

```text
COMPOSITION_ROOT_MAY_WIRE_MULTIPLE_BOUNDED_CONTEXTS = YES
```

Outer-edge wiring is not one bounded context importing another context's internals. The composition
root exists outside bounded-context internals precisely to preserve that distinction.

### Runtime graph cardinality

```text
ONE_COMPOSITION_BUILD = ONE_RUNTIME_INSTANCE_GRAPH
CAN_BUILD_MULTIPLE_DISTINCT_RUNTIME_GRAPHS = YES
```

The decision must support more than one runtime instance within a single process (for example, test
isolation or future embedding), consistent with ADR-0028's
`RUNTIME_INSTANCE_CONTINUITY != PROCESS_GLOBAL_CONTINUITY`.

### Global-state firewall

```text
PROCESS_GLOBAL_SINGLETON_ALLOWED = NO
PROCESS_GLOBAL_COGNITIVE_STATE = FORBIDDEN
```

No module-level canonical `CognitiveWorkspace`/`SituationModel` owner is implied or permitted by this
composition decision.

### Runtime-logic firewall

```text
BUILD_OBJECT_GRAPH != RUN_COGNITIVE_OPERATION
COMPOSITION_ROOT_OWNS_COGNITIVE_REASONING_LOGIC = NO
```

The bootstrap module must not contain `ReasoningEngine` behavior, `ContextComposer` selection logic,
domain invariants, model-selection policy, or cognitive coordination.

### Dependency injection framework

```text
DI_FRAMEWORK = NOT_REQUIRED
```

Manual Python composition is sufficient for the first DIRECT runtime. This does not permanently
prohibit a future DI mechanism; it records that the current architecture does not require one.

### Presentation normalization

```text
BOOTSTRAP_REUSABLE_BY_MULTIPLE_PROCESS_OR_TRANSPORT_ENTRYPOINTS = YES
PRESENTATION_REMAINS_APPLICATION_FACING = YES
PRESENTATION_PACKAGE_IMPORTS_BOOTSTRAP = NOT_REQUIRED
```

The CLI process entrypoint may delegate to the bootstrap module, and future process or transport
entrypoints may reuse the same top-level composition path without duplicating graph assembly:

```text
process/transport entrypoint A ─┐
                                ├──► bootstrap composition root
process/transport entrypoint B ─┘
```

This is conceptual. This ADR does not create new entrypoints, does not authorize `presentation/**`
to become an outer composition layer, and does not establish
`presentation -> bootstrap -> infrastructure` as a required dependency chain. The existing rule that
presentation calls application boundaries remains intact.

## Relationship to ADR-0001

The bootstrap module remains inside the single deployable modular monolith. It is not another
service and does not become a bounded context. Cross-context composition happens at the outer
assembly edge, leaving each context's internal model and contracts unchanged.

## Relationship to ADR-0003

Application-owned ports remain inward-facing contracts and concrete infrastructure adapters remain
replaceable. The bootstrap module binds those contracts to concrete adapters. This binding
responsibility does not permit any inward layer to import outward dependencies.

## Relationship to ADR-0005

```text
THIS_DECISION_MODIFIES_FROZEN_COGNITION_COMPONENT_SET = NO
THIS_DECISION_INTRODUCES_NEW_FROZEN_COGNITION_COMPONENT = NO
```

A top-level wiring module is not a cognitive-processing component. ADR-0029 records where the runtime
object graph is assembled; it does not add a component to ADR-0005's frozen set.

## Relationship to ADR-0028

```text
ADR0029_SUPERSEDES_ADR0028 = NO
ADR0028_SUPERSEDES_ADR0029 = NO
```

ADR-0028 establishes the runtime-instance lifetime and ownership semantics that the runtime must
realize. ADR-0029 establishes where the object graph that wires those semantics is assembled.

```text
LIFECYCLE_OWNER_CONCRETE_DESIGN = DEFERRED
B3_SELECTS_LIFECYCLE_OWNER_PACKAGE = NO
LIFECYCLE_OWNER_BEHAVIOR_IMPLEMENTATION != LIFECYCLE_OWNER_RUNTIME_WIRING
```

ADR-0029 determines the outer wiring location only. It does not choose the lifecycle-owner class,
its name, its package/layer, its internal methods, or its storage representation, and it completes
neither the owner's behavior implementation nor its runtime wiring.

## Relationship to ADR-0027

`B1` (`ContextStamp` unmaterialized-state representation) is unchanged and not reopened.

```text
B3_SELECTS_CONTEXTSTAMP_PRODUCER_CLASS = NO
```

ADR-0028's `CONTEXT_STAMP_RUNTIME_OBSERVATION_BOUNDARY = BEFORE_CONTEXT_REQUEST_ASSEMBLY` and
`CONTEXT_STAMP_WORKSPACE_SITUATION_OBSERVATION = SAME_LOGICAL_OBSERVATION_EVENT` are preserved. This
ADR does not choose the runtime or application object that performs that flow.

## Relationship to B2 authority

```text
B2_SEMANTIC_AUTHORITY_COMPLETE = YES
B2_DECISION_REPOSITORY_MAIN_AUTHORITY = YES
B2_DECISION_AUTHORITY_BLOCKER_EXISTS = NO
B2_IMPLEMENTATION_COMPLETE = NO
B2_REOPENED = NO
```

B2 (ADR-0028) is repository-main authority and is not reopened. ADR-0029 does not modify any of
ADR-0028's seven decisions.

## Cognitive Coordinator

```text
COGNITIVE_COORDINATOR_REQUIRED_FOR_FIRST_DIRECT_RUNTIME = NO
COMPOSITION_ROOT != COGNITIVE_COORDINATOR
```

## Architecture-test enforcement

```text
ARCHITECTURE_TEST_ENFORCEMENT_FOR_BOOTSTRAP_BOUNDARY = DEFERRED_TO_IMPLEMENTATION_REVIEW
```

No architecture test is introduced or made mandatory by this ADR. Potential future constraints, to
be evaluated when `bootstrap.py` is implemented, may include: bounded-context internals must not
depend on `noema.bootstrap`; domain code must never import bootstrap; presentation must not become
the composition root.

## Non-decisions

This ADR explicitly defers:

- the bootstrap module's concrete function/class API;
- the runtime graph return type;
- the lifecycle-owner concrete design;
- the lifecycle-owner package/layer;
- Workspace/Situation initialization policy;
- `WorkspaceBudget` source and values;
- initial Workspace items, initial focus, empty vs. seeded Situation, restore source;
- the `ContextStamp` producer class;
- the `ContextRequest` assembler class;
- the `ReasoningRequest` assembler class;
- model runtime configuration values — model name, Ollama host, candidate `ModelResource` set,
  selection-policy values;
- durable persistence, restart recovery, storage;
- concurrency mechanisms;
- CLI parsing;
- HTTP/API design;
- new presentation adapters;
- Cognitive Coordinator involvement;
- Model Registry involvement.

```text
INITIAL_SNAPSHOT_POLICY = DEFERRED
MODEL_RUNTIME_CONFIGURATION_VALUES = DEFERRED
```

The composition root is an integration/supply site for resolved configuration, not the policy
authority for those values.

### Scope firewall

This ADR does not name or introduce `RuntimeState`, `CognitiveRuntimeState`,
`RuntimeLifecycleOwner`, `StateManager`, `WorkspaceStore`, `SituationStore`, `NoemaRuntime`, or any
other concrete owner/runtime type. It references only generic concepts: the runtime-instance graph,
the lifecycle owner, and the composition root.

## Consequences

Positive:

- one context-neutral location owns runtime graph assembly;
- bounded contexts no longer need to own cross-context wiring;
- `main.py` stays small;
- concrete infrastructure visibility is isolated at the outer edge;
- repeated composition can yield independent runtime-instance graphs;
- ADR-0028's lifecycle semantics now have a defined future wiring location;
- future process/transport entrypoints can reuse one composition mechanism.

Constraints:

- no process-global cognitive-state singleton;
- the bootstrap module may contain wiring, not domain or application behavior;
- bounded contexts must not import the bootstrap module;
- the presentation boundary remains application-facing.

Deferred:

- the actual `src/noema/bootstrap.py` implementation;
- lifecycle-owner realization;
- initial cognitive-snapshot configuration;
- the `ContextStamp`/`ContextRequest` runtime flow;
- model runtime configuration.
