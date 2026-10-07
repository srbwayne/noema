# ADR-0045: Cognitive Budget max_tokens Semantic Meaning

- Status: Accepted
- Date: 2026-10-06

## Context

`CognitiveBudget` is a frozen COGNITION V1 component (ADR-0005). It carries seven upper bounds:
`max_time`, `max_steps`, `max_llm_calls`, `max_tool_calls`, `max_cost`, `max_tokens`, and
`max_search_depth`.

`max_tokens` already exists in the domain contract and is required operator configuration:
`direct.budget.max_tokens` must be supplied in every first-DIRECT process configuration file.
`CognitiveBudget` validates it as a non-negative integer, so `0` is accepted.

ADR-0032 left the field's meaning open:

```text
NOT_ENFORCED_NOW: max_time, max_steps, max_tool_calls, max_cost, max_tokens, max_search_depth
```

- `max_tokens` -- "its own meaning (input/output/aggregate/provider-reported) remains formally
  undefined, exactly as ADR-0030 already left it"; `MAX_TOKENS_RUNTIME_ENFORCEMENT_READY = NO`.
- `CONTENT_SIZE_TO_MODEL_TOKEN_BUDGET_RELATION` remains `UNRESOLVED`, and
  `MODEL_CONTEXT_WINDOW_AUTHORITY` remains `NONE`.

ADR-0033 enforced `max_time` and kept `max_tokens` unenforced. ADR-0032 also fixed the budget scope:

```text
COGNITIVE_BUDGET_SCOPE = PER_REASONING_REQUEST
```

One `CognitiveBudget` governs exactly one `ReasoningRequest`; it is not per-runtime, per-session,
or per-model-resource, and no usage state accumulates across requests. ADR-0032 did not decide how
a token budget accumulates within one request.

Provider-neutral usage telemetry, tokenization, and pricing remain future frontiers (ADR-0032,
ADR-0033), and `USAGE_FRONTIER_DISPOSITION = REMAIN_PARKED` is preserved by ADR-0035, ADR-0036, and
ADR-0037.

Post-M0-18 frontier work on the relation between context content size, token budgets, and model
context windows found that every later question in that area -- capacity authority, enforcement
stage, input and output reservation, overflow policy, and tokenization -- depends on what the
existing `max_tokens` field means. A required operator setting with no defined meaning cannot be
related coherently to any of them. This ADR defines that meaning and nothing else.

## Decision

### Selected policy

```text
SELECTED_R1_POLICY = P3_TOTAL_INPUT_PLUS_OUTPUT_TOKEN_LIMIT
COGNITIVE_BUDGET_MAX_TOKENS_MEANING = TOTAL_INPUT_PLUS_OUTPUT_MODEL_TOKENS
```

`CognitiveBudget.max_tokens` is the maximum cumulative number of model tokens -- input tokens plus
output tokens -- that all model calls made while executing one `ReasoningRequest` may together
consume.

### Scope

```text
COGNITIVE_BUDGET_MAX_TOKENS_SCOPE = PER_REASONING_REQUEST_CUMULATIVE_ACROSS_MODEL_CALLS
```

The budget is per `ReasoningRequest`, as ADR-0032 already establishes. It is not per session, not
per runtime, and not inherently per model resource. Within one `ReasoningRequest`, the tokens of
every model call made while executing it count against the same single limit. This
cumulative-across-calls semantics is decided by this ADR; ADR-0032 fixed only the per-request
scope.

### Token unit

```text
COGNITIVE_BUDGET_MAX_TOKENS_UNIT = TOKENS_OF_THE_EXECUTING_MODEL_RESOURCE_PER_CALL
CROSS_RESOURCE_TOKEN_COMMENSURABILITY = NOT_DECIDED_HERE
```

A token is denominated according to the model resource executing the call in which it occurs. Both
the input and the output of one call are therefore measured in the same unit. This ADR defines what
a token denotes, not how tokens are counted: neither a tokenizer nor an estimation method is chosen
here.

Current production execution uses one model resource per DIRECT request: DIRECT makes exactly one
model call, and the model resource is selected from the executor's single bound selection request.
Requests with several model calls, or calls on different model resources, are not canonically
forbidden. Whether token counts produced under different model resources may be summed into one
cumulative quantity is not decided by this ADR.

### Zero value

```text
COGNITIVE_BUDGET_MAX_TOKENS_ZERO_VALUE_MEANING = NO_MODEL_TOKENS_PERMITTED
MAX_TOKENS_VALIDATION_CHANGED = NO
```

`max_tokens = 0` permits no model tokens for the `ReasoningRequest`. Zero is already valid today,
and validation is unchanged. Because `max_tokens` is unenforced, runtime behavior does not change
now; future enforcement will make zero behaviorally meaningful. No test changes with this ADR.

### Budget is not model capacity

```text
MAX_TOKENS_IS_MODEL_CONTEXT_WINDOW = NO
```

`max_tokens` is a cognition-side requested budget. A model context window is a capability or
capacity fact of a model resource. The two must not be conflated: a budget may be lower than,
equal to, or higher than any model's capacity. This ADR does not decide model context-window
authority, model-capacity discovery, model-capacity enforcement, or model-overflow behavior.

### Relation to context content size

```text
MAX_TOKENS_TO_CONTEXT_CONTENT_SIZE_RELATION = NOT_DECIDED_HERE
```

`max_tokens` is token-denominated. `ContextRequest.max_total_content_size` remains a
provider-independent raw Unicode code-point budget under ADR-0030. Neither value is derived from
the other, no conversion ratio is introduced, and `ContextComposer` behavior is unchanged.

### Enforcement

```text
MAX_TOKENS_ENFORCEMENT_STATUS = DEFERRED
```

This ADR defines semantic meaning only. It does not authorize token counting, tokenizer
integration, estimation, budget enforcement, provider output limits, `ModelExecutionRequest`
changes, `ContextComposer` changes, usage telemetry, pricing or cost accounting, prompt
truncation, or model-capacity handling. `max_tokens` remains in ADR-0032's `NOT_ENFORCED_NOW` set,
and runtime behavior is unchanged.

### Implementation state

```text
IMPLEMENTATION_REQUIRED = NO
TEST_CHANGES_REQUIRED = NO
```

No production code or test is required, because the decision is semantic only.

### Milestone state

```text
NEXT_MILESTONE_IDENTIFIER = UNASSIGNED
M0_19_ASSIGNED = NO
```

## Rationale

- **Sibling dimensions are whole-request limits.** `max_llm_calls`, `max_cost`, and `max_time`
  each bound a resource for the whole `ReasoningRequest`. A token budget in the same component
  reads most consistently as a whole-request bound on the model-token resource.
- **Only P3 bounds the complete resource.** Model calls consume tokens both as input and as
  generated output. P3 is the only option that bounds the complete model-token resource rather
  than one half of it.
- **P1 leaves generation outside the budget.** An input-only limit would let output grow without
  bound under a field that claims to bound tokens.
- **P2 narrows the field and leaves input growth unbudgeted.** An output-only limit turns
  `max_tokens` into an output-length concept and leaves model-input growth, including growth from
  prior-`TASK` context, outside any token budget.
- **Implementation convenience does not choose semantics.** An output-only limit could be enforced
  more easily, through a provider-side cap, but ease of enforcement is not evidence of the right
  meaning. Enforcement is deferred for every option alike.
- **Boundaries are preserved.** P3 is defined without a tokenizer, usage telemetry, or
  context-window authority. It changes no composition, routing, provider, or configuration
  contract, and leaves every later C2 question open.

## Alternatives Considered

### P1: Input token limit

```text
P1_INPUT_TOKEN_LIMIT = REJECTED
```

Rejected because it bounds input only and leaves output outside the generic `max_tokens` budget.

### P2: Output token limit

```text
P2_OUTPUT_TOKEN_LIMIT = REJECTED
```

Rejected because it turns `max_tokens` into a narrower output-length concept and leaves input
growth unbudgeted.

### P3: Total input plus output token limit

```text
P3_TOTAL_INPUT_PLUS_OUTPUT_TOKEN_LIMIT = ACCEPTED
```

Selected, as decided above.

### P4: Abstract budget with no model-token semantics

```text
P4_ABSTRACT_NO_MODEL_TOKEN_SEMANTICS = REJECTED_AS_NON_RESOLUTION
```

Rejected because it would preserve the undefined semantic state under another description.

### P5: Remove or deprecate max_tokens

```text
P5_REMOVE_OR_DEPRECATE_MAX_TOKENS = OUT_OF_SCOPE_STRUCTURAL_DECISION
```

Out of scope because removal changes an existing domain and configuration contract of a frozen
component and requires a separate architectural decision.

## Not Decided Here

- R2: model context-window capacity authority.
- R3: the boundary between context composition and model capacity.
- R4: the token-budget enforcement stage.
- R5: reservation for non-context model input.
- R6: output-token reservation.
- R7: model-capacity overflow policy.
- R8: tokenizer or estimation policy.
- R9: operator configuration versus model-capability authority.
- The token counting algorithm.
- Cross-resource token commensurability.
- Usage telemetry.
- Pricing and cost accounting.
- Provider-specific tokenization.
- `ModelExecutionRequest` options.
- `ContextComposer` redesign.
- README and configuration documentation changes.
- Implementation.
- Milestone assignment.

```text
README_MAX_TOKENS_CLARIFICATION = FOLLOW_UP_DOCUMENTATION_ONLY
```

The README configuration example does not yet state this meaning. Clarifying it is a separate
documentation action.

## Consequences

**Positive:**

- The required `max_tokens` operator setting now has a defined meaning.
- Later C2 work on capacity, enforcement, reservation, and overflow can build on one fixed
  quantity.
- No production code, test, configuration, or runtime behavior changes.
- Subsystem boundaries between budget, composition, routing, and providers are unchanged.

**Tradeoffs:**

- `max_tokens` remains unenforced; an operator-configured value still has no runtime effect.
- Future enforcement needs both input-token knowledge and a way to limit output, through mechanisms
  this ADR does not decide.
- The cumulative quantity is undefined for a request that spans different model resources until
  cross-resource commensurability is decided.
- Many existing test fixtures use `max_tokens = 0` as a filler value; future enforcement will make
  that value deny every model call, so those fixtures will need review then.
- Some provider APIs use a parameter named `max_tokens` for output length only; operators may
  misread the field until the README clarification is made.

## ADR Relationship

ADR-0045 supplements ADR-0032 (Cognitive budget runtime enforcement). It resolves only ADR-0032's
previously undefined `max_tokens` semantic meaning and preserves its current non-enforcement. It
supersedes no ADR.

```text
ADR_0045_SUPPLEMENTS_ADR_0032 = YES
ADR_0045_SUPERSEDES_ADR_0032 = NO
SUPERSEDES = NONE
```

```text
ADR-0005 = NOT_AFFECTED
ADR-0030 = NOT_AFFECTED
ADR-0031 = NOT_AFFECTED
ADR-0032 = SUPPLEMENTED
ADR-0033 = NOT_AFFECTED
ADR-0035 = NOT_AFFECTED
ADR-0036 = NOT_AFFECTED
ADR-0037 = NOT_AFFECTED
ADR-0044 = NOT_AFFECTED
```

ADR-0045 gives meaning to an existing field and introduces no structural change to the frozen
ADR-0005 Cognitive Budget component.
