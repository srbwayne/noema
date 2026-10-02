# ADR-0042: Production Relevance Authority Binding Conditionality

- Status: Accepted
- Date: 2026-09-30

## Context

ADR-0037 through ADR-0040 defined the semantics, ownership, producer contract, and integration of
Context relevance. ADR-0040 fixed activation as:

```text
RELEVANCE_PRODUCTION_ACTIVATION_POLICY = BOUND_AUTHORITY
SEPARATE_RELEVANCE_FEATURE_FLAG = NO
```

Relevance production activates purely by whether a concrete realization of the relevance authority
is bound into the runtime object graph, "mirroring the existing
`context_composer: ContextComposer | None` bound-or-absent pattern the preparer already uses".
ADR-0041 selected the first deterministic realization, `NORMALIZED_EXACT_TASK_CONTENT_MATCH`, and
explicitly withheld production bootstrap binding:

```text
PRODUCTION_BOOTSTRAP_BINDING_AUTHORIZED = NO
RUNTIME_ACTIVATION_AUTHORIZATION = DEFERRED
```

The generic integration foundation (`ContextRelevanceAuthority`, delegation and result validation in
`ContextPackagePreparer`) and the concrete realization
(`NormalizedExactTaskContentRelevanceAuthority`) are now canonical on `main`. The production
composition root, `noema.bootstrap.open_direct_runtime`, binds no relevance authority:
`ContextPackagePreparer` is constructed without `context_relevance_authority`, which therefore
defaults to `None`.

A read-only discovery pass (POST-M0-18FS) established that:

- `open_direct_runtime` is the single concrete production construction root;
  `open_strategy_aware_direct_runtime` delegates to it and constructs no second runtime graph;
- each runtime constructs exactly one `RuntimeContentReferenceAuthority`, shared by identity with
  `PriorTaskContextProjector`, `PriorTaskContextMaterializer`, and `DirectReasoningOperation`;
- `ContextPackagePreparer` has exactly one production construction site, and the composition root
  already constructs `ContextComposer` only when `prior_task_context_enabled` is `True`, passing
  `None` otherwise;
- `DirectReasoningOperation.execute` registers the current task payload through the runtime-scoped
  `RuntimeContentReferenceAuthority` before `ContextPackagePreparer.prepare` runs, and every prior
  `TASK` candidate refers to an earlier `TASK` reference registered through that same authority
  instance during the same runtime lifetime;
- binding requires no new port, no domain, infrastructure, process-source, or process-schema
  change, and no change to the `DirectReasoningOperation` or `ContextPackagePreparer` APIs.

The same discovery found one question the existing ADRs do not answer. ADR-0040's invocation rules
and backward-compatibility table hold whether the authority is bound in every runtime or only in
runtimes with prior-`TASK` context enabled, because a disabled runtime never reaches projection or
relevance judgment. ADR-0040 constrains invocation, not collaborator presence in the disabled object
graph. This ADR decides that conditionality only.

## Decision

### Binding conditionality

```text
PRODUCTION_RELEVANCE_BINDING_CONDITIONALITY = PRIOR_TASK_CONTEXT_ENABLED_ONLY
DISABLED_RUNTIME_RELEVANCE_AUTHORITY = NONE
ENABLED_RUNTIME_RELEVANCE_AUTHORITY = NORMALIZED_EXACT_TASK_CONTENT_RELEVANCE_AUTHORITY
SEPARATE_RELEVANCE_FEATURE_FLAG = NO
EXISTING_PRIOR_TASK_CONTEXT_ACTIVATION_REUSED = YES
```

The production relevance authority is bound exactly when, and only when, the existing prior-`TASK`
context activation is enabled. No other condition governs its presence.

### Disabled-runtime semantics

When `prior_task_context_enabled = false`, the production composition root constructs
`context_composer = None` and binds `context_relevance_authority = None`.

```text
DISABLED_RUNTIME_OBJECT_GRAPH_PRESERVED = YES
RELEVANCE_AUTHORITY_CONSTRUCTED_WHEN_CONTEXT_DISABLED = NO
RELEVANCE_PRODUCTION_INVOCATIONS_WHEN_CONTEXT_DISABLED = 0
```

No relevance configuration is consulted or introduced. The disabled runtime object graph is exactly
the current one.

### Enabled-runtime semantics

When `prior_task_context_enabled = true`, a future production-binding implementation, if
separately authorized, must construct exactly one `NormalizedExactTaskContentRelevanceAuthority`
using the exact same runtime-scoped `RuntimeContentReferenceAuthority` instance already shared by
`PriorTaskContextProjector`, `PriorTaskContextMaterializer`, and `DirectReasoningOperation`, and
must pass that realization to `ContextPackagePreparer` as `context_relevance_authority`. This ADR
decides only that required composition shape; production binding remains unauthorized.

```text
ENABLED_RUNTIME_RELEVANCE_AUTHORITY_INSTANCE_COUNT = 1
SAME_RUNTIME_CONTENT_AUTHORITY_IDENTITY_REQUIRED = YES
SECOND_RUNTIME_CONTENT_AUTHORITY_ALLOWED = NO
SECOND_RELEVANCE_AUTHORITY_ALLOWED = NO
```

### Runtime-resolution basis

`DirectReasoningOperation` registers the current task payload through the runtime-scoped
`RuntimeContentReferenceAuthority` before `ContextPackagePreparer` runs. Prior `TASK` candidates
refer to earlier `TASK` references registered in that same runtime authority. The enabled
production relevance authority must therefore receive that same authority instance; a separate
instance would hold no registrations and could resolve neither the current task nor any candidate.

This is binding evidence recorded from the existing production flow, not a new content-resolution
semantic. ADR-0041's `CONTENT_RESOLUTION_STRATEGY = EXISTING_RUNTIME_CONTENT_REFERENCE_AUTHORITY`
and its fail-closed resolution policy are unchanged.

### Activation semantics preserved

```text
RELEVANCE_PRODUCTION_ACTIVATION_POLICY = BOUND_AUTHORITY
SEPARATE_RELEVANCE_FEATURE_FLAG = NO
NEW_PROCESS_CONFIGURATION_KEY = NO
NEW_TOML_RELEVANCE_KEY = NO
NEW_ENVIRONMENT_RELEVANCE_KEY = NO
NEW_CLI_RELEVANCE_FLAG = NO
```

ADR-0040's `BOUND_AUTHORITY` policy is unchanged. `prior_task_context_enabled` remains the existing
activation switch for the whole prior-`TASK` context subsystem, exactly as ADR-0031 established it.
Inside that enabled subsystem, dependency presence remains the relevance activation signal. The
conditional binding selected here reuses the existing subsystem switch; it does not add a relevance
switch.

### Invocation semantics preserved

```text
prior-TASK context disabled                  -> relevance authority absent
                                                judge invocations = 0
prior-TASK context enabled, zero candidates  -> relevance authority bound
                                                judge invocations = 0
prior-TASK context enabled, candidates exist -> relevance authority bound
                                                judge invocations = exactly 1 per preparation
```

These are ADR-0040's invocation rules applied to the selected binding. No other invocation rule
changes.

### Composition-root ownership

```text
PRODUCTION_BINDING_LOCATION = noema.bootstrap.open_direct_runtime
STRATEGY_AWARE_RUNTIME_BINDING = INHERITED_THROUGH_OPEN_DIRECT_RUNTIME
BOOTSTRAP_PUBLIC_SIGNATURE_CHANGE_REQUIRED = NO
PROCESS_SOURCE_CHANGE_REQUIRED = NO
PROCESS_SCHEMA_CHANGE_REQUIRED = NO
EXTERNAL_CONTEXT_RELEVANCE_AUTHORITY_INJECTION_AUTHORIZED = NO
```

Binding belongs to the ADR-0029 composition root. `open_strategy_aware_direct_runtime` receives the
binding only through its delegation to `open_direct_runtime` and must not construct another
relevance authority. No external injection parameter is introduced.

### Semantic ownership and boundaries preserved

```text
CONTEXT_RELEVANCE_PRODUCTION_AUTHORITY = COGNITION_CONTEXT_RELEVANCE_AUTHORITY
RUNTIME_RELEVANCE_PRODUCER_OWNER = COGNITION_CONTEXT_RELEVANCE_AUTHORITY
RELEVANCE_AUTHORITY_INTEGRATION_LAYER = COGNITION_APPLICATION
CONTEXT_PACKAGE_PREPARER_OWNS_RELEVANCE_SEMANTICS = NO
CONTEXT_PACKAGE_PREPARER_ORCHESTRATES_RELEVANCE_PRODUCTION = YES
RESULT_VALIDATION_OWNER = ContextPackagePreparer
NEW_PORT_REQUIRED = NO
DOMAIN_CHANGE_REQUIRED = NO
INFRASTRUCTURE_CHANGE_REQUIRED = NO
MODEL_ROUTER_CHANGE_REQUIRED = NO
COGNITIVE_BUDGET_CHANGE_REQUIRED = NO
```

All inherited unchanged from ADR-0038, ADR-0040, and ADR-0041.

### Deterministic realization unchanged

```text
FIRST_DETERMINISTIC_RELEVANCE_ALGORITHM = NORMALIZED_EXACT_TASK_CONTENT_MATCH
```

This ADR references ADR-0041's realization and does not redefine it. It introduces no new
normalization, no new score values, no known-low scores, no fallback scoring, no clamping, no
partial-result semantics, no model-based relevance, and no provider calls. Those remain governed by
ADR-0037 through ADR-0041.

### Lifecycle state

```text
PRODUCTION_BOOTSTRAP_BINDING_AUTHORIZED = NO
PRODUCTION_BOOTSTRAP_BINDING_IMPLEMENTED = NO
PRODUCTION_RELEVANCE_AUTHORITY_BOUND = NO
RUNTIME_ACTIVATION_AUTHORIZED = NO
RUNTIME_ACTIVATION_STARTED = NO
NEXT_MILESTONE_IDENTIFIER = UNASSIGNED
M0_19_ASSIGNED = NO
```

This ADR decides binding conditionality only. Authorizing and implementing the production binding
remain later lifecycle actions.

## Alternatives Considered

### Always-bound relevance authority

```text
ALWAYS_BOUND_RELEVANCE_AUTHORITY = REJECTED
```

`open_direct_runtime` would always construct the realization and pass it to
`ContextPackagePreparer`, including when `prior_task_context_enabled = false`. This option is
compatible with ADR-0040's generic invocation rules -- a disabled runtime returns before projection,
so the authority would never be invoked -- but it is not the selected production composition:

- it would place a bound relevance authority in the disabled prior-`TASK` object graph, where no
  relevance work could ever occur;
- dependency presence would therefore become a weaker indication of an active, relevance-capable
  context path;
- it would unnecessarily alter the currently preserved disabled object graph;
- it is less aligned with the bound-or-absent `ContextComposer` pattern ADR-0040 cites, under which
  the composer is already absent whenever prior-`TASK` context is disabled.

### External injection

```text
EXTERNAL_INJECTION = REJECTED
```

`open_direct_runtime` would receive a `context_relevance_authority` parameter from `_process.py` or
another outer caller. The composition root already owns every concrete collaborator the canonical
first deterministic realization needs. Passing a `ContextRelevanceAuthority` through `_process.py`,
or adding a new public `open_direct_runtime` parameter, would introduce an unnecessary
dependency-injection and API surface across the process boundary, which today supplies
already-resolved configuration only, and is not required by the canonical realization.

## Not Decided Here

- Authorization or implementation of the production bootstrap binding.
- Runtime activation.
- Any change to ADR-0041's algorithm, or any lexical, graded, or model-backed realization.
- Any change to `ContextComposer` eligibility or ordering, or deduplication of repeated identical
  prior tasks.
- Relevance for any `ContextCandidate` family beyond the current prior-`TASK` scope.
- A milestone identifier.

## Consequences

**Compatibility:**

- The disabled runtime object graph remains unchanged.
- An enabled runtime with zero projected candidates performs no relevance production.
- Once production binding is separately authorized and implemented, an enabled runtime with
  projected candidates will execute ADR-0041 deterministic relevance exactly once per preparation.
- Required `TASK` activation remains based on candidate existence (`REQUIRED_WHEN_PRIOR_EXISTS`),
  not on relevance.
- `ContextComposer` semantics remain unchanged.
- Result validation remains with `ContextPackagePreparer`.
- Fail-closed propagation of relevance and content-resolution failures remains unchanged.

**Benefits:**

- The binding question is closed without a new flag, port, configuration key, or public API.
- Relevance-authority presence in the production graph coincides exactly with the subsystem in
  which relevance can be produced.
- The future implementation is confined to the composition root and its tests.

**Tradeoffs:**

- The relevance authority's presence is coupled to the prior-`TASK` context switch. A future
  relevance consumer outside the prior-`TASK` subsystem would require its own binding decision.
- Production binding still does not exist; no runtime capability changes until a separate
  authorization and implementation gate passes.

## ADR Relationship

ADR-0042 supplements ADR-0040 (Context relevance producer integration semantics) and ADR-0041
(First deterministic context relevance realization). It decides production binding conditionality
under the activation policy already canonical in ADR-0040 and for the realization selected in
ADR-0041.

```text
ADR_0042_SUPERSEDES_ADR_0040 = NO
ADR_0042_SUPERSEDES_ADR_0041 = NO
```

It relies on ADR-0029's composition-root placement and ADR-0031's prior-`TASK` context activation
without changing either. It introduces no new top-level Cognition subsystem and changes no frozen
ADR-0005 component's structure.
