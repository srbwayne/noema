# ADR-0031: End-to-End Prior-Task Context Runtime Integration

- Status: Accepted
- Date: 2026-09-17

## Context

ADR-0030 made prior canonical `TASK` entries into constructible, honestly-classified
`ContextCandidate` values through `PriorTaskContextProjector`, corrected the
context-composition size schema, and introduced `PriorTaskContextMaterializer` -- but
explicitly deferred runtime integration:

```text
CONTEXT_COMPOSER_RUNTIME_INTEGRATION = NO
NONEMPTY_CONTEXT_PACKAGE_RUNTIME_USE = NO
MODEL_CONTEXT_MATERIALIZATION = NO
DIRECT_REASONING_OPERATION_RUNTIME_WIRING = NOT_CHANGED
```

Until this ADR, no production code path constructed `PriorTaskContextProjector`,
`ContextComposer`, `ContextCompositionPolicy`, or `PriorTaskContextMaterializer`;
`ContextRequestAssembler` observed canonical state itself;
`assemble_direct_reasoning_request` always wrapped an empty `ContextPackage`;
`ModelReasoningExecutor` rejected any non-empty context package; and `_process.py`
carried no prior-TASK activation/configuration transport.

This ADR closes that integration gap end to end: canonical runtime state now flows
through prior-TASK projection, context composition, `ReasoningRequest` assembly, and
model-input materialization, entirely behind an optional, backward-compatible
configuration flag.

## Decision

### Single-observation ownership transferred to `ContextPackagePreparer`

A new `cognition.application` component, `ContextPackagePreparer`, becomes the single
production owner of per-operation canonical-state observation
(`ADR-0028: SNAPSHOT_COHERENCE_DESIGN = B`). It calls
`CognitiveStateOwner.current_snapshots()` exactly once per `prepare()` call and threads
the exact returned `workspace`/`situation` pair into both `ContextRequestAssembler.assemble`
(for the `ContextStamp`) and, when enabled, `PriorTaskContextProjector.project` (for
candidate projection) -- guaranteeing both observe the same canonical state.

Responsibility, exactly:

```text
single canonical snapshot observation
+ prior-TASK projection
+ effective required-slice activation
+ ContextRequest assembly from the SAME snapshots
+ ContextComposer invocation
-> ContextPackage
```

It registers no current content, ingests no current TASK, materializes no model input,
executes no reasoning, calls no provider/model, persists nothing, scores no relevance,
and chooses no `CognitiveBudget`.

### `ContextRequestAssembler` becomes snapshot-parameterized

`ContextRequestAssembler` loses its `CognitiveStateOwner` constructor dependency
entirely and now performs zero canonical-state observations. Its `assemble()` accepts
explicit `workspace: CognitiveWorkspace` and `situation: SituationModel` parameters,
validated with `TypeError`, alongside the existing `ContextRequest` policy fields.

### Activation policy: `REQUIRED_WHEN_PRIOR_EXISTS`

```text
policy disabled                           -> prior TASK context never activated
policy enabled + zero projected candidates -> TASK not added to required_slice_types
policy enabled + >=1 projected candidate   -> TASK becomes required (appended once,
                                               never duplicated, never reordering the
                                               caller's existing required tuple)
```

Candidate existence alone never creates consumer authority independent of this rule --
it exactly gates whether TASK is required, nothing else.

### Optional, backward-compatible `[direct.context]` transport

`_process.py`'s strict `direct` table schema gains one new *optional* subtable,
`context`, alongside the existing required `policy` and `budget`. Its absence carries
exactly the same semantic result as an explicit `prior_task_context_enabled = false`:
disabled, no `ContextCompositionPolicy` constructed. Existing configuration files
without `[direct.context]` remain valid and produce disabled behavior unchanged.

Exact shapes:

```toml
# disabled (explicit)
[direct.context]
prior_task_context_enabled = false
# minimum_relevance / max_slices must NOT be supplied

# enabled
[direct.context]
prior_task_context_enabled = true
minimum_relevance = 0.30   # float, required
max_slices = 3             # int, required
```

Supplying `minimum_relevance`/`max_slices` while disabled is a configuration error --
no numeric policy value is ever silently ignored. Transport types are strict:
`prior_task_context_enabled` must be an exact `bool` (not `0`/`1`/`"true"`);
`minimum_relevance` must be an exact `float` (not `bool`/`int`/`str`); `max_slices`
must be a strict `int` (not `bool`), reusing the existing integer-leaf helper.
Semantic validation (finite `minimum_relevance` in `[0.0, 1.0]`, positive `max_slices`)
remains owned by `ContextCompositionPolicy.__post_init__` -- the transport layer only
converts types.

These names are chosen to be unambiguous against the two already-existing,
differently-scoped size/budget concepts: `ContextRequest.max_total_content_size`
(`direct.policy.context_max_content_size`) and `CognitiveBudget.max_tokens`
(`direct.budget.max_tokens`).

### `ContextCompositionPolicy` built once, by process configuration resolution

Exactly one `ContextCompositionPolicy` is constructed -- inside `_process.py`'s
configuration resolution, the same layer that already converts transport configuration
into `WorkspaceBudget`, `CognitiveBudget`, and `ModelResourceCapabilities` -- and passed
by reference into `open_direct_runtime`. `bootstrap.py` never reconstructs another one;
runtime binding remains one-policy-per-runtime, bound into one `ContextComposer` for the
runtime instance's lifetime.

### Shared `RuntimeContentReferenceAuthority` and `CognitiveStateOwner`

`bootstrap.open_direct_runtime` constructs exactly one `RuntimeContentReferenceAuthority`,
shared by `DirectReasoningOperation`'s current-content registration,
`PriorTaskContextProjector`, and `PriorTaskContextMaterializer`; and exactly one
`CognitiveStateOwner`, shared by `CanonicalInputIngestor` and `ContextPackagePreparer`.
No independently-constructed authority or state owner exists anywhere in the graph.

### `ContextPackage` handoff into `ReasoningRequest`

`assemble_direct_reasoning_request` is refactored from accepting a `context_request:
ContextRequest` (and always wrapping it in a freshly-constructed empty `ContextPackage`)
to accepting `context: ContextPackage` directly, retaining the exact supplied object by
reference. It constructs no `ContextPackage`, inspects no slice, and composes no context.

### `ReasoningInputMaterializer` port (seam D2)

A new `Protocol` in `cognition.ports`, `ReasoningInputMaterializer`, defines
`materialize(self, request: ReasoningRequest) -> str`. Its only Noema domain dependency
is `noema.cognition.domain.reasoning` -- it imports neither `ContextPackage`/`ContextSlice`
(from `cognition.domain.context_composition`) nor any `cognition.application`/
`cognition.infrastructure`/`model_router` module. This shape is forced by
`tests/architecture/test_domain_dependencies.py::test_cognition_ports_has_only_allowed_noema_dependencies`,
which permits `cognition.ports` to depend only on `domain.planning`, `domain.reasoning`,
and `cognition.ports` itself -- never `domain.context_composition` directly. Taking the
whole `ReasoningRequest` (already legitimately typed from `domain.reasoning`) rather than
`problem_statement`/`context` as separate parameters is what keeps this port within that
allow-list without any relaxation.

### `PriorTaskReasoningInputMaterializer` adapter

A concrete `cognition.application` adapter, `PriorTaskReasoningInputMaterializer`,
realizes the port by delegating exactly to a bound `PriorTaskContextMaterializer`:
`materialize(problem_statement=request.problem_statement, context=request.context)`. No
other logic, policy, selection, mutation, or provider knowledge.

### `ModelReasoningExecutor` materializes through the port

`ModelReasoningExecutor` gains a third constructor dependency,
`input_materializer: ReasoningInputMaterializer`, and calls
`input_materializer.materialize(request)` exactly once, before model execution, to
obtain `input_text`. The prior "non-empty context unsupported" rejection is removed.
`ModelReasoningExecutor` never imports `PriorTaskContextMaterializer`,
`PriorTaskReasoningInputMaterializer`, or any `cognition.application` module.

### Empty-context backward compatibility

`PriorTaskContextMaterializer.materialize` already returns `problem_statement` exactly,
unchanged, when `context.slices == ()`. Combined with the disabled path and the
enabled-but-no-candidates path both returning an empty `ContextPackage`, the first
first-DIRECT operation's model input remains bit-for-bit identical to pre-integration
behavior in every case that previously existed.

### Failure / rollback semantics

Materialization failures (`RuntimeContentReferenceNotFoundError`,
`UnsupportedPriorTaskContextSliceError`, `PriorTaskContextMaterializationCoherenceError`,
or a broken-contract `TypeError`/`ValueError`) occur before any model/provider call and
propagate unchanged -- never translated to `ReasoningExecutionError`. Provider/model
errors (`AmbiguousModelSelectionError`, `NoEligibleModelResourceError`,
`ModelExecutionError`) continue to translate to `ReasoningExecutionError` exactly as
before. Context-preparation failures (`ContextCompositionUnsatisfiedError`,
projector-propagated errors, `ContextRequest` construction errors) occur strictly after
current-content registration and canonical-task ingestion and propagate unchanged with
no rollback -- a successful registration/ingestion is never deleted, replaced, or
compensated by a later failure.

### Same-runtime-only prior-TASK continuity

Within one runtime instance, sequential first-DIRECT operations share one
`CognitiveStateOwner` and one `RuntimeContentReferenceAuthority`, so a later operation
may use an earlier operation's TASK input as prior context. No durable memory, no
cross-process history, no model-response history, no database, no vector store, and no
semantic retrieval are introduced. Two independently constructed runtime instances share
no state.

### `model_router` unchanged

`ModelExecutionEngine.execute(selection_request, input_text)` already accepted a plain
`str`; `cognition.infrastructure` hands `model_router` one already-materialized string.
No change to `ModelExecutionEngine`, `OllamaModelExecutor`, or any `model_router` schema
was required.

### Budget/token relationship remains unresolved

`ContextRequest.max_total_content_size` continues to bound raw Unicode code-point count;
it makes no guarantee of fitting within `CognitiveBudget.max_tokens` or any provider's
context window. This ADR does not add a tokenizer, estimate provider tokens, or compare
materialized text length against `CognitiveBudget.max_tokens`.

## Architecture impact

No architecture allow-list relaxation was required. `cognition.ports`' new
`ReasoningInputMaterializer` protocol depends only on `domain.reasoning`, already
permitted. `cognition.infrastructure`'s new dependency on it is already permitted
(`cognition.infrastructure -> cognition.ports` was already allowed). No new dependency
from `cognition.infrastructure` to `cognition.application` or
`cognition.domain.context_composition` was introduced.

## Non-decisions

This ADR does not alter `PriorTaskContextProjector`, `ContextComposer`,
`PriorTaskContextMaterializer`, `ContextCandidate`, `ContextSlice`, or `ContextPackage`
semantics (ADR-0030's classification, ordering, relevance, and coverage-bound rules are
unchanged), does not assign a milestone identifier, and does not resolve the
content-size/token-budget relationship.

## Consequences

Positive:

- prior canonical `TASK` entries are now usable as real model context in the
  first-DIRECT runtime, behind an explicit, backward-compatible opt-in;
- canonical-state observation is now owned by exactly one component per context
  preparation, closing the two-observation risk ADR-0030 flagged as a future
  integration requirement;
- the materialization seam keeps `cognition.infrastructure` fully ignorant of
  `cognition.application` and of prior-TASK rendering semantics.

Deferred:

- the `ContextRequest.max_total_content_size` / `CognitiveBudget.max_tokens`
  relationship;
- relevance scoring beyond ADR-0030's frozen unknown-relevance eligibility policy;
- goal, mode-arbitration, and planning integration.
