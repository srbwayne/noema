# ADR-0032: Cognitive Budget Runtime Enforcement (max_llm_calls Admission)

- Status: Accepted
- Date: 2026-09-18

## Context

`CognitiveBudget` (seven fields: `max_time`, `max_steps`, `max_llm_calls`, `max_tool_calls`,
`max_cost`, `max_tokens`, `max_search_depth`) has existed since early milestones as request
metadata, but until this ADR no production component read any individual field at runtime.
`ReasoningRequest.budget`/`PlanningRequest.budget` were validated only for type
(`isinstance(..., CognitiveBudget)`); `ReasoningEngine`'s own docstring states explicitly that
it "does not... consume the request's budget."

This was a demonstrated, not merely theoretical, gap: `CognitiveBudget.max_llm_calls` accepts
`0` (already valid domain construction, proven by the existing
`test_zero_resource_cognitive_budget_is_valid`), the canonical first-DIRECT runtime
deterministically requires exactly one model-execution attempt on its normal path, and prior to
this ADR a `CognitiveBudget` configured with `max_llm_calls=0` still allowed that attempt to
proceed and successfully contact a (fake, in tests; real, in production) provider. Multiple
existing test fixtures across the repository used `max_llm_calls=0` as a "don't care" filler
value specifically because it was unenforced, including fixtures backing tests that exercised
the complete real runtime graph end to end.

## Decision

### Authority semantics

```text
COGNITIVE_BUDGET_AUTHORITY_SEMANTICS = HARD_UPPER_BOUNDS
```

Every `CognitiveBudget` field is a hard ceiling, not an advisory hint. No soft/advisory variant
or override mechanism exists anywhere in the domain layer, and zero is already proven, by
existing domain tests, to be a fully legitimate value for every zero-permitted dimension.

### Scope

```text
COGNITIVE_BUDGET_SCOPE = PER_REASONING_REQUEST
```

One `CognitiveBudget` governs exactly one `ReasoningRequest`. It is not per-runtime, per-session,
or per-model-resource. The same immutable, already-configured `CognitiveBudget` object may be
reused by reference across multiple sequential operations in one process session (as
`_process.py` already does), but each `ReasoningRequest` is independently evaluated against it —
no usage state accumulates or is shared across requests, and none is introduced by this ADR.

### Zero semantics

```text
0 = zero available resource, never "unlimited"
```

No contradicting authority exists anywhere in the repository; this ADR does not introduce a
`0 = unlimited` sentinel for any dimension.

### First implementation slice: MAX_LLM_CALLS_ADMISSION_ONLY

Only `ReasoningStrategy.DIRECT`'s static resource demand is known today: exactly one
model-execution attempt, unconditionally, on every DIRECT path. This lets `max_llm_calls`
admission be decided purely before execution, with zero telemetry or accounting infrastructure:

```text
request.strategy is DIRECT and request.budget.max_llm_calls >= 1  -> admitted
request.strategy is DIRECT and request.budget.max_llm_calls <  1  -> denied
request.strategy is not DIRECT                                    -> no admission check performed
```

Materialization (`ReasoningInputMaterializer.materialize`) and model routing (`ModelRouter.route`,
purely local selection logic) are **not** LLM calls — neither performs provider I/O. The semantic
consumption boundary for "one LLM call" is one actual invocation of `ModelExecutor.execute`
against a selected model resource. This ADR does not introduce any usage counter, retry logic, or
attempt-accounting state — DIRECT's demand is a fixed constant (`1`), so no counting is needed to
admit or deny it.

Non-DIRECT strategies are explicitly out of scope: this component invents no demand for them and
performs no admission check, delegating unchanged. In the canonical first-DIRECT runtime this path
is unreachable today (the request assembler fixes `ReasoningStrategy.DIRECT`), but the explicit
pass-through prevents this component from pretending to enforce a budget dimension whose resource
demand is not yet defined for any other strategy.

### Enforcement ownership: an application-layer `ReasoningExecutor` decorator

`CognitiveBudgetAdmittingReasoningExecutor` (`cognition.application`) structurally implements the
existing, unmodified `ReasoningExecutor` port and wraps one inner executor
(`ModelReasoningExecutor` in the production graph). Bootstrap now wires:

```text
ModelReasoningExecutor -> CognitiveBudgetAdmittingReasoningExecutor -> ReasoningEngine
```

This preserves `ReasoningEngine`'s existing invariant literally unchanged — it still consumes no
budget itself — and keeps `ModelReasoningExecutor` (and every component beneath it: input
materialization, model routing, `ModelExecutionEngine`, `ModelExecutor`, provider adapters)
completely unaware that budget admission exists. `CognitiveBudget` remains cognition-owned
authority; `model_router` gains no new dependency and no schema change.

### Failure semantics: `CognitiveBudgetExhaustedError`

A new `DomainError` subtype, `CognitiveBudgetExhaustedError`
(`cognition.domain.errors.cognitive_budget_errors`), distinct from `InvalidCognitiveBudgetError`:

- `InvalidCognitiveBudgetError` — the `CognitiveBudget` value itself is malformed.
- `CognitiveBudgetExhaustedError` — the `CognitiveBudget` is perfectly valid, but the current
  operation's known resource demand cannot be admitted within it.

This is a domain-policy admission failure. It is never translated to `ReasoningExecutionError`
(reserved exclusively for technical execution-technology failures — nothing technical failed
here, since nothing was attempted) and never represented as `ReasoningStatus.UNRESOLVED`
(reserved for genuine semantic reasoning incompleteness after an attempt). It propagates
unwrapped, exactly as the existing `ContextCompositionUnsatisfiedError` already does for its own,
structurally analogous "valid inputs cannot satisfy this request" case.

### No rollback

Budget admission runs beneath `DirectReasoningOperation`, after content registration and
canonical-TASK ingestion. A denial therefore leaves registration and ingestion committed, exactly
matching `DirectReasoningOperation`'s existing no-rollback guarantee for every other later-stage
failure. Admission is not moved upward into `DirectReasoningOperation` merely to avoid this —
doing so would duplicate `ReasoningRequest`/`CognitiveBudget` knowledge into a component that
today constructs neither.

## What remains explicitly deferred

```text
ENFORCED_NOW:     max_llm_calls, for ReasoningStrategy.DIRECT admission only
NOT_ENFORCED_NOW: max_time, max_steps, max_tool_calls, max_cost, max_tokens, max_search_depth
```

- `max_steps` — "cognitive step" has no operational definition anywhere in this repository;
  remains `SEMANTICS_UNRESOLVED`.
- `max_time` — clock authority (monotonic/wall/CPU), deadline scope, and in-flight provider-call
  cancellation are all undecided; `MAX_TIME_RUNTIME_ENFORCEMENT_READY = NO`.
- `max_cost` — no provider adapter reports cost or usage; no pricing table exists;
  `MAX_COST_RUNTIME_ENFORCEMENT_READY = NO`.
- `max_tokens` — its own meaning (input/output/aggregate/provider-reported) remains formally
  undefined, exactly as ADR-0030 already left it; `MAX_TOKENS_RUNTIME_ENFORCEMENT_READY = NO`.
- `max_tool_calls`/`max_search_depth` — DIRECT statically consumes zero of either today, so no
  configured value can ever be violated; this is not claimed as implemented enforcement, only as
  a currently-inapplicable dimension.
- `CONTENT_SIZE_TO_MODEL_TOKEN_BUDGET_RELATION` remains `UNRESOLVED`; `ContextRequest.max_total_content_size`
  remains independent from `CognitiveBudget.max_tokens` — neither is derived from the other.
- `MODEL_CONTEXT_WINDOW_AUTHORITY` remains `NONE` — no model resource carries a capacity/context-window
  field.
- No provider-neutral usage telemetry (`ModelExecutionUsage` or equivalent), no tokenization, no
  pricing data, and no retry mechanism are introduced by this ADR.

Full `CognitiveBudget` enforcement is **not** complete after this ADR. This ADR does not claim
"CognitiveBudget is fully enforced" or "all cognitive limits are active" — exactly one dimension,
for exactly one strategy, is enforced.

## Non-decisions

This ADR does not modify ADR-0030 or ADR-0031, does not decide multi-strategy budget aggregation
(`ReasoningCoordinationPlan` remains unwired and carries no budget concept), does not assign a
milestone identifier, and does not resolve any of the deferred dimensions listed above.

## Consequences

Positive:

- closes the demonstrated `max_llm_calls=0` runtime gap: a canonical DIRECT operation with an
  insufficient budget can no longer reach a provider;
- `ReasoningEngine`, `ModelReasoningExecutor`, and every `model_router` component remain
  completely unchanged and unaware of budget policy;
- the decorator shape generalizes cleanly to future strategies/coordination without committing to
  an aggregation model prematurely.

Deferred:

- six of seven `CognitiveBudget` dimensions remain unenforced, honestly and explicitly;
- provider-neutral usage telemetry, tokenization, and pricing remain future frontiers.
