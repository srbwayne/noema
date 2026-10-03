# ADR-0043: Deterministic Relevance Activation Semantics Clarification

- Status: Accepted
- Date: 2026-10-03

## Context

ADR-0040 fixed how Context relevance production is activated:

```text
RELEVANCE_PRODUCTION_ACTIVATION_POLICY = BOUND_AUTHORITY
SEPARATE_RELEVANCE_FEATURE_FLAG = NO
```

Relevance production activates purely by whether a concrete realization of the relevance authority
is bound into the runtime object graph. No separate relevance-specific configuration setting or
feature flag participates in that activation.

ADR-0041 selected the first deterministic realization, `NORMALIZED_EXACT_TASK_CONTENT_MATCH`. At
that point no production binding existed, so ADR-0041 deferred both production bootstrap binding
and runtime activation:

```text
PRODUCTION_BOOTSTRAP_BINDING_AUTHORIZED = NO
RUNTIME_ACTIVATION_AUTHORIZATION = DEFERRED
```

ADR-0042 decided the production binding shape:

```text
PRODUCTION_RELEVANCE_BINDING_CONDITIONALITY = PRIOR_TASK_CONTEXT_ENABLED_ONLY
EXISTING_PRIOR_TASK_CONTEXT_ACTIVATION_REUSED = YES
```

It reused ADR-0031's `prior_task_context_enabled` switch rather than introducing a relevance switch,
and listed runtime activation under "Not Decided Here".

The binding ADR-0042 describes is now canonical on `main` (PR #82):
`noema.bootstrap.open_direct_runtime` constructs exactly one
`NormalizedExactTaskContentRelevanceAuthority` when `prior_task_context_enabled` is `True`, using
the runtime's single `RuntimeContentReferenceAuthority`, and passes it to `ContextPackagePreparer`
as `context_relevance_authority`; when `prior_task_context_enabled` is `False`, no relevance
authority is constructed.

A post-merge lifecycle discovery pass found that the phrase "runtime activation" had continued to be
carried in lifecycle gate state (`RUNTIME_ACTIVATION_AUTHORIZED`, `RUNTIME_ACTIVATION_STARTED`)
after the technical activation mechanism itself had become canonical. No source code and no ADR
defines a second activation mechanism beyond binding. The earlier ADRs were correct for their time:
before binding existed, deferring "runtime activation" was equivalent to deferring binding. The
ambiguity arose only because that lifecycle terminology survived after its pre-binding purpose
ended. This ADR clarifies the terminology; it changes no behavior.

## Decision

### Technical activation

```text
RELEVANCE_PRODUCTION_ACTIVATION_POLICY = BOUND_AUTHORITY
TECHNICAL_RELEVANCE_ACTIVATION_MECHANISM = BOUND_AUTHORITY
TECHNICAL_RELEVANCE_ACTIVATION_CANONICAL = YES
SEPARATE_TECHNICAL_RUNTIME_ACTIVATION_STATE_EXISTS = NO
TECHNICAL_ACTIVATION_REQUIRES_SECOND_POST_BINDING_STEP = NO
```

A deterministic relevance realization is technically active exactly when it is bound into a runtime
whose surrounding prior-`TASK` subsystem is enabled.

There is no distinct post-binding technical activation state.

### Conditional runtime behavior

```text
PRODUCTION_RELEVANCE_BINDING_CONDITIONALITY = PRIOR_TASK_CONTEXT_ENABLED_ONLY
EXISTING_PRIOR_TASK_CONTEXT_ACTIVATION_REUSED = YES
```

- `prior_task_context_enabled = false` requires `context_relevance_authority = None`.
- `prior_task_context_enabled = true` requires the canonical deterministic relevance authority to be
  bound exactly as ADR-0042 specifies.

ADR-0040's zero-candidate semantics are preserved: when projection returns zero candidates, the
relevance authority is not invoked.

### Operational use

```text
SEPARATE_RELEVANCE_OPERATIONAL_ENABLEMENT_CONCEPT = NO
RELEVANCE_OPERATIONAL_USE_GOVERNANCE = ADR_0031_OPERATOR_CONFIGURATION
SEPARATE_RELEVANCE_FEATURE_FLAG = NO
NEW_RELEVANCE_TOML_KEY = NO
NEW_RELEVANCE_ENVIRONMENT_KEY = NO
NEW_RELEVANCE_CLI_FLAG = NO
ADDITIONAL_RUNTIME_KILL_SWITCH_REQUIRED = NO
```

The operator's existing ADR-0031 choice to enable or disable the prior-`TASK` context subsystem is
sufficient. The relevance feature receives no second operational permission layer. ADR-0040 and
ADR-0042 already reject a separate relevance-specific feature flag or configuration switch; this
ADR likewise introduces no parallel relevance-specific governance permission.

If future governance is introduced for continuously-running, service, deployment, or
production-like use, it is a frontier for the broader prior-`TASK` subsystem or deployment model
rather than a relevance-specific activation switch.

### Default posture

ADR-0031 is preserved unchanged:

- absence of `[direct.context]` disables prior-`TASK` context;
- explicit `prior_task_context_enabled = false` disables prior-`TASK` context.

ADR-0043 introduces no new default.

### Failure semantics

```text
RELEVANCE_PRODUCTION_FAILURE_POLICY = FAIL_CLOSED_PROPAGATE
OPERATIONAL_USE_CHANGES_FAILURE_POLICY = NO
```

There is no fail-open behavior and no fallback to all-`None` relevance after a relevance or
content-resolution failure.

### Evidence semantics

```text
ADDITIONAL_RELEVANCE_ACTIVATION_EVIDENCE_REQUIRED = NO
CANONICAL_TEST_EVIDENCE_SUFFICIENT_FOR_BINDING_LIFECYCLE = YES
REAL_RUNTIME_SMOKE_TEST_REQUIRED_FOR_ACTIVATION = NO
REAL_RUNTIME_SMOKE_TEST_ALLOWED_AS_OPTIONAL_CONFIRMATION = YES
```

The canonical automated tests for the deterministic realization and its production binding are the
evidence for the binding lifecycle. A real-runtime smoke test may be performed as optional
confirmation; this ADR neither requires nor authorizes one, and records no such test as performed.

### Lifecycle vocabulary

```text
LEGACY_RUNTIME_ACTIVATION_FIELDS_STATUS = RETIRED_FOR_RELEVANCE_LIFECYCLE
LEGACY_RUNTIME_ACTIVATION_FIELD_MEANING = PRE_BINDING_GOVERNANCE_STATUS_NOT_SEPARATE_RUNTIME_MECHANISM
```

`RUNTIME_ACTIVATION_AUTHORIZED` and `RUNTIME_ACTIVATION_STARTED` are retired for future relevance
lifecycle reporting. Future relevance lifecycle state uses:

```text
TECHNICAL_RELEVANCE_ACTIVATION_CANONICAL = YES | NO
OPERATIONAL_USE_GOVERNANCE = ADR_0031_OPERATOR_CONFIGURATION
```

No separate operational-enablement authorization field is introduced.

### Architectural invariants

```text
SAME_RUNTIME_CONTENT_AUTHORITY_IDENTITY_REQUIRED = YES
SECOND_RUNTIME_CONTENT_AUTHORITY_ALLOWED = NO
SECOND_RELEVANCE_AUTHORITY_ALLOWED = NO
SEPARATE_RELEVANCE_FEATURE_FLAG = NO
CONTEXT_RELEVANCE_PRODUCTION_AUTHORITY = COGNITION_CONTEXT_RELEVANCE_AUTHORITY
FIRST_DETERMINISTIC_RELEVANCE_ALGORITHM = NORMALIZED_EXACT_TASK_CONTENT_MATCH
```

The semantics of `NORMALIZED_EXACT_TASK_CONTENT_MATCH` remain exactly as ADR-0041 defines them.

### Milestone state

```text
NEXT_MILESTONE_IDENTIFIER = UNASSIGNED
M0_19_ASSIGNED = NO
```

### Documentation follow-up

```text
README_CONFIGURATION_DRIFT_DISCOVERED = YES
README_UPDATE_REQUIRED = YES
README_UPDATE_AUTHORIZED_BY_THIS_ADR = NO
```

The README does not describe the optional ADR-0031 `[direct.context]` table, and its description of
multi-problem invocations does not account for prior-`TASK` context when enabled. Correcting it is a
separate documentation action.

## Not Decided Here

- Broader deployment or operations governance for the prior-`TASK` subsystem.
- Service, daemon, or continuously-running deployment policy.
- Environment or deployment-profile policy.
- Lexical or graded relevance.
- Model-backed relevance.
- Relevance for additional `ContextCandidate` families.
- Future prior-`TASK` context retrieval or storage expansion.
- M0-19 scope.
- Implementation of the README correction.

## Consequences

**Benefits:**

- Removes the lifecycle ambiguity between binding and "runtime activation".
- Aligns lifecycle terminology with ADR-0040's `BOUND_AUTHORITY` semantics.
- Keeps exactly one operator switch for the prior-`TASK` subsystem and its relevance production.
- Prevents lifecycle governance from accidentally becoming a second relevance feature flag.
- Leaves ADR-0031, ADR-0040, ADR-0041, and ADR-0042 implementation behavior unchanged.

**Tradeoffs:**

- Broader operational or deployment governance remains undefined if it is ever needed; it belongs
  to a larger prior-`TASK` subsystem or deployment frontier rather than to relevance.

## ADR Relationship

ADR-0043 supplements ADR-0040 (Context relevance producer integration semantics), ADR-0041 (First
deterministic context relevance realization), and ADR-0042 (Production relevance authority binding
conditionality). It clarifies their activation terminology after the production binding became
canonical and supersedes none of them.

```text
ADR_0043_SUPERSEDES_ADR_0040 = NO
ADR_0043_SUPERSEDES_ADR_0041 = NO
ADR_0043_SUPERSEDES_ADR_0042 = NO
ADR_0043_SUPPLEMENTS_ADR_0040 = YES
ADR_0043_SUPPLEMENTS_ADR_0041 = YES
ADR_0043_SUPPLEMENTS_ADR_0042 = YES
```

ADR-0031's configuration semantics remain unchanged. ADR-0043 introduces no new top-level Cognition
subsystem and changes no frozen ADR-0005 component's structure.
