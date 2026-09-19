# ADR-0034: Reasoning Strategy Demand Admission

- Status: Accepted
- Date: 2026-09-18

## Context

`ReasoningStrategy` has ten members, `ReasoningStrategyDemand`/`ReasoningStrategySelector`/
`ReasoningCoordinator`/`ReasoningCoordinationPlan` form a fully mature, already-tested domain
layer for resolving an explicit demand into one (or, via the coordinator, several) required
strategies, yet no production component has ever constructed a `ReasoningStrategyDemand` or
called `ReasoningStrategySelector.select`. Canonical first-DIRECT execution hardcodes
`strategy=ReasoningStrategy.DIRECT` in `assemble_direct_reasoning_request`, unconditionally, on
every call; `ModelReasoningExecutor` supports only `DIRECT` and rejects everything else with
`ReasoningExecutionError`. This is the same class of demonstrated gap ADR-0032/ADR-0033 closed
for `CognitiveBudget`: mature domain authority that no runtime component ever exercises.

## Decision

### Scope: first strategy-aware DIRECT admission only

This ADR introduces the first runtime path that ever consults `ReasoningStrategyDemand`. It does
not implement any specialized `ReasoningStrategy` execution, does not integrate Mode Arbitration,
Attention, Planning, Prediction/Counterfactual, Evaluation, or Verification, and does not design a
future specialized-execution architecture. Only `ReasoningStrategy.DIRECT` is executable by this
runtime slice.

### Demand authority

```text
REASONING_STRATEGY_DEMAND_SCOPE    = PER_REASONING_OPERATION
REASONING_STRATEGY_DEMAND_PRODUCER = CALLER_PER_OPERATION
```

`ReasoningStrategyDemand` is caller-supplied per reasoning operation. Noema does not infer a
demand from `problem_statement` or any other content in this slice -- no text classification, no
model-derived classifier, no mapping from `CognitiveDemand` (that relation remains explicitly
undefined). A missing demand is never treated as equivalent to an explicit all-`False` demand:
`ReasoningStrategyAdmittingDirectOperation.execute` requires an actual `ReasoningStrategyDemand`
instance and rejects anything else with `TypeError` before any resolution is attempted.

### Resolution authority: `ReasoningStrategySelector`, unmodified

`ReasoningStrategySelector` -- not `ReasoningCoordinator` -- is the admission resolution
authority, because its single-decision output shape is exactly what a single-strategy runtime
needs: zero active specialized requirements resolves to DIRECT; exactly one resolves to that
specialized strategy; more than one raises the existing, unmodified `AmbiguousReasoningStrategyError`
unchanged. `ReasoningCoordinator`/`ReasoningCoordinationPlan` remain exactly as they were --
reserved for a future multi-strategy execution model this ADR does not create.

### Enforcement ownership: a new, additive application operation

`ReasoningStrategyAdmittingDirectOperation` (`cognition.application`) wraps exactly one injected
`ReasoningStrategySelector` and one injected `DirectReasoningOperation`. It is not a decorator
implementing an existing port -- `DirectReasoningOperation` is a concrete application class, not a
port -- but it follows the same structural pattern already established by
`CognitiveBudgetAdmittingReasoningExecutor`/`CognitiveBudgetTimeBoundReasoningExecutor`: bind one
inner collaborator, add exactly one new concern, forward everything else unchanged.

`DirectReasoningOperation` itself is completely unmodified: its signature, its "selects no
reasoning strategy" invariant, and every existing test asserting its unconditional DIRECT behavior
remain exactly as they were. `assemble_direct_reasoning_request` is likewise unmodified and
remains unconditionally `strategy=ReasoningStrategy.DIRECT`. The new admission behavior is
strictly additive, layered one level above both.

### Admission timing: strictly before `DirectReasoningOperation.execute`

`ReasoningStrategyAdmittingDirectOperation.execute` resolves the demand via the selector *before*
calling `DirectReasoningOperation.execute` at all -- not interposed between any of that method's
own internal steps, since an external caller of a single atomic method cannot interpose within it.
`ReasoningStrategySelector.select` consumes only the demand object; it needs no registered
content, no ingested TASK, and no prepared `ContextPackage`, so there is no semantic reason to
perform any of that work before admission.

### Failure semantics: no fallback, no leakage into `ReasoningEngine`

```text
SPECIALIZED_TO_DIRECT_FALLBACK_ALLOWED    = NO
SPECIALIZED_REQUEST_REACHES_REASONING_ENGINE = NO
```

A resolved specialized strategy is never silently executed as DIRECT. `assemble_direct_reasoning_request`
can only ever construct a DIRECT `ReasoningRequest` in the first place, so a non-DIRECT decision is
rejected strictly before any `ReasoningRequest` is assembled -- `ReasoningEngine`,
`CognitiveBudgetAdmittingReasoningExecutor`, `CognitiveBudgetTimeBoundReasoningExecutor`, and
`ModelReasoningExecutor` are never reached for a denied demand.

### Failure type: `UnsupportedReasoningStrategyError`, application-owned

A new `UnsupportedReasoningStrategyError`, inheriting directly from `Exception` -- not
`DomainError`, not `ReasoningExecutionError` -- defined in
`cognition.application.reasoning_strategy_admitting_direct_operation` alongside the class that
raises it. The selected `ReasoningStrategy` is valid domain state; `ReasoningStrategySelector`
resolved it deterministically and correctly. What is true is that *this runtime composition*
cannot yet execute it -- an application-owned runtime-capability limitation, structurally
identical to `UnsupportedPriorTaskContextSliceError`'s already-established "valid input this
component cannot yet handle" reasoning, not a domain-policy admission failure in the
`CognitiveBudgetExhaustedError` sense and not a technical execution failure in the
`ReasoningExecutionError` sense. The message may include the selected `ReasoningStrategy` and
`ReasoningStrategyReason` only -- never `problem_statement`, task payload, context content, refs,
provider response, or credentials. No typed payload fields are added; a message-only exception is
sufficient, matching the exact precedent `UnsupportedPriorTaskContextSliceError` already sets.

Multiple active specialized requirements remain the existing `AmbiguousReasoningStrategyError`,
propagated completely unchanged -- never translated into `UnsupportedReasoningStrategyError`. These
are genuinely distinct failure categories: domain-level ambiguity (the demand itself does not
determine one strategy) versus application-level unexecutability (the demand determines one valid
strategy this runtime cannot run).

### No canonical state side effects on denial

```text
DENIED_STRATEGY_RETAINS_CONTENT_REGISTRATION = NO
DENIED_STRATEGY_RETAINS_TASK_INGESTION       = NO
DENIED_STRATEGY_BECOMES_PRIOR_TASK_CONTEXT   = NO
```

Because `DirectReasoningOperation.execute` is never called for a denied or ambiguous demand, none
of its internal steps (content registration, TASK ingestion, context preparation) ever run. This
is not rollback -- nothing to roll back exists, since the operation was never attempted. No
compensating logic is introduced.

### Budget and deadline: never reached on denial

Because denial occurs before any `ReasoningRequest` is ever assembled, `CognitiveBudget` is never
consulted, `max_llm_calls` admission (ADR-0032) is never reached, and the `max_time` deadline scope
(ADR-0033) never opens for a denied demand. For admitted DIRECT, the existing budget path is
byte-for-byte behaviorally unchanged. Neither ADR-0032 nor ADR-0033 is reopened or modified.

### Bootstrap: `open_strategy_aware_direct_runtime`, purely additive

A new `open_strategy_aware_direct_runtime` async context manager in `bootstrap.py` takes the exact
same configuration `open_direct_runtime` already takes, enters `open_direct_runtime` itself,
receives its exact yielded `DirectReasoningOperation` by identity, constructs one
`ReasoningStrategySelector`, and yields one `ReasoningStrategyAdmittingDirectOperation` binding
both. It constructs no second provider client and duplicates no part of the runtime graph --
`open_direct_runtime` still exclusively owns opening and deterministically closing the provider
client exactly once. `open_direct_runtime` itself is completely unchanged: same signature, same
yield type, same behavior, same lifecycle, independently usable exactly as before.

### No CLI/process integration

`_process.py` and `main.py` are unmodified. No CLI syntax is introduced. No strategy demand is
added to `_FirstDirectInvocationPolicy` -- doing so would force the same demand onto every problem
statement in a session, which is incoherent with `REASONING_STRATEGY_DEMAND_SCOPE = PER_REASONING_OPERATION`.
Exit-code semantics for `UnsupportedReasoningStrategyError` are not decided here, since this slice
has no CLI/process caller to define them for.

### No decision trace, no capability registry, no specialized execution architecture

No strategy-decision history, telemetry event, persistence, or `Workspace`/`Situation` write is
introduced -- no consumer for one exists. No `ReasoningCapabilityRegistry`/`StrategyExecutorRegistry`
is introduced; the single local rule "admitted iff DIRECT" is sufficient for a runtime with exactly
one executable strategy. This ADR does not design how a future specialized executor would replace
denial with execution.

## What remains explicitly deferred

`CognitiveMode`/`CognitiveDemand` integration, dynamic strategy execution beyond DIRECT,
`ReasoningCoordinator`-based multi-strategy execution, Planning, Prediction/Counterfactual,
Evaluation, Verification, and any CLI/process-level strategy-aware transport all remain entirely
out of scope and unimplemented after this ADR.

## Non-decisions

This ADR does not modify ADR-0030 through ADR-0033, does not assign a milestone identifier, and
does not decide the relationship between `CognitiveDemand` and `ReasoningStrategyDemand`.

## Consequences

Positive:

- exercises the previously-dead `ReasoningStrategyDemand`/`ReasoningStrategySelector`/
  `AmbiguousReasoningStrategyError` domain authority for the first time in production;
- `DirectReasoningOperation`, `assemble_direct_reasoning_request`, `ReasoningEngine`, both
  `CognitiveBudget` decorators, and `ModelReasoningExecutor` remain completely unchanged;
- `open_direct_runtime` and every existing caller of it remain completely unaffected.

Deferred:

- only `DIRECT` is executable; every specialized `ReasoningStrategy` remains unexecutable and is
  now, for the first time, honestly reported as such rather than silently unreachable;
- no CLI/process surface exists yet for this capability.
