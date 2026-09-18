# ADR-0033: Reasoning Cognitive Budget max_time Runtime Deadline

- Status: Accepted
- Date: 2026-09-18

## Context

ADR-0032 closed the `max_llm_calls` runtime gap for `ReasoningStrategy.DIRECT` admission, but left
six of `CognitiveBudget`'s seven dimensions unenforced, `max_time` included. Prior to this ADR, no
production component ever read `ReasoningRequest.budget.max_time`: a `CognitiveBudget` configured
with an arbitrarily small `max_time` still allowed materialization, model routing, and provider
execution to run for however long the underlying technology actually took, with no runtime
deadline of any kind. This is the same class of demonstrated gap ADR-0032 closed for
`max_llm_calls` — `CognitiveBudget` already validates `max_time` as a required positive
`timedelta` (`CognitiveBudget.__post_init__`), so the value has always been present and
well-formed; it was simply never consumed.

## Decision

### Authority semantics preserved

```text
COGNITIVE_BUDGET_AUTHORITY_SEMANTICS = HARD_UPPER_BOUNDS
COGNITIVE_BUDGET_SCOPE               = PER_REASONING_REQUEST
```

ADR-0032's authority model is unchanged and unreopened. `max_time` is a hard ceiling on one
`ReasoningRequest`'s execution, not an advisory hint, and not per-runtime or per-session state.

### Scope: `ReasoningRequest` execution only

```text
MAX_TIME_SCOPE = REASONING_REQUEST_EXECUTION_ONLY
```

The deadline wraps exactly the call into the inner `ReasoningExecutor.execute` this decorator
wraps — nothing upstream of it. Content registration, canonical-TASK ingestion, `ContextPackage`
preparation, and `ReasoningRequest` assembly all happen in `DirectReasoningOperation` before
`ReasoningEngine.reason(...)` is ever called, so none of that is inside the timed scope, and a
deadline expiry cannot roll any of it back (see "No rollback" below).

Inside the timed scope: `max_llm_calls` admission (`CognitiveBudgetAdmittingReasoningExecutor`,
outermost — see bootstrap topology below) runs *before* the deadline is opened, but everything
`ModelReasoningExecutor` does once called — `ReasoningInputMaterializer.materialize`
(`PriorTaskReasoningInputMaterializer` / `PriorTaskContextMaterializer` in the production graph),
`ModelRouter.route`, and the provider execution itself — runs *inside* it.

### Clock authority and timeout primitive

```text
MAX_TIME_CLOCK_AUTHORITY    = asyncio event-loop monotonic clock
MAX_TIME_TIMEOUT_PRIMITIVE  = asyncio.timeout(request.budget.max_time.total_seconds())
```

No wall-clock `datetime`, no `asyncio.wait_for`, no manually created timer task, no
`threading.Timer`, no signal alarm, and no provider-specific timeout parameter. The domain
`timedelta` is converted to seconds via `.total_seconds()` at the point of use only — no
`timedelta` reconstruction, and `direct.budget.max_time_ms` (the process-config millisecond value
that already builds `CognitiveBudget.max_time`) is never read directly by this component.

### Enforcement ownership: a second, separate `ReasoningExecutor` decorator

`CognitiveBudgetTimeBoundReasoningExecutor` (`cognition.application`) structurally implements the
existing, unmodified `ReasoningExecutor` port — the same structural-port pattern
`CognitiveBudgetAdmittingReasoningExecutor` already uses, deliberately not `runtime_checkable` and
not validated via `isinstance` — and wraps one inner executor. It is a distinct component from
`CognitiveBudgetAdmittingReasoningExecutor`, not a modification of it: admission and deadline
enforcement are separate concerns with separate failure semantics, so they remain separate
decorators.

Bootstrap now wires:

```text
ModelReasoningExecutor
  -> CognitiveBudgetTimeBoundReasoningExecutor
  -> CognitiveBudgetAdmittingReasoningExecutor
  -> ReasoningEngine
```

This exact ordering is load-bearing: `max_llm_calls` admission runs *first* (outermost), so a
request denied by admission never opens a deadline scope, never materializes input, and never
reaches the provider — `MAX_LLM_ADMISSION_PRECEDES_TIME_DEADLINE = YES`, proven end to end through
the real bootstrap graph. `ReasoningEngine`, `ModelReasoningExecutor`, and every `model_router`
component remain completely unaware that a deadline exists, exactly as they remained unaware of
budget admission under ADR-0032.

### Stateless decorator, per-request deadlines

`CognitiveBudgetTimeBoundReasoningExecutor` holds no mutable timer state (`__slots__ =
("_inner_executor",)`; no `deadline`, `started_at`, `remaining_time`, or shared
`asyncio.Timeout`). Each `execute` call opens its own local `asyncio.timeout` scope. Two
independent calls — sequential or concurrent — sharing the same immutable `CognitiveBudget` object
therefore each receive a fully independent deadline:
`MAX_TIME_PER_REQUEST_RESET = YES`, proven by both a unit test (two sequential calls whose
individual durations fit the budget but whose sum would not, if any elapsed time leaked between
them) and a real-graph bootstrap test.

### Timeout ownership verification: `expired()`, not bare `TimeoutError`

Catching `TimeoutError` alone is not sufficient: an inner `ReasoningExecutor` implementation could
independently raise a plain built-in `TimeoutError` unrelated to this deadline (for example, a
future executor wrapping a technology whose own client raises it directly, before any provider
adapter has a chance to translate it). To avoid misclassifying that as a cognitive deadline
expiry, the decorator retains the `asyncio.timeout` context object and checks
`timeout_context.expired()` before translating:

```python
timeout_context = asyncio.timeout(request.budget.max_time.total_seconds())
try:
    async with timeout_context:
        return await self._inner_executor.execute(request)
except TimeoutError as exc:
    if not timeout_context.expired():
        raise
    raise CognitiveBudgetTimeExceededError(...) from exc
```

`CognitiveBudgetTimeExceededError` may be raised only when the timeout context this decorator
itself created reports `expired() is True`. A raw inner `TimeoutError` whose owning context never
expired propagates completely unchanged — proven by a dedicated unit test with an inner executor
that raises `TimeoutError` immediately under a comfortably large `max_time`.

### External cancellation remains `CancelledError`

Cancellation delivered by a caller unrelated to this decorator's own deadline (`asyncio.Task.cancel()`)
is never caught, suppressed, or translated: this decorator catches only `TimeoutError`, never
`BaseException` or `asyncio.CancelledError`. Proven by a unit test that cancels an in-flight
`execute()` task externally and asserts the exact original `CancelledError` propagates.

### Provider technical timeout remains `ReasoningExecutionError`

A provider/technology-level timeout (for example the Ollama SDK's own client raising a technical
`TimeoutError`, already translated by `OllamaModelExecutor`'s existing `except Exception` boundary
into `ModelExecutionError` and then by `ModelReasoningExecutor` into `ReasoningExecutionError`)
remains entirely distinct from a cognitive deadline expiry. Proven at two boundaries:

1. a real-graph bootstrap test where the fake provider raises a plain `TimeoutError` immediately
   while `max_time` is comfortably large — expects `ReasoningExecutionError`, not
   `CognitiveBudgetTimeExceededError`;
2. the decorator-level unit test above (`expired()` firewall), since the canonical Ollama path
   already translates its own technical timeout before it would ever reach this decorator as a
   raw `TimeoutError`, but the decorator is generic over any `ReasoningExecutor` and must prove the
   distinction on its own terms too.

### Cooperative-cancellation contract

`ReasoningExecutor`'s port docstring (`cognition.ports.reasoning_executor`) now states explicitly,
as behavioral documentation only (no signature change:
`REASONING_EXECUTOR_RUNTIME_SCHEMA_CHANGE_REQUIRED = NO`), that implementations must allow task
cancellation to propagate, must not intentionally suppress `asyncio.CancelledError`, may perform
cleanup via `try`/`finally`, and must re-raise cancellation after that cleanup. This is what makes
deadline-triggered cancellation of `ModelReasoningExecutor` (and everything it calls) actually
observable rather than silently swallowed.

### Failure semantics: `CognitiveBudgetTimeExceededError`

A new `DomainError` subtype, `CognitiveBudgetTimeExceededError`
(`cognition.domain.errors.cognitive_budget_errors`, re-exported through
`cognition.domain.budget` exactly as `CognitiveBudgetExhaustedError` already is), distinct from
every neighboring error:

- `InvalidCognitiveBudgetError` — the `CognitiveBudget` value itself is malformed.
- `CognitiveBudgetExhaustedError` — the `CognitiveBudget` is valid, but known demand could not be
  admitted *before* reasoning execution ever began. Its semantics are completely unchanged by this
  ADR.
- `CognitiveBudgetTimeExceededError` — the `CognitiveBudget` is valid, admission already passed,
  reasoning execution actually began, but `request.budget.max_time` elapsed before it completed.
- `ReasoningExecutionError` — a technical execution-technology failure; a cognitive deadline is a
  budget-policy failure, not a technical one.

The error message may include `max_time` and the `ReasoningStrategy` value
(`ReasoningStrategy.DIRECT exceeded max_time=<value>`); it must never include
`problem_statement`, `problem_ref`, TASK payloads, model output, or provider credentials — the same
content-privacy discipline `CognitiveBudgetExhaustedError`'s denial message already follows.

### Provider attempt semantics: no refund, no retry

When the fake/real provider execution has actually begun before the deadline cancels it, one LLM
attempt is semantically consumed — proven by asserting exactly one `generate` call recorded even
though the request ultimately raised `CognitiveBudgetTimeExceededError`. No mutable
`max_llm_calls` counter is introduced; this ADR does not add attempt accounting, refund logic, or
automatic retry of any kind.

### No rollback

A cognitive deadline expiry runs beneath `DirectReasoningOperation`, after content registration and
canonical-TASK ingestion, exactly like an ADR-0032 admission denial. A deadline failure therefore
leaves registration and ingestion committed — proven by a real-graph test asserting the registered
current-TASK payload remains resolvable and the canonical `SituationModel` still contains the TASK
entry after `CognitiveBudgetTimeExceededError` propagates.

### Materialization and blocking-work limitation

`max_time` enforcement is cooperative async deadline enforcement, not hard real-time scheduling,
thread preemption, or process termination. `PriorTaskReasoningInputMaterializer` /
`PriorTaskContextMaterializer` remain synchronous, CPU-bound calls inside the timed scope; this ADR
does not make them async and does not introduce any clock into them. A cancellation delivered while
synchronous, non-yielding work is running cannot preempt that work — it can only be delivered at
the next event-loop scheduling opportunity (in practice, at or after the next `await`, most often
inside the actual provider I/O call). This is a known, accepted limitation of cooperative
`asyncio` cancellation, not a defect this ADR attempts to solve.

## What remains explicitly deferred

```text
ENFORCED_NOW:     max_llm_calls (ADR-0032, DIRECT admission only), max_time (this ADR,
                   ReasoningRequest execution only)
NOT_ENFORCED_NOW: max_steps, max_tool_calls, max_cost, max_tokens, max_search_depth
```

- Planning `max_time` (`PlanningRequest.budget`) is not implemented by this ADR — only
  `ReasoningRequest` execution is in scope.
- `max_steps`, `max_cost`, `max_tokens`, `max_search_depth`, and `max_tool_calls` remain exactly as
  deferred by ADR-0032; this ADR does not change any of their readiness.
- `CONTENT_SIZE_TO_MODEL_TOKEN_BUDGET_RELATION` remains `UNRESOLVED`; `MODEL_CONTEXT_WINDOW_AUTHORITY`
  remains `NONE`.
- No provider-neutral usage telemetry (`ModelExecutionUsage`, elapsed-time fields, token usage,
  cost usage, or provider duration metadata) is introduced. `max_time` is enforced purely by
  cancellation/deadline, not by post-hoc measurement.
- `model_router` (including `OllamaModelExecutor`) gains no new dependency, no timeout parameter,
  and no schema change of any kind.

Full `CognitiveBudget` enforcement is **not** complete after this ADR. This ADR does not claim
"CognitiveBudget is fully enforced" — exactly two of seven dimensions are enforced, and only for
`ReasoningRequest` execution.

## Non-decisions

This ADR does not modify ADR-0030, ADR-0031, or ADR-0032, does not assign a milestone identifier,
and does not resolve any of the deferred dimensions listed above.

## Consequences

Positive:

- closes the demonstrated `max_time` runtime gap: a `ReasoningRequest` execution that outlives its
  own budget is now cancelled and reported as a distinct, catchable domain error instead of running
  unbounded;
- `ReasoningEngine`, `ModelReasoningExecutor`, and every `model_router` component remain completely
  unchanged and unaware that a deadline exists;
- `max_llm_calls` admission and `max_time` deadline enforcement remain two separate, independently
  reasoned-about decorators with independent failure semantics, composed rather than merged.

Deferred:

- five of seven `CognitiveBudget` dimensions remain unenforced, honestly and explicitly;
- Planning budget enforcement, blocking-work preemption, and provider-neutral usage telemetry
  remain future frontiers.
