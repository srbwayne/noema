# ADR-0046: Model Effective Context Capacity Authority

- Status: Accepted
- Date: 2026-10-07

## Context

No component of the repository knows how many tokens a model resource can use in one call.
ADR-0032 recorded this as an explicit deferral, and ADR-0033 restated it:

```text
MODEL_CONTEXT_WINDOW_AUTHORITY = NONE
```

The current state is:

```text
MODEL_CONTEXT_WINDOW_VALUE_EXISTS_IN_DOMAIN = NO
MODEL_CONTEXT_WINDOW_VALUE_EXISTS_IN_CONFIG = NO
MODEL_CONTEXT_WINDOW_RUNTIME_DISCOVERY_EXISTS = NO
MODEL_CONTEXT_WINDOW_RUNTIME_ENFORCEMENT_EXISTS = NO
```

- `ModelResource` carries only the opaque references `resource_ref`, `provider_ref`, and
  `model_ref`.
- `ModelResourceCapabilities` associates a resource with a frozenset of declared `ModelCapability`
  values and, by its own contract, represents declared capabilities only.
- `ModelExecutionRequest` carries only `resource` and `input_text`, and the Ollama adapter passes no
  execution options to the provider.
- The strict `[runtime.model]` configuration table accepts only `resource_ref`, `provider_ref`,
  `model_ref`, and `capabilities`.

ADR-0045 gave `CognitiveBudget.max_tokens` its meaning: a cumulative per-`ReasoningRequest`
input-plus-output token budget, which is not a model context-window capacity. It left open, among
others:

- R2: model context-window capacity authority;
- R9: operator configuration versus model-capability authority.

Post-M0-18 frontier work found that these two roots are coupled and that the remaining capacity
questions depend on them. In particular, the boundary between composition and model capacity (R3)
and model-capacity overflow policy (R7) cannot be decided while no capacity fact can exist.
Selecting a tokenizer (R8) also depends on how resource-specific facts are sourced. This ADR
decides which authority governs a model resource's effective context capacity and how operator
configuration relates to it. It decides nothing else.

## Decision

### Governed fact

```text
MODEL_EFFECTIVE_CONTEXT_CAPACITY = maximum combined model-input + model-output tokens usable by one
                                   model call under the resource's effective runtime configuration
```

A model resource's effective context capacity is the maximum combined number of model-input and
model-output tokens, denominated in that resource's tokens, that one model call may use under the
resource's effective runtime configuration. The fact is call-scoped and resource-specific. Its
token unit is the unit ADR-0045 already defines for the executing model resource.

The governed fact is distinct from neighboring quantities:

```text
TRAINED_MODEL_MAXIMUM_IS_SAME_FACT = NO
MAX_OUTPUT_GENERATION_IS_SAME_FACT = NO
OPERATOR_POLICY_LIMIT_IS_SAME_FACT = NO
COGNITIVE_BUDGET_MAX_TOKENS_IS_SAME_FACT = NO
```

- The maximum context a model was trained for may differ from what its effective runtime
  configuration permits.
- A limit on generated output covers only part of one call's tokens.
- An operator policy limit is a policy about permitted use, not a fact about the resource.
- `CognitiveBudget.max_tokens` is a cognition-side budget for a whole `ReasoningRequest`, not a
  per-call resource fact.

### Selected authority

```text
SELECTED_D1_POLICY = P2_DECLARED_RESOURCE_CAPACITY
MODEL_EFFECTIVE_CONTEXT_CAPACITY_AUTHORITY = DECLARED_RESOURCE_FACT
DECLARER = OPERATOR_AT_CONFIGURATION_TIME
DECLARATION_IS_POLICY_LIMIT = NO
```

The canonical source of a model resource's effective context capacity is a declaration that:

- is associated with the configured model resource;
- is made at configuration time;
- states a fact about that resource;
- is not a policy limit;
- is trusted as declared in this architectural phase;
- may be absent.

The declaration has the same standing that `ModelResourceCapabilities` declarations already have:
an operator-supplied statement of fact about the configured resource, resolved at configuration
time and trusted without verification. A declaration deliberately set below the resource's real
capacity in order to restrict use is a misdeclaration, not a policy mechanism.

```text
DECLARATION_VERIFICATION = NOT_DECIDED_HERE
PROVIDER_DISCOVERY = NOT_DECIDED_HERE
```

This ADR does not guarantee that a declaration is physically correct. Verifying a declaration
against the provider, and discovering capacity from the provider, are separate later decisions.

### UNKNOWN capacity

```text
CAPACITY_UNKNOWN_IS_VALID_STATE = YES
UNKNOWN_CAPACITY_MEANS_ZERO = NO
UNKNOWN_CAPACITY_MEANS_UNLIMITED = NO
UNKNOWN_CAPACITY_MEANS_OPERATOR_LIMIT_BECOMES_CAPACITY = NO
```

A model resource with no capacity declaration has UNKNOWN effective context capacity. UNKNOWN means
that Noema has no authoritative knowledge of the resource's effective context capacity. No
capacity-derived conclusion may be asserted from UNKNOWN. UNKNOWN is neither zero nor unlimited, and
no other value may be substituted for it.

This ADR does not define runtime handling for UNKNOWN.

### Operator policy relation

```text
SELECTED_D2_POLICY = D2A_NO_OPERATOR_POLICY_LIMIT_CONCEPT_YET
OPERATOR_CAPACITY_POLICY_LIMIT = NOT_DEFINED
```

This ADR defines resource capacity only. No separate operator limit that narrows capacity is
introduced, and no configuration key for one exists. Operator configuration relates to capacity
only as the channel through which the capacity fact is declared. It is not a second capacity
authority.

Any future operator policy limit must:

- remain distinct from the capacity fact;
- only narrow permitted use;
- never increase capacity;
- never replace UNKNOWN with known capacity.

### Semantic ownership

```text
MODEL_CAPACITY_SEMANTIC_OWNER_CONTEXT = MODEL_ROUTER
RESOLVED_CAPABILITY_OBJECT_IS_AUTHORITY = NO
RESOLVED_CAPABILITY_OBJECT_IS_DELIVERY_MECHANISM = YES
CONCRETE_TYPE_DESIGN = NOT_DECIDED_HERE
MODEL_RESOURCE_CAPABILITIES_FIELD_CHANGE = NOT_DECIDED_HERE
NEW_VALUE_OBJECT = NOT_DECIDED_HERE
```

- **Semantic owner:** `model_router` owns the meaning of the capacity fact, because it is a fact
  about a model resource. Cognition owns `CognitiveBudget` (ADR-0045) but not model capacity.
- **Delivery:** an already-resolved object handed to the runtime by the composition root carries a
  declared value. It is a delivery mechanism, not an authority. ADR-0029 already authorizes the
  composition root to receive resolved runtime configuration.

This ADR does not choose a concrete type, does not decide whether `ModelResourceCapabilities` gains
a field, and does not decide whether a new value object is introduced.

### Structural implications

```text
DOMAIN_STRUCTURE_CHANGE_REQUIRED_LATER = YES
CONFIG_STRUCTURE_CHANGE_REQUIRED_LATER = YES
NEW_PORT_REQUIRED_BY_SELECTED_POLICY = NO
```

A future implementation must support:

- a capacity fact owned by `model_router`;
- UNKNOWN capacity;
- an optional configured declaration;
- backward-compatible absence of that declaration, meaning UNKNOWN, so that existing configuration
  files remain valid.

`model_router` is not part of the frozen ADR-0005 component set. This ADR names no type, field,
configuration key, schema, port, or class.

### Current tests

```text
CURRENT_TESTS_REJECT_CONTEXT_WINDOW_FIELD = YES
TEST_ASSERTION_MEANING = CURRENT_STRUCTURE_GUARD
```

Existing unit tests assert that `ModelResource` and `ModelResourceCapabilities` expose no
`context_window` field. These tests describe current structure. They are not architectural
authority, and no ADR prohibits a capacity fact. This ADR does not change them; any revision
belongs to a later implementation gate.

### Implementation state

```text
IMPLEMENTATION_REQUIRED = NO
TEST_CHANGES_REQUIRED = NO
```

This ADR sets architectural direction only. No production code, test, configuration, or runtime
behavior changes. Implementation requires a later explicit gate.

### Milestone state

```text
NEXT_MILESTONE_IDENTIFIER = UNASSIGNED
M0_19_ASSIGNED = NO
```

## Rationale

- **It follows an existing pattern.** `ModelResourceCapabilities` already holds declared,
  operator-configured facts about a resource, delivered through the composition root. Capacity is
  another fact of the same kind.
- **It is provider-neutral.** The authority does not depend on any provider, SDK, or provider API,
  consistent with ADR-0002 and ADR-0003.
- **It is deterministic.** A declared value is fixed at configuration time and does not vary
  between runs or calls.
- **It requires no runtime I/O authority and no new port.** It does not place provider-specific
  policy in the composition root, consistent with ADR-0029.
- **It models absence truthfully.** UNKNOWN is a defined state, following the repository's
  existing precedent of representing an absent judgment explicitly (ADR-0030's
  `relevance = None`), rather than as a numeric sentinel.
- **It unblocks later work without deciding it.** A capacity fact can now exist, so the
  composition and capacity boundary (R3) and overflow policy (R7) become decidable. Neither is
  decided here.
- **It keeps later options open.** Provider discovery and declaration verification remain
  available as later, separate decisions.

### External-provider evidence boundary

```text
OLLAMA_EXTERNAL_FACTS_USED_AS_NORMATIVE_BASIS = NO
```

Some local providers are understood to let the usable context length be configured at runtime
independently of a model's trained maximum. That understanding is external to the repository and is
not verified by it. It motivates only the word "effective" in the governed fact. The decision above
rests on repository and canonical grounds alone.

## Alternatives Considered

### P1: No canonical capacity authority

```text
P1_NO_CANONICAL_CAPACITY_AUTHORITY = REJECTED
```

Noema would deliberately never know or represent capacity, and capacity would always be UNKNOWN.
Rejected because, while it formally resolves the authority question, it leaves all downstream
capacity work permanently blocked. It would also turn ADR-0032's deferral into a prohibition without
evidence for one.

### P3: Provider-discovered capacity

```text
P3_PROVIDER_DISCOVERED_CAPACITY = REJECTED_FOR_NOW
```

Capacity would be a fact reported by the provider side through a discovery boundary. Rejected for
now because it introduces dynamic provider I/O as an authority and requires a new port. It also
raises cache, refresh, and discovery-failure questions beyond the smallest decision, and its basis
would rest on provider behavior the repository does not verify. It is not prohibited. Provider
discovery, including as a way to verify declarations, remains a possible later decision.

### D2B: Optional operator narrow-only limit

```text
D2B_OPTIONAL_OPERATOR_NARROW_ONLY_LIMIT = DEFERRED
```

An optional operator limit could reduce allowed usable capacity without ever increasing or
replacing the capacity fact. Deferred because it is coherent but currently unnecessary: no consumer
exists. It would also introduce a third operator-facing token quantity alongside the capacity fact
and `CognitiveBudget.max_tokens`, which risks conflating them. The constraints any future limit must
satisfy are recorded above. A later decision may introduce one.

## Not Decided Here

```text
R3_COMPOSITION_CAPACITY_BOUNDARY = NOT_DECIDED_HERE
R4_TOKEN_BUDGET_ENFORCEMENT = NOT_DECIDED_HERE
R5_NON_CONTEXT_INPUT_RESERVATION = NOT_DECIDED_HERE
R6_OUTPUT_RESERVATION = NOT_DECIDED_HERE
R7_CAPACITY_OVERFLOW_POLICY = NOT_DECIDED_HERE
R8_TOKENIZER_ESTIMATION = NOT_DECIDED_HERE
TRAINED_MODEL_MAXIMUM = NOT_DECIDED_HERE
MAX_OUTPUT_GENERATION = NOT_DECIDED_HERE
PROVIDER_DISCOVERY_MECHANICS = NOT_DECIDED_HERE
CAPACITY_CACHE_POLICY = NOT_DECIDED_HERE
CAPACITY_REFRESH_POLICY = NOT_DECIDED_HERE
DECLARATION_VERIFICATION_OR_CONFLICT_RESOLUTION = NOT_DECIDED_HERE
PROVIDER_EXECUTION_OPTIONS = NOT_DECIDED_HERE
USAGE_TELEMETRY = REMAIN_PARKED
PRICING_COST = NOT_DECIDED_HERE
CROSS_RESOURCE_TOKEN_COMMENSURABILITY = NOT_DECIDED_HERE
```

### Context composition

```text
CONTEXT_COMPOSER = UNCHANGED
CONTEXT_COMPOSER_REQUIRES_PROVIDER_CAPACITY = NO
```

`ContextComposer` remains provider-independent, and `ContextRequest.max_total_content_size` remains
a raw Unicode code-point budget under ADR-0030. This ADR does not decide where, or whether, any
future capacity check takes place.

### CognitiveBudget max_tokens

```text
MAX_TOKENS_IS_CAPACITY = NO
MODEL_CAPACITY_IS_BUDGET = NO
ADR_0045_MAX_TOKENS_MEANING_CHANGED = NO
ADR_0045_MAX_TOKENS_SCOPE_CHANGED = NO
ADR_0045_TOKEN_UNIT_CHANGED = NO
ADR_0045_ENFORCEMENT_STATUS_CHANGED = NO
```

Model effective context capacity and `CognitiveBudget.max_tokens` remain independent concepts.
Neither is derived from the other.

### Documentation

```text
README_MAX_TOKENS_CLARIFICATION = FOLLOW_UP_DOCUMENTATION_ONLY
README_CHANGE_REQUIRED_BY_ADR_0046 = NO
```

## Consequences

**Positive:**

- A model resource's effective context capacity has a defined meaning and a defined authority.
- Absence of capacity knowledge is a defined, truthful state rather than an architectural gap.
- The composition and capacity boundary (R3) and overflow policy (R7) become decidable.
- Capacity, operator policy, and `CognitiveBudget.max_tokens` remain separate concepts.
- No production code, test, configuration, or runtime behavior changes.

**Tradeoffs:**

- A declared capacity may be wrong or stale. This ADR trusts the declaration and provides no
  verification.
- Until a declaration mechanism is implemented, every resource's capacity is UNKNOWN.
- A later implementation must change the `model_router` domain structure and the process
  configuration schema, and revise the current structure-guard tests.
- An operator wishing to restrict per-call usage has no policy mechanism for it yet.

## ADR Relationship

ADR-0046 supplements ADR-0032 (Cognitive budget runtime enforcement) by resolving its
`MODEL_CONTEXT_WINDOW_AUTHORITY = NONE` deferral. It supplements ADR-0045 (Cognitive budget
max_tokens semantic meaning) by resolving its R2 and R9 non-decisions, without changing any of its
semantics. It supersedes no ADR.

```text
ADR_0046_SUPPLEMENTS_ADR_0032 = YES
ADR_0046_SUPPLEMENTS_ADR_0045 = YES
SUPERSEDES = NONE
```

```text
ADR_0032_MODEL_CONTEXT_WINDOW_AUTHORITY_DEFERRAL = RESOLVED
```

The authority is now defined. Individual resources may still have UNKNOWN capacity; UNKNOWN is a
defined semantic state, not an architectural deferral.

```text
ADR-0005 = NOT_AFFECTED
ADR-0028 = NOT_AFFECTED
ADR-0029 = NOT_AFFECTED
ADR-0030 = NOT_AFFECTED
ADR-0032 = SUPPLEMENTED
ADR-0033 = NOT_AFFECTED
ADR-0045 = SUPPLEMENTED
```

ADR-0046 introduces no structural change to any frozen ADR-0005 component.
