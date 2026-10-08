# ADR-0047: Model Input Capacity Relation Boundary

- Status: Accepted
- Date: 2026-10-07

## Context

ADR-0046 made a model resource's effective context capacity a declared resource fact owned by
`model_router`, with UNKNOWN as a valid state. It did not decide where, or by whom, that fact is
related to the input of a model call:

```text
R3_COMPOSITION_CAPACITY_BOUNDARY = NOT_DECIDED_HERE
```

The current first-DIRECT runtime builds and executes model input in this order:

1. `ContextPackagePreparer` composes a `ContextPackage` under the provider-independent
   code-point budget of ADR-0030.
2. `ReasoningRequest` is assembled and passes the existing cognition budget decorators
   (`max_llm_calls` admission, ADR-0032; `max_time` deadline, ADR-0033).
3. Inside `ModelReasoningExecutor`, `ReasoningInputMaterializer.materialize` returns the final
   model input text.
4. Inside `ModelExecutionEngine.execute`, `ModelRouter.route` returns the single
   `ModelSelectionDecision`.
5. A `ModelExecutionRequest` binds the selected resource to the final input text.
6. `ModelExecutor.execute` performs provider execution.

The final model input therefore first exists after materialization, and the selected resource first
exists after routing. Both first coexist inside `model_router`'s execution boundary, after routing
and before provider execution. Cognition never sees the selected resource before execution.

The current state of capacity is:

```text
CAPACITY_AUTHORITY_CANONICAL = YES_BY_ADR_0046
CAPACITY_RUNTIME_REPRESENTATION_IMPLEMENTED = NO
CAPACITY_RELATION_IMPLEMENTED = NO
```

No component represents capacity at runtime and no component relates input to capacity. This ADR
decides the boundary stage and the owner of that relation. It decides nothing else.

## Decision

### Governed relation

```text
MODEL_INPUT_CAPACITY_RELATION = relation between the exact final model input of one call, the
                                already-selected model resource, and that resource's effective
                                context capacity under ADR-0046
R3_COUNTING_OBJECT = EXACT_FINAL_MODEL_INPUT_OF_ONE_CALL
```

The relation is per call and per selected resource. Its input-side object is the exact final model
input of that one call, as materialized. This ADR determines what object will later be counted, not
how it is counted.

### Boundary stage

```text
MODEL_INPUT_CAPACITY_RELATION_STAGE = FINAL_INPUT_PRE_PROVIDER
PRE_MATERIALIZATION_CAPACITY_RELATION_AUTHORITATIVE = NO
PROVIDER_ADAPTER_OWNS_CAPACITY_RELATION = NO
```

The normative order is:

1. the final model input is fully materialized;
2. one model resource is selected;
3. the capacity relation is evaluated;
4. provider execution may occur afterward.

A relation evaluated before materialization is not authoritative, because the exact final input
does not yet exist then. Provider adapters execute calls; they do not own this relation.

### Strict selected-resource semantics

```text
SELECTED_RESOURCE_RELATION_SEMANTICS = S1_STRICT_SELECTED_RESOURCE_ADMISSION
CAPACITY_AS_SELECTION_ELIGIBILITY = NOT_DECIDED_HERE
F3_REQUIRES_SEPARATE_ROUTING_FRONTIER = YES
```

- The relation does not participate in choosing the resource.
- Selection completes first.
- The selected resource is then related to the exact final input.
- Treating capacity as a selection-eligibility criterion is not part of this decision.

Resource selection keeps its current, capability-only semantics.

### Single-selection coherence

```text
CAPACITY_RELATION_AND_PROVIDER_EXECUTION_USE_SAME_RESOURCE_DECISION = YES
SECOND_ROUTING_FOR_CAPACITY_CHECK_ALLOWED = NO
```

The resource whose capacity is related to the input must be exactly the resource later used for
provider execution. No separate routing may be performed for the purpose of the relation. This ADR
does not decide how the selection decision is represented.

### Semantic owner

```text
SELECTED_R3_OWNER_POLICY = F1_POST_SELECTION_ADMISSION_IN_MODEL_ROUTER
CAPACITY_FACT_OWNER = MODEL_ROUTER
CAPACITY_RELATION_POLICY_OWNER = MODEL_ROUTER
```

The relation is owned by `model_router`. This assignment is a separate architectural decision. It
is not inferred merely from ADR-0046's assignment of the capacity fact to `model_router`.

The relation belongs to `model_router` because:

- `model_router` owns resource selection;
- `model_router` owns the semantics of the capacity fact;
- the selected resource, the final input, and the future capacity fact meet at the pre-provider
  execution boundary;
- ownership there avoids leaking capacity and selection information back into cognition.

The selected architecture places the future capacity relation at the point where the final input
and the selected resource already coexist. ADR-0046 requires the capacity fact to become available
there in a later implementation.

### UNKNOWN capacity

```text
SELECTED_UNKNOWN_RELATION_POLICY = U1_TOTAL_RELATION_NO_CAPACITY_JUDGMENT
CAPACITY_RELATION_IS_TOTAL = YES
UNKNOWN_CAPACITY_RELATION_RESULT = NO_CAPACITY_JUDGMENT
```

The relation is defined for every call and selected resource. When the selected resource's
effective context capacity is UNKNOWN, the relation's result is `NO_CAPACITY_JUDGMENT`.

```text
UNKNOWN_CAPACITY_MEANS_ZERO = NO
UNKNOWN_CAPACITY_MEANS_UNLIMITED = NO
UNKNOWN_CAPACITY_IMPLIES_ALLOW = NO
UNKNOWN_CAPACITY_IMPLIES_DENY = NO
UNKNOWN_CAPACITY_IMPLIES_FALLBACK = NO
```

`NO_CAPACITY_JUDGMENT` is a semantic result only. It implies neither allowance nor denial nor any
fallback. This ADR does not decide the runtime response to it. For a resource whose capacity is
known, the content of the judgment depends on how input is counted (R8) and on any output share of
capacity (R6), neither of which is decided here.

### Structural implications

```text
COGNITION_STRUCTURE_CHANGE_REQUIRED_BY_R3 = NO
MODEL_ROUTER_STRUCTURE_CHANGE_REQUIRED_BY_R3 = YES
MODEL_EXECUTION_REQUEST_CHANGE_REQUIRED_BY_R3 = NO
NEW_PORT_REQUIRED_BY_R3 = NO
COMPOSITION_ROOT_CHANGE_REQUIRED_BY_R3 = NO
PROVIDER_ADAPTER_CHANGE_REQUIRED_BY_R3 = NO
```

These are architectural consequences only. A future implementation of the relation changes
`model_router` structure. Delivery of the declared capacity fact is already established by
ADR-0046. This ADR names no type, field, port, or class.

### Current tests

Existing tests that describe the current route-once and execute-once behavior of model execution,
or the current shape of `model_router` types, are evidence of current structure. They are not
architectural authority. This ADR does not change them.

### Implementation state

```text
CAPACITY_RELATION_IMPLEMENTED = NO
IMPLEMENTATION_REQUIRED = NO
TEST_CHANGES_REQUIRED = NO
```

This ADR sets architectural direction only. No production code, test, configuration, or runtime
behavior changes. A later explicit gate is required before implementation.

### Milestone state

```text
NEXT_MILESTONE_IDENTIFIER = UNASSIGNED
M0_19_ASSIGNED = NO
```

## Rationale

- **The exact final input is available.** After materialization, the input to be related is the
  input the call will actually send.
- **One resource has already been selected.** Capacity is resource-specific under ADR-0046, so the
  relation needs the resource the call will execute on.
- **`model_router` is the smallest coherent owner.** The input, the single selection decision, and
  the future capacity fact all meet inside `model_router` before provider execution.
- **The resource judged is the resource executed.** Ownership at that point binds the relation to
  the same selection decision under which the call executes.
- **It is provider-neutral.** The relation is architectural policy, not provider behavior,
  consistent with ADR-0002 and ADR-0003.
- **`ContextComposer` remains capacity-agnostic.** Composition keeps the provider-independent
  code-point budget of ADR-0030.
- **Cognition needs no resource or capacity information.** Cognition continues to hand
  `model_router` a materialized string, as under ADR-0031.
- **Counting stays separate.** The relation fixes the object to be counted, leaving tokenizer and
  estimation authority to R8.
- **Routing semantics stay unchanged.** Selection remains capability-only.

### External-provider evidence boundary

```text
PROVIDER_EMPIRICAL_DATA_REQUIRED = NO
OLLAMA_BEHAVIOR_USED_AS_NORMATIVE_BASIS = NO
```

This decision rests on repository and canonical grounds alone.

## Alternatives Considered

### Pre-materialization relation

```text
PRE_MATERIALIZATION_RELATION = REJECTED_AS_AUTHORITATIVE
```

Rejected as an authoritative relation because the exact final input does not yet exist before
materialization. Any earlier relation could only be an estimate or a reservation.

### Provider-adapter relation

```text
PROVIDER_ADAPTER_RELATION = REJECTED
```

Rejected because it would place provider-neutral policy inside technology adapters and duplicate it
in every adapter.

### F2: Cognition owns the post-selection relation

```text
F2_COGNITION_OWNS_POST_SELECTION_RELATION = REJECTED
```

Cognition would own the relation, and `model_router` would expose the selected resource and its
capacity before execution. Rejected because it:

- requires selected-resource and capacity information to cross back into cognition;
- requires a select, admit, then execute handshake;
- risks splitting the existing route-once and execute-once coherence;
- introduces extra information flow only to move ownership.

It is coherent and not impossible, but it is a larger commitment than F1 with no corresponding
benefit.

### F3: Capacity as selection eligibility

```text
F3_CAPACITY_AS_SELECTION_ELIGIBILITY = OUT_OF_SCOPE_FOR_R3
```

Capacity would participate in choosing which resource is eligible. It is out of scope because it:

- changes resource-selection semantics;
- makes routing input-dependent;
- falls outside R3, which under S1 applies only after one resource has already been selected.

A future routing frontier may consider it.

### U2: Conditional relation

```text
U2_CONDITIONAL_RELATION = REJECTED
```

The relation would be performed only when capacity is known. Rejected because skipping the relation
on UNKNOWN creates weaker, more ambiguous semantics than an explicit `NO_CAPACITY_JUDGMENT`. A
skipped relation is easily read as an implicit allowance.

## Not Decided Here

### Counting

```text
R3_MAY_DEFINE_TOKENIZER = NO
R3_MAY_DEFINE_TOKEN_ESTIMATOR = NO
R3_MAY_DEFINE_PREDICTED_COUNT_AUTHORITY = NO
R8_STATUS = OPEN
```

### Non-context input reservation

```text
PRE_MATERIALIZATION_RESERVATION_REQUIRED_FOR_R3_CORRECTNESS = NO
R5_RESERVATION_POLICY = NOT_DECIDED_HERE
```

Because the relation applies to the complete final input, framing and other non-context input
require no earlier reservation for the relation to be correct. An earlier reservation may still be
useful for efficiency or for another budget concern; this ADR does not decide that.

### Output allocation

```text
OUTPUT_SHARE_OF_CONTEXT_CAPACITY = NOT_DECIDED_HERE
OUTPUT_ALLOWANCE_UNDER_MAX_TOKENS = NOT_DECIDED_HERE
MAX_OUTPUT_CAPABILITY = NOT_DECIDED_HERE
PROVIDER_GENERATION_CAP = NOT_DECIDED_HERE
```

### Overflow

```text
OVERFLOW_DETECTION_POLICY = NOT_DECIDED_HERE
OVERFLOW_RESPONSE = NOT_DECIDED_HERE
TRIMMING = NOT_DECIDED_HERE
RECOMPOSITION = NOT_DECIDED_HERE
REMATERIALIZATION = NOT_DECIDED_HERE
DENIAL = NOT_DECIDED_HERE
RETRY = NOT_DECIDED_HERE
R7_SEMANTIC_OWNER = NOT_DECIDED_HERE
```

Placing the relation after materialization does not restrict which responses a later overflow
policy may adopt, and it does not decide which context owns that policy.

### Budget enforcement

```text
MAX_TOKENS_ENFORCEMENT = NOT_DECIDED_HERE
CUMULATIVE_ACCOUNTING = NOT_DECIDED_HERE
PRE_CALL_BUDGET_ADMISSION = NOT_DECIDED_HERE
POST_HOC_RECONCILIATION = NOT_DECIDED_HERE
USAGE_TELEMETRY = REMAIN_PARKED
```

### Context composition

```text
CONTEXT_COMPOSER = UNCHANGED
CONTEXT_COMPOSER_CAPACITY_AWARE = NO
```

`ContextComposer` remains provider-independent and capacity-agnostic.

### CognitiveBudget max_tokens

```text
MAX_TOKENS_IS_CAPACITY = NO
MODEL_CAPACITY_IS_BUDGET = NO
ADR_0045_MAX_TOKENS_MEANING_CHANGED = NO
ADR_0045_MAX_TOKENS_SCOPE_CHANGED = NO
ADR_0045_ENFORCEMENT_STATUS_CHANGED = NO
```

### Documentation

```text
README_MAX_TOKENS_CLARIFICATION = FOLLOW_UP_DOCUMENTATION_ONLY
README_CHANGE_REQUIRED_BY_ADR_0047 = NO
```

## Consequences

**Positive:**

- The relation between a call's input and model capacity has a defined stage, object, and owner.
- The resource whose capacity is judged is the resource that executes.
- UNKNOWN capacity yields a defined result rather than a skipped step.
- Counting (R8), output allocation (R6), and overflow policy (R7) can now be decided against one
  fixed relation point.
- Cognition, `ContextComposer`, and provider adapters are unaffected.
- No production code, test, configuration, or runtime behavior changes.

**Tradeoffs:**

- A later implementation must change `model_router` structure to evaluate the relation.
- Overflow detected at this stage must be communicated back to whichever context owns the overflow
  response; how is left to R7.
- Capacity cannot yet influence which resource is selected; that requires a separate routing
  decision.

## ADR Relationship

ADR-0047 depends on ADR-0046 (Model effective context capacity authority), which supplies the
authoritative effective capacity fact. ADR-0047 decides only where and by whom that fact is related
to a final input. It supplements ADR-0046 by resolving its R3 non-decision without redefining it,
and supersedes no ADR.

```text
ADR_0047_DEPENDS_ON_ADR_0046 = YES
ADR_0047_SUPPLEMENTS_ADR_0046 = YES
SUPERSEDES = NONE
```

```text
ADR-0029 = NOT_AFFECTED
ADR-0030 = NOT_AFFECTED
ADR-0032 = NOT_AFFECTED
ADR-0033 = NOT_AFFECTED
ADR-0045 = NOT_AFFECTED
ADR-0046 = SUPPLEMENTED
```

ADR-0047 introduces no structural change to any frozen ADR-0005 component.
