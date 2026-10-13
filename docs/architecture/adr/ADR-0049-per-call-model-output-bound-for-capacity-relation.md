# ADR-0049: Per-Call Model Output Bound for Capacity Relation

- Status: Accepted
- Date: 2026-10-13

## Context

ADR-0046 defines a model resource's effective context capacity as the maximum combined number of
model-input and model-output tokens that one call may use, and makes it a declared resource fact
owned by `model_router`. ADR-0047 places the relation between one call and that capacity inside
`model_router`, after materialization and resource selection and before provider execution.
ADR-0048 defines how the input side of that relation is counted:

```text
MODEL_EFFECTIVE_CONTEXT_CAPACITY = combined input + output tokens usable by one call
R3_COUNTING_OBJECT = EXACT_FINAL_MODEL_INPUT_OF_ONE_CALL
MODEL_INPUT_CAPACITY_RELATION_STAGE = FINAL_INPUT_PRE_PROVIDER
CAPACITY_RELATION_POLICY_OWNER = MODEL_ROUTER
R8_NUMERIC_COUNT_UNIT = TOKENS_OF_SELECTED_RESOURCE
CURRENT_R8_COUNT_STATUS_SET = EXACT | COUNT_UNAVAILABLE
PROVIDER_TRANSFORMATION_OVERHEAD = OPEN_EXTERNAL_BOUNDARY
```

The output side of the relation remains open. ADR-0046 records `R6_OUTPUT_RESERVATION` as not
decided, and ADR-0047 states that, for a resource whose capacity is known, the content of the
judgment depends on any output share of capacity (R6). ADR-0047 and ADR-0048 both record
`OUTPUT_SHARE_OF_CONTEXT_CAPACITY = NOT_DECIDED_HERE`.

Because capacity is a combined input-plus-output quantity, a relation with no output-side term can
only compare the input count against a quantity that already includes room for output. It can show
that input alone exceeds capacity; it cannot show that the input together with the output a call is
permitted to generate fits within capacity.

The current repository state is:

```text
OUTPUT_BOUND_EXISTS_IN_DOMAIN = NO
OUTPUT_BOUND_EXISTS_IN_CONFIG = NO
PROVIDER_EXECUTION_OPTIONS_PASSED = NO
CAPACITY_RELATION_IMPLEMENTED = NO
```

This ADR decides whether an explicit per-call output quantity participates in the Noema-side
capacity relation and, since it does, its meaning, classification, owner, value source, timing,
unit, zero semantics, and absence semantics. It decides nothing else.

## Decision

### Terminology

```text
R6_SELECTED_TERM = PER_CALL_MODEL_OUTPUT_BOUND
```

Earlier material named R6 "output reservation" or "output share". The selected concept is neither
residual capacity nor a proportional share derived from capacity. It is a normative bound on the
output of one call. The rest of this ADR calls it the **output bound**.

### Existence

```text
SELECTED_R6_EXISTENCE_POLICY = E1_EXPLICIT_NORMATIVE_PER_CALL_OUTPUT_BOUND
```

The architecture has an explicit output-side quantity that participates in the capacity relation
of ADR-0047.

### Meaning

```text
OUTPUT_CAPACITY_BOUND_MEANING = NORMATIVE_MAXIMUM_OUTPUT_TOKENS_FOR_ONE_CALL
```

The output bound is the maximum number of output tokens that one model call is permitted to
generate under Noema policy.

The output bound is distinct from neighboring quantities:

```text
OUTPUT_BOUND_IS_RESIDUAL_CAPACITY = NO
OUTPUT_BOUND_IS_RESOURCE_CAPABILITY = NO
OUTPUT_BOUND_IS_PROVIDER_GENERATION_PARAMETER = NO
OUTPUT_BOUND_IS_COGNITIVE_BUDGET_REMAINING = NO
```

- **Residual capacity** is the theoretical room left after the input is counted. It is derived,
  not permitted: it says how much output could fit, not how much output is allowed.
- **Resource capability** is a possible future fact about how much output a model resource can
  generate. A fact about the resource is not a policy about its use.
- **A provider generation parameter** is a possible enforcement mechanism. A mechanism realizes a
  bound; it does not define one.
- **Remaining `CognitiveBudget.max_tokens`** is derived from a cumulative per-`ReasoningRequest`
  policy defined by ADR-0045. It is not a per-call bound.

### Classification

```text
OUTPUT_BOUND_CLASSIFICATION = CALL_POLICY
RESOURCE_HAS_INHERENT_OUTPUT_SHARE = NO
```

Effective context capacity remains a resource fact under ADR-0046. The output bound is a Noema
policy that restricts how that capacity is used by one call. No resource has an inherent output
share.

The output bound:

- never increases capacity;
- never replaces UNKNOWN capacity with known capacity;
- remains semantically distinct from the capacity fact.

These are the constraints ADR-0046 places on any operator policy that restricts permitted use.

### Ownership

```text
SELECTED_R6_POLICY_OWNER = MODEL_ROUTER
SEMANTIC_POLICY_OWNER = MODEL_ROUTER
VALUE_SOURCE = RESOURCE_ASSOCIATED_MODEL_ROUTER_POLICY_CONFIGURATION
MECHANISM_ENFORCER = NOT_DECIDED_HERE
CAPACITY_RELATION_CONSUMER = MODEL_ROUTER
```

- **Semantic policy owner:** `model_router` owns the meaning of the output bound, alongside the
  capacity fact (ADR-0046), the capacity relation (ADR-0047), and the count policy (ADR-0048).
- **Value source:** policy configuration associated with the configured model resource. The
  configuration supplies the value; it does not own the policy.
- **Mechanism enforcer:** not decided here.
- **Consumer:** the `model_router` capacity relation. Other consumers are not decided here.

### Value source

```text
SELECTED_OUTPUT_BOUND_VALUE_SOURCE = V1_MODEL_ROUTER_POLICY_CONFIGURATION
CONFIGURED_OUTPUT_BOUND_IS_RESOURCE_FACT = NO
CONFIGURED_OUTPUT_BOUND_IS_POLICY = YES
CONFIGURED_POLICY_SCOPE = RESOURCE_ASSOCIATED_POLICY
```

The value of the output bound comes from `model_router` policy configuration associated with a
configured model resource. The scope is per resource, not global, because the bound is denominated
in the tokens of a specific resource and ADR-0045 leaves cross-resource token commensurability
undecided; a single global integer would have no fixed unit.

The configured value is a policy, not a fact. It must remain distinguishable from the declared
capacity fact of ADR-0046 even though both are associated with the same configured resource.

This ADR chooses no configuration key, schema, environment variable, field name, class, or DTO.

### Caller-supplied value

```text
CALLER_SUPPLIED_OUTPUT_BOUND = REJECTED_FOR_CURRENT_R6_POLICY
```

A caller-supplied output bound is not part of the current policy:

- under ADR-0047, cognition hands over the materialized input before resource selection;
- cognition does not know the selected resource or its effective context capacity;
- a bare integer could technically be interpreted in the selected resource's tokens after
  selection, but cognition cannot choose a meaningful bound on capacity use without knowing that
  capacity;
- deriving the caller's value from remaining `max_tokens` would prematurely merge R6 with R4.

This ADR does not hold that a caller-supplied value is impossible in principle. A later decision
may revisit it.

### Timing

```text
SELECTED_OUTPUT_BOUND_TIMING = AFTER_RESOURCE_SELECTION_BEFORE_CAPACITY_RELATION
OUTPUT_BOUND_MUST_BE_FIXED_NO_LATER_THAN = CAPACITY_RELATION_EVALUATION
PROVIDER_ADAPTER_TIME_IS_TOO_LATE = YES
```

The policy value may already exist in configuration. It becomes applicable to a call through the
selected resource, after selection and before the capacity relation is evaluated. It must be fixed
no later than that evaluation. Provider-adapter time is too late, because the relation precedes
provider execution under ADR-0047.

### Unit

```text
R6_NUMERIC_UNIT = TOKENS_OF_SELECTED_RESOURCE
```

The output bound is a number of tokens of the selected resource, the same unit as the ADR-0048
input count. No generic token unit, conversion ratio, or inferred tokenizer is introduced.

### Zero

```text
OUTPUT_BOUND_ZERO_SEMANTICS = ZERO_VALID_MEANS_NO_OUTPUT_TOKENS_PERMITTED
```

An output bound of `0` is valid and permits no output tokens for the call. This is a per-call
policy value and is separate from ADR-0045's `CognitiveBudget.max_tokens = 0`, which permits no
model tokens for a whole `ReasoningRequest`. Provider conventions such as "0 means unlimited" or
"0 means default" are not imported.

### Absence

```text
OUTPUT_BOUND_ABSENCE_POLICY = ABSENCE_ALLOWED_INCOMPLETE_RELATION
ABSENCE_IS_ZERO = NO
ABSENCE_IS_UNLIMITED = NO
ABSENCE_IS_DEFAULT_VALUE = NO
ABSENCE_RELATION_SEMANTICS = INPUT_ONLY_INCOMPLETE_CAPACITY_RELATION
```

The architecture has an output bound. An individual selected resource may nevertheless have no
configured output bound. In that case:

- absence is not zero, not unlimited, and not a default value;
- no value is substituted;
- the relation for that call is input-only and incomplete;
- the architecture does not pretend the call has a complete bounded input-plus-output relation.

Absence for one resource is a defined state under the selected policy. It does not mean that the
rejected no-output-term alternative was selected.

### Semantic shape

```text
MINIMUM_R6_SEMANTIC_SHAPE = OPTIONAL_NON_NEGATIVE_INTEGER
```

This is a semantic shape only. No type is designed here.

### COUNT_UNAVAILABLE

```text
OUTPUT_BOUND_CAN_EXIST_WHEN_INPUT_COUNT_UNAVAILABLE = YES
CAPACITY_RELATION_CAN_PRODUCE_COMPLETE_JUDGMENT_WHEN_INPUT_COUNT_UNAVAILABLE = NO
KNOWN_CAPACITY_COUNT_UNAVAILABLE_RESULT = NOT_DECIDED_HERE
```

The output bound is policy and can exist whatever the input count status. When the input count is
COUNT_UNAVAILABLE, the relation cannot produce a complete judgment, even with an output bound.
COUNT_UNAVAILABLE must not be interpreted as zero, infinity, a predicted count, a fit, or an
overflow. The outcome for a known capacity with an unavailable count belongs to R7.

### UNKNOWN capacity

```text
R6_DOES_NOT_REDEFINE_UNKNOWN_CAPACITY = YES
OUTPUT_BOUND_CAN_EXIST_WHEN_CAPACITY_UNKNOWN = YES
```

The output bound can exist for a resource whose capacity is UNKNOWN. ADR-0047 remains
authoritative: when effective context capacity is UNKNOWN, the relation's result is
`NO_CAPACITY_JUDGMENT`. The presence of an output bound does not change that.

### Noema-side bounded relation

When capacity is known, the input count is EXACT, and an output bound is present, the Noema-side
bounded relation is:

```text
NOEMA_SIDE_BOUNDED_RELATION =
    EXACT_NOEMA_INPUT_COUNT + NORMATIVE_OUTPUT_BOUND <= EFFECTIVE_CONTEXT_CAPACITY
```

All three terms are in tokens of the selected resource.

```text
NOEMA_SIDE_BOUNDED_RELATION_PROVES_PROVIDER_ACTUAL_FIT = NO
PROVIDER_ACTUAL_FIT_CLAIM_AUTHORIZED = NO
```

This is a Noema policy relation, not a provider actual capacity fit. ADR-0048 excludes any framing
or transformation a provider adds from the input count and leaves that overhead as an open external
boundary. A relation that holds on the Noema side therefore does not prove that the call fits the
provider's actual consumption, and no component may claim that it does.

What R7 concludes from the relation, including whether it holds, is not decided here.

### Provider overhead

```text
PROVIDER_ADDED_INPUT_OVERHEAD_AUTHORITY = NOT_DECIDED_HERE
PROVIDER_TRANSFORMATION_OVERHEAD = OPEN_EXTERNAL_BOUNDARY
```

This ADR introduces no overhead estimator, overhead reserve, provider tokenizer, safety margin, or
provider-specific fit guarantee.

### Runtime soundness

```text
R6_BOUND_REQUIRES_EVENTUAL_ENFORCEMENT_FOR_RUNTIME_SOUNDNESS = YES
BOUND_ENFORCEMENT_MECHANISM = NOT_DECIDED_HERE
PROVIDER_GENERATION_CAP = NOT_DECIDED_HERE
```

A preventive bounded relation is operationally sound only if runtime output is actually constrained
so that it cannot exceed the output bound. This ADR selects the semantic authority of the bound,
not its enforcement. Until a mechanism honors the bound, runtime code must not claim that the
bounded relation is operationally sound.

### Policy versus mechanism

```text
OUTPUT_BOUND_SEMANTIC_AUTHORITY != PROVIDER_GENERATION_CAP
```

A future provider-native generation limit may be one enforcement mechanism, if it faithfully
realizes the selected bound. This ADR neither requires nor selects one. A provider adapter is a
mechanism, not the owner of the policy.

### Relation to R4

```text
R6_OUTPUT_BOUND_MAY_BE_NARROWED_BY_R4_LATER = YES
R6_OUTPUT_BOUND_EQUALS_REMAINING_MAX_TOKENS = NO
R6_OUTPUT_BOUND_AUTHORITY_IS_MAX_TOKENS = NO
R4_MAX_TOKENS_ENFORCEMENT = NOT_DECIDED_HERE
R4_CUMULATIVE_ACCOUNTING = NOT_DECIDED_HERE
```

A later budget-enforcement decision may narrow the output bound for a call. The output bound is not
the remaining `max_tokens`, and `max_tokens` is not its authority. No narrowing algorithm or
precedence is defined here.

### Relation to model max-output capability

```text
MODEL_MAX_OUTPUT_CAPABILITY_AUTHORITY = NOT_DECIDED_HERE
FUTURE_MODEL_MAX_OUTPUT_CAPABILITY_MAY_NARROW_R6_BOUND = YES
R6_BOUND_EQUALS_MODEL_MAX_OUTPUT_CAPABILITY = NO
```

A future model max-output capability fact, if one is introduced, may narrow the output bound. It is
not the same concept. This ADR introduces no resource field for it.

### Relation to R7

```text
R7_OVERFLOW_DETECTION = NOT_DECIDED_HERE
R7_OVERFLOW_RESPONSE = NOT_DECIDED_HERE
R7_RESPONSE_OWNER = NOT_DECIDED_HERE
KNOWN_CAPACITY_COUNT_UNAVAILABLE_RESULT = NOT_DECIDED_HERE
```

ADR-0049 provides R7 with the output-side normative term of the capacity relation. It does not
decide how R7 interprets capacity-relation outcomes or how it reacts to them.

### Structural implications

```text
MODEL_RESOURCE_CONFIGURATION_CHANGE_REQUIRED = YES
MODEL_ROUTER_CHANGE_REQUIRED = YES
MODEL_EXECUTION_REQUEST_CHANGE_REQUIRED = DEPENDS_ON_ENFORCEMENT_MECHANISM
PROVIDER_ADAPTER_CHANGE_REQUIRED = DEPENDS_ON_ENFORCEMENT_MECHANISM
COGNITION_CHANGE_REQUIRED = NO
NEW_PORT_REQUIRED = NO
NEW_DEPENDENCY_REQUIRED = NO
```

These are future consequences only. A future implementation needs optional resource-associated
policy configuration, whose absence leaves the output bound absent, and `model_router` support for
the bound in the capacity relation. Whether `ModelExecutionRequest` or a provider adapter changes
depends on the enforcement mechanism, which is not decided here. The value is delivered through the
composition root, as ADR-0046 already establishes for resource declarations.

### Implementation state

```text
IMPLEMENTATION_AUTHORIZED = NO
TEST_CHANGES_AUTHORIZED = NO
IMPLEMENTATION_REQUIRED = NO
TEST_CHANGES_REQUIRED = NO
```

This ADR establishes semantic architecture only. No production code, test, configuration, or
runtime behavior changes. A later explicit gate is required for implementation.

### Milestone state

```text
NEXT_MILESTONE_IDENTIFIER = UNASSIGNED
M0_19_ASSIGNED = NO
```

### Normative assignments

```text
R6_SELECTED_TERM = PER_CALL_MODEL_OUTPUT_BOUND
SELECTED_R6_EXISTENCE_POLICY = E1_EXPLICIT_NORMATIVE_PER_CALL_OUTPUT_BOUND
OUTPUT_CAPACITY_BOUND_MEANING = NORMATIVE_MAXIMUM_OUTPUT_TOKENS_FOR_ONE_CALL
OUTPUT_BOUND_CLASSIFICATION = CALL_POLICY
SELECTED_R6_POLICY_OWNER = MODEL_ROUTER
SELECTED_OUTPUT_BOUND_VALUE_SOURCE = V1_MODEL_ROUTER_POLICY_CONFIGURATION
CONFIGURED_OUTPUT_BOUND_IS_RESOURCE_FACT = NO
CONFIGURED_OUTPUT_BOUND_IS_POLICY = YES
CONFIGURED_POLICY_SCOPE = RESOURCE_ASSOCIATED_POLICY
SELECTED_OUTPUT_BOUND_TIMING = AFTER_RESOURCE_SELECTION_BEFORE_CAPACITY_RELATION
OUTPUT_BOUND_MUST_BE_FIXED_NO_LATER_THAN = CAPACITY_RELATION_EVALUATION
R6_NUMERIC_UNIT = TOKENS_OF_SELECTED_RESOURCE
OUTPUT_BOUND_ZERO_SEMANTICS = ZERO_VALID_MEANS_NO_OUTPUT_TOKENS_PERMITTED
OUTPUT_BOUND_ABSENCE_POLICY = ABSENCE_ALLOWED_INCOMPLETE_RELATION
ABSENCE_IS_ZERO = NO
ABSENCE_IS_UNLIMITED = NO
ABSENCE_IS_DEFAULT_VALUE = NO
MINIMUM_R6_SEMANTIC_SHAPE = OPTIONAL_NON_NEGATIVE_INTEGER
OUTPUT_BOUND_CAN_EXIST_WHEN_INPUT_COUNT_UNAVAILABLE = YES
CAPACITY_RELATION_CAN_PRODUCE_COMPLETE_JUDGMENT_WHEN_INPUT_COUNT_UNAVAILABLE = NO
R6_DOES_NOT_REDEFINE_UNKNOWN_CAPACITY = YES
OUTPUT_BOUND_CAN_EXIST_WHEN_CAPACITY_UNKNOWN = YES
NOEMA_SIDE_BOUNDED_RELATION_PROVES_PROVIDER_ACTUAL_FIT = NO
PROVIDER_ACTUAL_FIT_CLAIM_AUTHORIZED = NO
R6_BOUND_REQUIRES_EVENTUAL_ENFORCEMENT_FOR_RUNTIME_SOUNDNESS = YES
BOUND_ENFORCEMENT_MECHANISM = NOT_DECIDED_HERE
R6_OUTPUT_BOUND_MAY_BE_NARROWED_BY_R4_LATER = YES
R6_OUTPUT_BOUND_EQUALS_REMAINING_MAX_TOKENS = NO
R6_OUTPUT_BOUND_AUTHORITY_IS_MAX_TOKENS = NO
FUTURE_MODEL_MAX_OUTPUT_CAPABILITY_MAY_NARROW_R6_BOUND = YES
R6_BOUND_EQUALS_MODEL_MAX_OUTPUT_CAPABILITY = NO
KNOWN_CAPACITY_COUNT_UNAVAILABLE_RESULT = NOT_DECIDED_HERE
PROVIDER_TRANSFORMATION_OVERHEAD = OPEN_EXTERNAL_BOUNDARY
IMPLEMENTATION_AUTHORIZED = NO
TEST_CHANGES_AUTHORIZED = NO
M0_19_ASSIGNED = NO
```

## Rationale

- **Capacity is combined, so the relation needs an output term.** ADR-0046 defines capacity over
  input plus output. Without an output-side quantity, the relation of ADR-0047 can only detect that
  input alone is too large; it can never establish that a call's permitted input and output fit.
- **A bound, not residual room.** Only a normative maximum states how much output a call is
  permitted. Residual room states only how much could fit, and makes the relation trivially true.
- **It is fail-closed in meaning.** An absent bound leaves an explicitly incomplete relation rather
  than an implied fit, and no value is substituted for absence, UNKNOWN, or COUNT_UNAVAILABLE.
- **`model_router` is the coherent owner.** It already owns the capacity fact, the relation, and
  the count policy, and the bound is applied where those meet.
- **Resource-associated configuration keeps the unit defined.** The bound is denominated in the
  selected resource's tokens, which a per-resource value preserves and a global value would not.
- **Cognition stays unaware of resources.** Cognition continues to hand `model_router` a
  materialized string under ADR-0047, and needs no resource or capacity knowledge.
- **It is provider-neutral.** The bound is policy; any provider limit is a replaceable mechanism,
  consistent with ADR-0002 and ADR-0003.
- **It keeps neighboring frontiers open.** Budget enforcement, max-output capability, overflow
  policy, and provider overhead remain separate decisions that may narrow or interpret the bound.

### External-provider evidence boundary

```text
PROVIDER_EMPIRICAL_DATA_REQUIRED = NO
PROVIDER_SPECIFIC_NUMERIC_FACTS_REQUIRED = NO
```

This decision rests on repository and canonical grounds alone.

## Alternatives Considered

### F0: No explicit output term

```text
F0_NO_EXPLICIT_OUTPUT_TERM = REJECTED
```

No output-side quantity would participate in the relation. Rejected as the selected architecture
because it permits only an input-only necessary test and cannot establish the Noema-side permitted
input-plus-output relation. A resource without a configured bound under the selected policy has an
explicitly incomplete relation; that is a defined state of E1, not a selection of F0.

### F2: Caller-supplied per-call output bound

```text
F2_CALLER_SUPPLIED_PER_CALL_OUTPUT_BOUND = REJECTED_FOR_CURRENT_R6_POLICY
```

The caller would supply the bound before resource selection, and `model_router` would interpret it
in the selected resource's tokens afterward. Rejected for the current policy because cognition
does not possess selected-resource capacity knowledge, and using remaining `max_tokens` as its
principled source would prematurely merge R6 with R4. It is not prohibited in principle.

### O3: Residual capacity

```text
O3_RESIDUAL_CAPACITY = REJECTED
```

The output term would be capacity minus the input count. Rejected because it:

- is undefined under COUNT_UNAVAILABLE;
- is not an allowance;
- consumes the theoretical remaining room by definition;
- ignores open provider overhead;
- turns the capacity relation into an input-only tautology.

### Output bound as a resource fact

```text
OUTPUT_BOUND_AS_RESOURCE_FACT = REJECTED
```

Rejected because the output bound is a policy restricting use of capacity, not an intrinsic
property of the resource. Treating it as a fact would also contradict ADR-0046, under which a
declaration made to restrict use is a misdeclaration rather than a policy mechanism.

### Provider authority

```text
PROVIDER_ADAPTER_AS_OUTPUT_BOUND_AUTHORITY = REJECTED
```

Rejected because a provider adapter is a mechanism, not the semantic policy owner, and its time of
action is later than the capacity relation.

## Not Decided Here

This ADR does not decide:

- `CognitiveBudget.max_tokens` enforcement;
- cumulative `ReasoningRequest` accounting;
- allocation of `max_tokens` across calls;
- pre-materialization reservation;
- overflow detection;
- overflow response;
- response ownership;
- the outcome for known capacity with a COUNT_UNAVAILABLE input count;
- provider transformation overhead authority;
- provider actual token usage;
- actual-usage reconciliation;
- model maximum-output capability authority;
- a provider generation-cap API or mechanism;
- the tokenizer or counting mechanism.

```text
R4_MAX_TOKENS_ENFORCEMENT = NOT_DECIDED_HERE
R4_CUMULATIVE_ACCOUNTING = NOT_DECIDED_HERE
MAX_TOKENS_ALLOCATION_ACROSS_CALLS = NOT_DECIDED_HERE
R5_PRE_MATERIALIZATION_RESERVATION = NOT_DECIDED_HERE
R7_OVERFLOW_DETECTION = NOT_DECIDED_HERE
R7_OVERFLOW_RESPONSE = NOT_DECIDED_HERE
R7_RESPONSE_OWNER = NOT_DECIDED_HERE
KNOWN_CAPACITY_COUNT_UNAVAILABLE_RESULT = NOT_DECIDED_HERE
PROVIDER_ADDED_INPUT_OVERHEAD_AUTHORITY = NOT_DECIDED_HERE
MODEL_MAX_OUTPUT_CAPABILITY_AUTHORITY = NOT_DECIDED_HERE
PROVIDER_GENERATION_CAP = NOT_DECIDED_HERE
BOUND_ENFORCEMENT_MECHANISM = NOT_DECIDED_HERE
ACTUAL_USAGE_TELEMETRY = REMAIN_PARKED
POST_CALL_RECONCILIATION = NOT_DECIDED_HERE
TOKENIZER_OR_COUNTING_MECHANISM = NOT_DECIDED_HERE
CROSS_RESOURCE_TOKEN_COMMENSURABILITY = NOT_DECIDED_HERE
```

### Pre-materialization reservation

The output bound is a per-call policy applied at the capacity relation. It is not a
`ContextComposer` reservation and does not change composition. `ContextComposer` remains
provider-independent and capacity-agnostic, and `ContextRequest.max_total_content_size` remains a
raw Unicode code-point budget under ADR-0030.

### Token counting

ADR-0048 remains authoritative for counting the input side of the relation. This ADR does not
change the counting object, unit, status set, or token-space authority.

### Documentation

```text
README_MAX_TOKENS_CLARIFICATION = FOLLOW_UP_DOCUMENTATION_ONLY
README_CHANGE_REQUIRED_BY_ADR_0049 = NO
```

## Consequences

**Positive:**

- Known-capacity reasoning gains an explicit output-side policy term.
- `model_router` retains ownership of capacity policy.
- The resource capacity fact and operator policy remain distinct.
- Provider neutrality is preserved.
- R7 can later reason from a bounded output term.
- R4 may later narrow the bound without becoming its authority.
- No production code, test, configuration, or runtime behavior changes.

**Costs and limitations:**

- Resource-associated policy configuration will eventually be required.
- `model_router` requires future structural support for the bound.
- Runtime soundness is incomplete until an enforcement mechanism exists.
- Absence of a configured bound still yields an incomplete, input-only relation.
- COUNT_UNAVAILABLE still prevents a complete judgment.
- UNKNOWN capacity still yields `NO_CAPACITY_JUDGMENT`.
- Provider actual fit remains unproven while provider overhead is open.
- A per-call output bound adds another operator-facing token quantity alongside the capacity fact
  and `CognitiveBudget.max_tokens`; the three must be kept distinct in configuration and
  documentation.

## ADR Relationship

ADR-0049 supplements ADR-0046 and ADR-0047, and supersedes no ADR.

- ADR-0049 supplements ADR-0046 by resolving its deferred output reservation concern as a policy
  bound, without changing effective-capacity authority or the UNKNOWN state.
- ADR-0049 supplements ADR-0047 by supplying the output-side term that its known-capacity relation
  depends on, without changing the relation's stage, object, owner, or UNKNOWN result.
- ADR-0045 is not affected, because `max_tokens` meaning, enforcement, and accounting are not
  decided or changed here.
- ADR-0048 is not affected, because input-counting semantics are unchanged.

```text
ADR_0049_SUPPLEMENTS_ADR_0046 = YES
ADR_0049_SUPPLEMENTS_ADR_0047 = YES
SUPERSEDES = NONE
```

```text
ADR-0045 = NOT_AFFECTED
ADR-0046 = SUPPLEMENTED
ADR-0047 = SUPPLEMENTED
ADR-0048 = NOT_AFFECTED
```

ADR-0049 introduces no structural change to any frozen ADR-0005 component.
