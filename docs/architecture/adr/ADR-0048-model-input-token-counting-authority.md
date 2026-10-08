# ADR-0048: Model Input Token Counting Authority

- Status: Accepted
- Date: 2026-10-08

## Context

ADR-0045 defines `CognitiveBudget.max_tokens` in tokens of the model resource executing each call,
and states that it defines what a token denotes, not how tokens are counted. ADR-0046 made a
resource's effective context capacity a declared resource fact. ADR-0047 fixed the object that a
capacity relation relates to that capacity:

```text
R3_COUNTING_OBJECT = EXACT_FINAL_MODEL_INPUT_OF_ONE_CALL
```

Both ADR-0046 and ADR-0047 left token counting open:

```text
R8_TOKENIZER_ESTIMATION = NOT_DECIDED_HERE
R8_STATUS = OPEN
```

The current repository state is:

```text
TOKEN_COUNTING_IMPLEMENTED = NO
TOKEN_SPACE_RUNTIME_REPRESENTATION_IMPLEMENTED = NO
TOKENIZER_LIBRARY_PRESENT = NO
PROVIDER_NATIVE_COUNTING_PRESENT = NO
```

- No source module counts tokens, and no locked dependency is a tokenizer library.
- The provider SDK used by the current adapter exposes no pre-call counting operation. Its token
  usage fields are reported only after a call, as part of the parked usage frontier.
- The strict `[runtime.model]` configuration table can express neither a tokenizer identity nor a
  counting capability.

These absences describe the current implementation. They are not the reasons for this decision.

This ADR decides what authority determines the token count of the counting object, and what
semantic statuses that count may have. It decides nothing else.

## Decision

### Counting object

```text
R8_COUNTING_OBJECT = EXACT_FINAL_MODEL_INPUT_OF_ONE_CALL
R8_OBJECT_INCLUDES_PROVIDER_ADDED_TRANSFORMATION = NO
```

The counted object is the fully materialized final model input supplied by Noema for one model
call, as fixed by ADR-0047. It does not include any framing or transformation a provider may add.

### Numeric unit

```text
R8_NUMERIC_COUNT_UNIT = TOKENS_OF_SELECTED_RESOURCE
GENERIC_TOKEN_LIKE_ESTIMATE_IS_R8_TOKEN_COUNT = NO
```

A count is a number of tokens of the selected model resource. The unit is resource-relative,
consistent with ADR-0045. No generic, resource-independent "token-like" unit is defined, and an
estimate in such a unit is not a count under this ADR.

### Token-space authority

```text
SELECTED_TOKEN_SPACE_AUTHORITY = T1_DECLARED_RESOURCE_TOKEN_SPACE_IDENTITY
TOKEN_SPACE_IDENTITY_SOURCE = DECLARATION_ASSOCIATED_WITH_CONFIGURED_RESOURCE
TOKEN_SPACE_IDENTITY_OWNER = MODEL_ROUTER
TOKEN_SPACE_IDENTITY_CAN_BE_UNKNOWN = YES
UNKNOWN_TOKEN_SPACE_IMPLIES_DEFAULT_TOKENIZER = NO
```

A resource's token-space identity is an authoritative declared fact associated with the configured
model resource. It determines the tokenization semantics needed to interpret "tokens of the selected
resource". `model_router` owns its meaning.

This follows the semantic declared-resource-fact pattern that ADR-0046 established for effective
context capacity. It does not redefine that capacity.

```text
TOKEN_SPACE_DECLARATION_IS_POLICY = NO
TOKEN_SPACE_DECLARATION_IS_FACT_SOURCE = YES
```

The declaration is a statement of fact about the resource, not a policy. When no declaration
exists, the token-space identity is UNKNOWN.

### Opaque references

```text
TOKEN_SPACE_IDENTITY_DERIVED_FROM_MODEL_REF = NO
TOKEN_SPACE_IDENTITY_DERIVED_FROM_PROVIDER_REF = NO
```

Tokenizer semantics are never inferred from the opaque resource, model, or provider references of a
`ModelResource`. Those references keep their existing meaning: identifiers with no imposed or
inferred format.

### Count statuses

```text
SELECTED_COUNT_STATUS_SET = CS1_EXACT_OR_COUNT_UNAVAILABLE
CURRENT_R8_COUNT_STATUS_SET = EXACT | COUNT_UNAVAILABLE
SELECTED_COUNT_RESULT_SEMANTIC_SHAPE = SUM_TYPE
```

A count has exactly one of two statuses:

- **EXACT** -- an authoritative numeric count produced according to the declared token-space
  semantics of the selected resource over the exact Noema-supplied input.
- **COUNT_UNAVAILABLE** -- no authoritative count can be produced.

```text
COUNT_VALUE_PRESENT_FOR_EXACT = YES
COUNT_VALUE_PRESENT_FOR_COUNT_UNAVAILABLE = NO
```

An EXACT result carries a value. A COUNT_UNAVAILABLE result carries none. No other status is
admitted. This ADR does not decide how the result is represented.

### UNKNOWN token space

```text
COUNT_RESULT_WHEN_TOKEN_SPACE_UNKNOWN = COUNT_UNAVAILABLE
UNKNOWN_TOKEN_SPACE_MEANS_ZERO = NO
UNKNOWN_TOKEN_SPACE_MEANS_DEFAULT = NO
UNKNOWN_TOKEN_SPACE_IMPLIES_PREDICTED = NO
```

When the selected resource's token-space identity is UNKNOWN, the count is COUNT_UNAVAILABLE.
UNKNOWN does not mean zero or unlimited. It does not imply a default tokenizer, an inferred
tokenizer, or a prediction.

### COUNT_UNAVAILABLE

```text
COUNT_UNAVAILABLE_PUBLIC_SEMANTIC = YES
UNAVAILABLE_CAUSES = DIAGNOSTIC_PROVENANCE
```

COUNT_UNAVAILABLE is the single public architectural state for the absence of an authoritative
count. Its possible causes include:

- the token-space identity is unknown;
- no faithful tokenizer mechanism is available;
- the token space is unsupported;
- an external counting mechanism is unavailable.

These causes are diagnostic provenance. They are not distinct architectural states. This ADR
designs no error or reason representation.

### Prediction

```text
CURRENT_R8_PREDICTED_STATUS = NOT_ADMITTED
PREDICTED_COUNT_CURRENTLY_CANONICAL = NO
PREDICTED_BOUNDED = DEFERRED_NOT_PROHIBITED
PREDICTED_UNBOUNDED = NOT_ADMITTED
CONFIDENCE_SCORE = NOT_DECIDED_HERE
NUMERIC_ERROR_BOUND = NOT_DECIDED_HERE
ESTIMATOR_AUTHORITY = NOT_DECIDED_HERE
```

No predicted count is part of the current architecture. A generic PREDICTED status is not admitted,
because later budget enforcement (R4) and overflow policy (R7) could not interpret it safely without
knowing whether it is an upper bound. A future decision may add a bounded prediction status.

Any such future extension is constrained:

```text
FUTURE_PREDICTION_UNIT_INVARIANT = ANY_FUTURE_PREDICTED_R8_COUNT_MUST_BE_BOUND_TO_AN_AUTHORITATIVE_
                                   TOKEN_SPACE_IDENTITY
PRED_A_IS_CURRENT_STATUS = NO
PRED_A_IS_FUTURE_EXTENSION_CONSTRAINT = YES
```

A future predicted count, if one is ever admitted, must still be denominated in the tokens of a
declared, authoritative token space. This is a constraint on future extension, not a status that
exists today.

### Exact counting mechanisms

```text
EXACT_REQUIRES_POST_CALL_USAGE = NO
LOCAL_EXACT_COUNT_SEMANTICALLY_POSSIBLE = DEPENDS
PROVIDER_NATIVE_EXACT_COUNT_SEMANTICALLY_POSSIBLE = DEPENDS
```

A count is exact only if its mechanism faithfully counts the exact Noema-supplied input under the
declared token-space semantics. Such a mechanism may run locally or be provider-native. A
provider-native count is exact only if it counts that same object, not a provider-consumed prompt.
If no faithful mechanism exists for the declared token space, the result is COUNT_UNAVAILABLE; no
substitute tokenizer is used. An exact count requires no post-call usage report.

### Ownership

```text
SELECTED_COUNT_POLICY_OWNER = MODEL_ROUTER
RESOURCE_CONFIGURATION_IS_SOURCE_NOT_POLICY_OWNER = YES
PROVIDER_ADAPTER_IS_MECHANISM_NOT_POLICY_OWNER = YES
```

- **Token-space identity source:** the declaration associated with the configured resource.
- **Count policy owner:** `model_router`, alongside the capacity relation it owns under ADR-0047.
- **Count mechanism provider:** an implementation concern.
- **Count result consumer:** the `model_router` capacity relation immediately. Future consumers are
  not decided here.

### Authority versus mechanism

A tokenizer implementation, library, provider API, estimator, or adapter does not become
architectural authority merely because it computes a number. Authority for what a token is comes
from the declared token-space identity. A mechanism only realizes it.

```text
TOKENIZER_LIBRARY = NOT_DECIDED_HERE
PROVIDER_COUNT_API = NOT_DECIDED_HERE
ESTIMATOR_ALGORITHM = NOT_DECIDED_HERE
NUMERIC_ERROR_BOUND = NOT_DECIDED_HERE
PORT_DESIGN = NOT_DECIDED_HERE
TYPE_DESIGN = NOT_DECIDED_HERE
CONFIG_KEY_DESIGN = NOT_DECIDED_HERE
```

### Provider transformation boundary

```text
NOEMA_SUPPLIED_INPUT_COUNT = count of the exact input text supplied by Noema
PROVIDER_CONSUMED_INPUT_COUNT = the provider's effective consumed input after any provider-added
                                framing or transformation
NOEMA_SUPPLIED_INPUT_COUNT_IS_ALWAYS_PROVIDER_CONSUMED_INPUT_COUNT = NO
PROVIDER_ADDED_INPUT_OVERHEAD_AUTHORITY = NOT_DECIDED_HERE
PROVIDER_TRANSFORMATION_OVERHEAD = OPEN_EXTERNAL_BOUNDARY
```

A provider may add template, system, or special-token framing outside the input Noema supplies. This
ADR counts only the Noema-supplied input. The two counts are not treated as identical, and no
authority for provider-added overhead is decided here.

### What a count does not prove

```text
R8_COUNT_ALONE_PROVES_CONTEXT_CAPACITY_FIT = NO
R8_COUNT_ALONE_PROVES_PROVIDER_CONSUMED_INPUT_SIZE = NO
R8_DEFINES_CAPACITY = NO
R8_DEFINES_CAPACITY_JUDGMENT = NO
R8_DEFINES_OUTPUT_SHARE = NO
R8_DEFINES_OVERFLOW_RESPONSE = NO
```

Even an EXACT count does not by itself prove that an input fits capacity: provider-added overhead
remains open, and any output share of capacity (R6) remains open. This ADR is not an admission
decision.

### Structural implications

```text
MODEL_RESOURCE_CONFIGURATION_CHANGE_REQUIRED = YES
MODEL_ROUTER_CHANGE_REQUIRED = YES
MODEL_EXECUTION_REQUEST_CHANGE_REQUIRED = NO
COGNITION_CHANGE_REQUIRED = NO
PROVIDER_ADAPTER_CHANGE_REQUIRED = DEPENDS
NEW_PORT_REQUIRED = DEPENDS
NEW_DEPENDENCY_REQUIRED = DEPENDS
```

These are future consequences only. A future implementation needs an optional token-space
declaration, whose absence means UNKNOWN, and `model_router` counting behavior. A provider adapter
changes only if a provider-native mechanism is chosen. A port is needed if the mechanism is external
technology, under ADR-0003. A tokenizer library would require its own dependency decision.

```text
IMPLEMENTATION_AUTHORIZED = NO
TEST_CHANGES_AUTHORIZED = NO
```

### Implementation state

```text
IMPLEMENTATION_REQUIRED = NO
TEST_CHANGES_REQUIRED = NO
```

This ADR establishes semantic architecture only. No production code, test, configuration, or runtime
behavior changes. A later explicit gate is required for implementation.

### Milestone state

```text
NEXT_MILESTONE_IDENTIFIER = UNASSIGNED
M0_19_ASSIGNED = NO
```

## Rationale

- **Only a declared token space keeps the unit well defined.** "Tokens of the selected resource"
  requires knowing which tokenization defines a token for that resource.
- **It reuses an established pattern.** ADR-0046 already treats a resource's capacity as a declared
  fact. Token-space identity is another fact of the same kind.
- **It is provider-neutral and deterministic.** A declaration is fixed at configuration time and
  needs no runtime provider I/O.
- **It is fail-closed.** Without an authoritative token space or a faithful mechanism, the count is
  explicitly unavailable rather than approximated.
- **It avoids false authority.** No status claims more than an authoritative exact count supports.
- **It keeps mechanism separate from authority.** Any later tokenizer, library, or provider facility
  is replaceable without changing what a count means.

### External-provider evidence boundary

```text
PROVIDER_EMPIRICAL_DATA_REQUIRED_FOR_R8_DECISION = NO
PROVIDER_DOCUMENTATION_REQUIRED_FOR_R8_DECISION = NO
PROVIDER_SPECIFIC_NUMERIC_FACTS_REQUIRED_FOR_R8_DECISION = NO
```

Repository facts about the current provider SDK motivate rejecting provider discovery as an
authority. The decision does not depend on any provider and remains provider-neutral.

## Alternatives Considered

### T4: No explicit token-space identity

```text
T4_NO_EXPLICIT_TOKEN_SPACE_IDENTITY = REJECTED
```

Rejected because without a token-space identity the selected-resource token unit cannot be defined
coherently.

### T2: Provider discovery

```text
T2_PROVIDER_DISCOVERY = REJECTED
```

Rejected because runtime provider discovery would become the authority and would introduce provider
and runtime coupling. The current repository also lacks any such pre-call mechanism.

### T3: Derivation from model reference

```text
T3_MODEL_REF_DERIVATION = REJECTED
```

Rejected because inferring tokenizer semantics from a model reference violates the opaque-reference
contract of `ModelResource`.

### F2: Declared token space with prediction

```text
F2_DECLARED_TOKEN_SPACE_WITH_PREDICTION = DEFERRED
```

Deferred because a bare prediction is unsafe for downstream consumers. A bounded prediction would
require additional estimator and bound semantics that are not decided here.

### F3: Prediction without a token space

```text
F3_NO_TOKEN_SPACE_PREDICTED = REJECTED
```

Rejected because its numeric unit would not be authoritative tokens of the selected resource.

## Not Decided Here

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
R7_SEMANTIC_OWNER = NOT_DECIDED_HERE
TRIMMING = NOT_DECIDED_HERE
RECOMPOSITION = NOT_DECIDED_HERE
REMATERIALIZATION = NOT_DECIDED_HERE
DENIAL = NOT_DECIDED_HERE
RETRY = NOT_DECIDED_HERE
```

### Budget enforcement

```text
MAX_TOKENS_ENFORCEMENT = NOT_DECIDED_HERE
CUMULATIVE_ACCOUNTING = NOT_DECIDED_HERE
PRE_CALL_BUDGET_ADMISSION = NOT_DECIDED_HERE
POST_HOC_RECONCILIATION = NOT_DECIDED_HERE
ACTUAL_USAGE_TELEMETRY = REMAIN_PARKED
```

### Pre-materialization reservation

```text
PRE_MATERIALIZATION_RESERVATION = NOT_DECIDED_HERE
R5_RESERVATION_POLICY = NOT_DECIDED_HERE
```

### Actual usage

```text
R8_INPUT_COUNT_REQUIRES_POST_CALL_USAGE = NO
ACTUAL_USAGE_TELEMETRY_REQUIRED = NO
POST_CALL_RECONCILIATION = NOT_DECIDED_HERE
```

Usage counts a provider reports after a call are not an authority for counting input before a call.

### Documentation

```text
README_MAX_TOKENS_CLARIFICATION = FOLLOW_UP_DOCUMENTATION_ONLY
README_CHANGE_REQUIRED_BY_ADR_0048 = NO
```

## Consequences

**Positive:**

- "Tokens of the selected resource" now has a defined counting authority.
- A count either carries an authoritative exact value or is explicitly unavailable.
- Capacity relation (ADR-0047), output allocation (R6), and overflow policy (R7) can rely on a fixed
  count meaning.
- Tokenizer and counting mechanisms remain replaceable without changing semantics.
- No production code, test, configuration, or runtime behavior changes.

**Tradeoffs:**

- Every resource's count is unavailable until a token-space declaration and a faithful mechanism
  exist.
- A declared token space may be wrong; it is trusted as declared, as ADR-0046's capacity
  declaration is.
- No approximate count is available for resources whose token space has no faithful mechanism.
- Provider-added input overhead remains unaccounted.

## ADR Relationship

ADR-0048 supplements ADR-0045, ADR-0046, and ADR-0047, and supersedes no ADR.

- ADR-0045's meaning of `max_tokens` is not changed; ADR-0048 gives its token unit a counting
  authority.
- ADR-0046's capacity authority is not changed; ADR-0048 resolves its R8 non-decision through a
  parallel declared resource fact.
- ADR-0047's counting object and boundary are not changed; ADR-0048 defines how that object is
  counted.

```text
ADR_0048_SUPPLEMENTS_ADR_0045 = YES
ADR_0048_SUPPLEMENTS_ADR_0046 = YES
ADR_0048_SUPPLEMENTS_ADR_0047 = YES
SUPERSEDES = NONE
```

```text
ADR-0029 = NOT_AFFECTED
ADR-0030 = NOT_AFFECTED
ADR-0032 = NOT_AFFECTED
ADR-0045 = SUPPLEMENTED
ADR-0046 = SUPPLEMENTED
ADR-0047 = SUPPLEMENTED
```

ADR-0048 introduces no structural change to any frozen ADR-0005 component.
