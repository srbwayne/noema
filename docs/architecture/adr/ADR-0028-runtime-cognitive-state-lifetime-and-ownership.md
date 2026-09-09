# ADR-0028: Runtime Cognitive State Lifetime and Ownership

- Status: Accepted
- Date: 2026-09-08

## Context

`CognitiveWorkspace` and `SituationModel` already exist as immutable, versioned snapshots (`@dataclass(frozen=True, slots=True, kw_only=True)`, each with an incrementing `version: int` field starting at `0`). Their state-changing behavior — `CognitiveWorkspace.add_item`/`remove_item`/`set_focus`/`clear_focus` and `SituationModel.apply` — never mutates in place; each returns a new replacement snapshot via `dataclasses.replace`, with `version` incremented and the snapshot's own logical identifier (`workspace_id`/`situation_id`) preserved unchanged.

No canonical runtime owner currently retains either snapshot. No production code anywhere in the repository constructs a `CognitiveWorkspace` or `SituationModel` outside their own module and test fixtures, and no production code reads `.version` from either live snapshot to produce runtime observation data.

Correspondingly, no production `ContextStamp` producer currently exists: nothing in `src/` constructs a `ContextStamp`, so nothing currently observes real `workspace_version`/`situation_version` values from a live snapshot.

ADR-0027 requires `workspace_version` and `situation_version` to represent an observed version — these two fields are `int`-only and observed-only by that decision's own asymmetric carrier typing (`SCOPE_A`); they are not eligible for the `ContextVersionMarker.UNMATERIALIZED` marker available to `identity_version`/`goal_version`/`policy_version`. A `ContextStamp` can therefore only be honestly constructed once real Workspace/Situation versions are actually observable.

The first DIRECT runtime composition (Reasoning → ModelExecutionEngine → Ollama) therefore needs explicit lifecycle and ownership semantics for `CognitiveWorkspace`/`SituationModel` before context composition can honestly construct a `ContextStamp`. This ADR resolves that semantic gap. It does not resolve where the composition root that wires such an owner will live — that question (`COMPOSITION_ROOT_PLACEMENT`) remains open and unaddressed here.

## Decision

### Continuity

```text
RUNTIME_COGNITIVE_STATE_CONTINUITY = RUNTIME_INSTANCE_CONTINUITY
```

The logical current Workspace and Situation survive across cognitive operations performed by one live Noema runtime instance.

`RUNTIME_INSTANCE_CONTINUITY != PROCESS_GLOBAL_CONTINUITY` — this decision does not couple state lifetime to the hosting OS process. A process may host more than one runtime instance (for example, test isolation or future embedding), and this decision does not forbid that.

State survival after the runtime instance is destroyed and a new one recreated is `NOT_REQUIRED_BY_THIS_DECISION`.

### Ownership cardinality

```text
RUNTIME_COGNITIVE_STATE_OWNER_CARDINALITY = ONE_LOGICAL_OWNER_FOR_BOTH_SNAPSHOTS
```

One lifecycle authority is the canonical source of both the current `CognitiveWorkspace` and the current `SituationModel`. This decision does not name a concrete class, package, or layer for that authority.

### Owner lifetime

```text
RUNTIME_COGNITIVE_STATE_OWNER_LIFETIME = RUNTIME_INSTANCE
```

The owner's lifetime matches the runtime instance's lifetime, not the hosting process's lifetime.

### Replacement authority

```text
RUNTIME_COGNITIVE_STATE_REPLACEMENT_AUTHORITY = OWNER_RECEIVES_AND_RETAINS_REPLACEMENT
```

Domain snapshots remain immutable. State transitions on `CognitiveWorkspace`/`SituationModel` continue to produce new replacement snapshots exactly as they do today; this decision adds no mutation to either type. The lifecycle authority is the one that receives each replacement snapshot and makes it the new canonical snapshot.

### Observation boundary

```text
CONTEXT_STAMP_RUNTIME_OBSERVATION_BOUNDARY = BEFORE_CONTEXT_REQUEST_ASSEMBLY
```

`workspace_version` and `situation_version` are observed from the canonical snapshots before construction of the `ContextRequest` that will contain the resulting `ContextStamp` (`ContextRequest.context_stamp` is a mandatory field with no default, so the `ContextStamp` must already exist by the time a `ContextRequest` is built).

This decision does not state that observation happens "at operation start." Whether `ContextStamp` is bound to any single "cognitive operation" concept remains unresolved and is not established by this ADR.

### Observation correlation

```text
CONTEXT_STAMP_WORKSPACE_SITUATION_OBSERVATION = SAME_LOGICAL_OBSERVATION_EVENT
```

The two canonical versions describe one coherent logical observation used to construct one `ContextStamp` — not two independently-timed reads.

`SAME_LOGICAL_OBSERVATION_EVENT != LOCK_BASED_ATOMICITY`. This is a semantic commitment, not a concurrency mechanism. A concurrency mechanism is `NOT_REQUIRED_BY_FIRST_DIRECT_RUNTIME`: nothing in the current first DIRECT runtime scope requires concurrent operations against shared cognitive state.

### Initialization authority

```text
RUNTIME_COGNITIVE_STATE_INITIALIZATION_AUTHORITY = OWNER_RECEIVES_ALREADY_VALID_INITIAL_SNAPSHOTS
```

The lifecycle authority starts from valid `CognitiveWorkspace` and `SituationModel` instances supplied to it. This ADR does not choose `WorkspaceBudget` values, initial Workspace items, initial focus, initial Situation entries, a restore policy, or a persistence source.

## Non-decisions

This ADR explicitly defers:

- the concrete lifecycle-owner class;
- its package/layer placement (`domain`/`application`/`infrastructure`/other);
- composition-root placement (`main.py`, a dedicated bootstrap module, or any other location);
- how the owner is wired into the runtime;
- Workspace initialization policy, `WorkspaceBudget` source and values;
- Situation initialization policy;
- durable persistence, restart recovery, database or filesystem storage, event sourcing;
- concurrency mechanisms — locks, transactions, compare-and-swap;
- session semantics and conversation semantics (no such concept currently exists in accepted authority);
- Identity/Goal/Policy ownership (unaffected — those dimensions remain `ContextVersionMarker.UNMATERIALIZED`-eligible per ADR-0027 and are out of this ADR's scope);
- Cognitive Coordinator involvement;
- Model Registry involvement.

## Relationship to ADR-0005

```text
THIS_DECISION_MODIFIES_FROZEN_COGNITION_COMPONENT_SET = NO
THIS_DECISION_MODIFIES_COGNITIVE_WORKSPACE_BOUNDARY = NO
THIS_DECISION_MODIFIES_SITUATION_MODEL_BOUNDARY = NO
THIS_DECISION_INTRODUCES_NEW_FROZEN_COGNITION_COMPONENT = NO
```

`CognitiveWorkspace` and `SituationModel` keep exactly the shape, fields, and methods ADR-0005 already froze. ADR-0028 records runtime lifecycle semantics around those existing frozen components; it does not add another cognitive-processing component to ADR-0005's frozen set, and no other named frozen component is made to own them.

## Relationship to ADR-0027

ADR-0027 establishes what `ContextStamp` can represent. ADR-0028 establishes how the materialized Workspace/Situation versions become honestly observable runtime values for that representation. Neither ADR supersedes the other.

## Relationship to B3 (composition-root placement)

```text
COMPOSITION_ROOT_PLACEMENT = UNRESOLVED
```

ADR-0028 determines what lifecycle behavior the eventual composition root must place and wire — not where that wiring belongs. That placement decision is deferred to a separate, later decision.

## Consequences

Positive:

- a canonical Workspace/Situation pair exists per runtime instance;
- version history can continue across runtime-instance operations rather than resetting per call;
- immutable replacement snapshots have explicit retention authority instead of being silently discarded;
- honest `ContextStamp` construction becomes semantically possible;
- the eventual composition-root decision receives sufficient lifecycle information to proceed once made.

Constraints:

- one runtime instance must not silently share canonical state with another;
- process-global singleton semantics are not implied by this decision;
- a `ContextStamp` used by a given `ContextRequest` must use the pre-request canonical observation, not a later one.

Deferred:

- actual implementation of the lifecycle authority;
- composition-root placement;
- initial-state construction policy;
- persistence;
- concurrency.
