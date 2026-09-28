# ADR-0040: Context Relevance Producer Integration Semantics

- Status: Accepted
- Date: 2026-09-26

## Context

ADR-0037 defined what a known `ContextCandidate.relevance` value means. ADR-0038 decided who
may produce one: a generic, Cognition-owned authority (`COGNITION_CONTEXT_RELEVANCE_AUTHORITY`),
applying to any `ContextCandidate`. ADR-0039 defined the shape of one production operation --
composition-batch granularity, positional correlation, a minimal `float | None` result, and a
production operational failure kept distinct from a legitimate absence of judgment. None of
those three ADRs decided *how* such a producer participates in the existing first-DIRECT
runtime: where it is invoked, who invokes it, how its output is folded back into the immutable
candidates `ContextComposer` consumes, what happens when it is absent or fails, and what
happens to every configuration that exists today, before any producer exists.

A read-only discovery pass (POST-M0-18DN), corrected once (POST-M0-18DNR) after it conflated
ADR-0005's structural freeze with an implementation prohibition and overlapped two of its three
candidate timing windows, traced the exact current sequence inside
`ContextPackagePreparer.prepare`:

```text
canonical snapshot observation (exactly once, ADR-0031/ADR-0028)
→ PriorTaskContextProjector.project(situation)
→ effective required-slice-type activation (today: gated by projected candidate existence, independent of relevance)
→ ContextRequestAssembler.assemble(...)
→ ContextComposer.compose(request, candidates)
```

and established, among other things, that a known relevance value can already turn a
currently-succeeding required-slot composition into a failure (`ContextCompositionUnsatisfiedError`),
confirmed by an existing, already-passing test using `relevance=0.49` against the default
`minimum_relevance=0.5`; that every step in this sequence is synchronous except the outer
`DirectReasoningOperation.execute`; and that `cognition.application` may already reference both
`context_composition` and `cognition.ports`, while `cognition.ports` and `cognition.infrastructure`
may not reference `context_composition` today.

A decision pass (POST-M0-18DO) closed every remaining integration question this ADR now
records. This ADR authorizes no implementation; it fixes the architecture that a future concrete
producer must be integrated against.

## Decision

### Inherited authority, not redefined

```text
CONTEXT_RELEVANCE_SEMANTIC = CURRENT_TASK_PERTINENCE
CONTEXT_RELEVANCE_SEMANTIC_SCOPE = PER_CONTEXT_COMPOSITION
CONTEXT_RELEVANCE_PRODUCTION_AUTHORITY = COGNITION_CONTEXT_RELEVANCE_AUTHORITY
RUNTIME_RELEVANCE_PRODUCER_OWNER = COGNITION_CONTEXT_RELEVANCE_AUTHORITY
RELEVANCE_PRODUCER_GRANULARITY = COMPOSITION_BATCH
RELEVANCE_CORRELATION_AUTHORITY = POSITIONAL
ONE_AUTHORITY_PER_COMPOSITION_SCORE_SET = YES
CURRENT_TASK_REFERENCE_REQUIRED = YES
NONE_RELEVANCE_SEMANTIC = NO_RELEVANCE_JUDGMENT_EXISTS
RELEVANCE_PRODUCTION_FAILURE_SEMANTICS = OPERATION_LEVEL_FAILURE_DISTINCT_FROM_RESULT
PARTIAL_OPERATIONAL_FAILURE_RESULT_AUTHORIZED = NO
```

All inherited unchanged from ADR-0037/0038/0039; none reinterpreted here.

### ADR-0005 does not decide this

```text
ADR_0005_FREEZES = COGNITION_V1_COMPONENT_STRUCTURE
ADR_0005_DECIDES_CONTEXT_COMPOSER_IMPLEMENTATION_DETAILS = NO
CONTEXT_COMPOSER_ROLE = RELEVANCE_CONSUMER
CONTEXT_COMPOSER_OWNS_RELEVANCE_PRODUCTION = NO
CONTEXT_COMPOSER_PRODUCTION_SEAM_ALLOWED = NO
```

ADR-0005 freezes the named COGNITION V1 component set -- that "Context Composer" exists as one
of the listed structural components, and that restructuring that set requires an ADR. It says
nothing about what `ContextComposer`'s internals may do. The actual authority excluding it from
relevance production is ADR-0038's and ADR-0039's own explicit consumer/producer role boundary,
and this ADR attributes the exclusion to that boundary only.

### Known-low required-TASK policy

```text
KNOWN_LOW_REQUIRED_TASK_POLICY = REQUIRED_WHEN_PRIOR_EXISTS
```

ADR-0031's activation rule is preserved exactly: whenever prior-task context is enabled and at
least one prior `TASK` candidate is projected, `TASK` becomes a required slice type --
regardless of whether that candidate's relevance is unknown, known and above
`ContextCompositionPolicy.minimum_relevance`, or known and below it. A known relevance value
below the threshold may therefore cause `ContextCompositionUnsatisfiedError` for required `TASK`
coverage, exactly as the existing test suite already exercises today with no producer at all.

```text
KNOWN_RELEVANCE_CAN_REDUCE_REQUIRED_COVERAGE_ELIGIBILITY = YES
KNOWN_LOW_REQUIRED_TASK_FAILURE_ACCEPTED = YES
LOW_SCORE_CLAMP_TO_MINIMUM_RELEVANCE_AUTHORIZED = NO
LEGITIMATE_LOW_SCORE_TO_NONE_SUBSTITUTION_AUTHORIZED = NO
PRODUCER_MAY_CHANGE_SCORE_TO_PRESERVE_REQUIRED_COVERAGE = NO
```

`REQUIRED_WHEN_PRIOR_EXISTS` was selected because it preserves ADR-0031's existing activation rule
unchanged, preserves all-`None` compatibility, imposes no relevance-dependent activation or timing
constraint, and introduces no new consumer-side failure-recovery behavior before evidence requires
one. Other families considered also preserve all-`None` compatibility on their own, but none
combines that with leaving both activation and producer timing unconstrained by relevance without
also requiring new consumer-side failure-recovery design work invented ahead of any concrete
producer. Required coverage remains entirely a `ContextComposer`
concern; the producer must never clamp a legitimate low score upward, substitute `None` for it,
or otherwise adjust its own judgment to avoid this outcome. If the resulting failure mode ever
proves operationally unacceptable, the fix belongs in a future, evidence-driven consumer-side
decision -- not in this ADR, and not in the producer.

### Timing

```text
RELEVANCE_PRODUCER_TIMING = AFTER_PROJECTION_BEFORE_REQUIRED_SLICE_ACTIVATION
```

This is the interval immediately after `PriorTaskContextProjector.project` returns and before
`ContextPackagePreparer` computes its effective required-slice types. At this point the current
task's reference and the ordered candidate batch both already exist, and the single canonical
snapshot observation that produced them is already established -- nothing additional needs to be
observed. The producer receives neither the eventual `ContextRequest`, nor
`ContextCompositionPolicy`, nor `minimum_relevance` (per ADR-0039, these are composition
guardrails, not part of the relevance judgment), so production has no dependency on anything
computed after this point. Because `KNOWN_LOW_REQUIRED_TASK_POLICY` above never consults
relevance during activation, this timing is not technically *required* by that policy -- required-
slice activation would behave identically if production happened later. This timing is chosen
because it is the least-coupled point available: it inserts one new step immediately after the
step whose output it needs, without incidentally depending on, or being depended on by, the
required-slice-activation or `ContextRequest`-assembly computations that follow it.

### Integration shape

```text
RELEVANCE_INTEGRATION_SHAPE = PREPARER_DELEGATES_TO_DISTINCT_RELEVANCE_AUTHORITY
CONTEXT_PACKAGE_PREPARER_OWNS_RELEVANCE_SEMANTICS = NO
CONTEXT_PACKAGE_PREPARER_ORCHESTRATES_RELEVANCE_PRODUCTION = YES
SEMANTIC_AUTHORITY_PRESERVED = YES
SINGLE_SNAPSHOT_OWNERSHIP_PRESERVED = YES
GENERIC_CONTEXT_CANDIDATE_SCOPE_PRESERVED = YES
CURRENT_DEPENDENCY_BOUNDARIES_PRESERVED = YES
```

`ContextPackagePreparer` remains exactly what ADR-0031 already made it: the single owner of
per-operation canonical-state observation and orchestration. It gains one new, narrowly-bounded
responsibility -- delegating one composition-batch relevance judgment to a distinct, bound
realization of `COGNITION_CONTEXT_RELEVANCE_AUTHORITY`, and applying the returned positional
results -- without becoming that authority itself. The same distinction the preparer already
relies on for `ContextComposer` applies here unchanged: invoking `compose()` does not make the
preparer "own composition"; invoking the relevance authority and applying its output does not
make it "own relevance semantics" either. Ownership (ADR-0038) stays with the conceptual
authority; orchestration (ADR-0031, now supplemented) stays with the preparer.

Three other shapes were considered and not selected. A shape in which the preparer's own method
body directly contains the concrete judgment logic was excluded because that distinction cannot
be honestly drawn -- if the judgment is computed inline, the preparer *is* the producer, not
merely its orchestrator. A shape in which `DirectReasoningOperation` orchestrates production
outside the preparer was excluded because that component's own contract explicitly disclaims
observing canonical state or constructing a `ContextPackage` at all, and giving it that role
would risk a second, independent snapshot observation. A shape in which an outer coordinator
wraps or replaces the preparer was excluded because it would relocate ADR-0031's core
single-observation-ownership assignment, a larger structural move than adding one delegated step
to the orchestrator that already exists.

### Exact invocation semantics

```text
RELEVANCE_AUTHORITY_INVOCATIONS_PER_PREPARATION = AT_MOST_ONE
ACTIVE_RELEVANCE_PRODUCTION_INVOCATIONS_PER_PREPARATION = EXACTLY_ONE
```

The relevance authority is invoked under exactly one condition, and not invoked under three
others:

```text
prior-task context disabled                                    -> not invoked
prior-task context enabled, projected candidate batch empty     -> not invoked
candidates exist, no concrete relevance authority realization bound -> not invoked
candidates exist AND a concrete authority realization is bound  -> exactly one
                                                                    composition-batch
                                                                    relevance operation
```

"Exactly once per preparation" is true only of this last, active-production case; the other three
states are all forms of the authority simply not being called, not an authority call that
happens to return early.

### Semantic home versus integration layer

```text
CONTEXT_COMPOSITION_IS_SEMANTIC_HOME = YES
RELEVANCE_AUTHORITY_INTEGRATION_LAYER = COGNITION_APPLICATION
```

ADR-0038's finding that the relevance concern belongs conceptually to Context Composition is
preserved unchanged. `cognition.application` is where this integration is *placed* at runtime --
it is not thereby made the semantic owner. Semantic ownership remains
`COGNITION_CONTEXT_RELEVANCE_AUTHORITY`, a conceptual authority inside the existing Context
Composition concern; `cognition.application` is simply the layer that already legally
orchestrates `ContextPackagePreparer` and every collaborator it depends on. No new top-level
Cognition subsystem is introduced.

### Dependency boundaries

```text
APPLICATION_LAYER_ORCHESTRATION_FIT = HIGH
PORT_BOUNDARY_CHANGE_AUTHORIZED = NO
CURRENT_PORT_LAYER_CAN_REFERENCE_CONTEXT_COMPOSITION = NO
COGNITION_INFRASTRUCTURE_CAN_OWN_RELEVANCE_SEMANTICS = NO
MODEL_ROUTER_CAN_OWN_RELEVANCE_SEMANTICS = NO
```

`cognition.application` already legally imports both `context_composition` and `cognition.ports`,
and already hosts every collaborator a first, generic realization would need. No architecture
dependency allow-list changes as a result of this ADR. A future model-backed realization, should
one ever be pursued, remains a separate frontier and may require its own port-boundary decision
at that time -- this ADR neither authorizes nor forecloses that.

### Applying positional results

```text
SCORED_CANDIDATE_BATCH_RECONSTRUCTION_REQUIRED = YES
SCORED_CANDIDATE_RECONSTRUCTION_OWNER = ContextPackagePreparer
CONTEXT_SLICE_PRESERVED = YES
AGE_PRESERVED = YES
INPUT_ORDER_PRESERVED = YES
ORIGINAL_CANDIDATE_MUTATION_ALLOWED = NO
CANDIDATE_OBJECT_IDENTITY_REQUIRED = NO
```

`ContextCandidate` is frozen; there is no in-place update. `ContextPackagePreparer`, already
holding the projector's ordered candidate tuple, is the one place that applies the authority's
returned ordered judgment tuple back to it: for every input candidate at position *i*, only
output judgment *i* applies to it, and a resulting scored candidate must preserve its
`context_slice` and `age` exactly, differing only in `relevance`. Object identity is not
required -- nothing downstream (`ContextComposer` included) inspects it, only structural value
and position. Reconstruction is application of a judgment, never the judgment itself: the
authority judges; the preparer applies.

### Result validation

```text
RELEVANCE_RESULT_VALIDATION_OWNER = ContextPackagePreparer
```

Before reconstruction, the preparer must confirm the returned result's cardinality equals the
input candidate batch's cardinality, and that every element is either `None` or a finite float in
`[0.0, 1.0]`. A contract-invalid result must not be truncated, padded, reordered, clamped,
coerced, or silently replaced with `None` -- it is a producer-contract violation, not a
recoverable condition. This ADR does not name a concrete exception type for that violation; doing
so is left to implementation.

### Operational failure

```text
RELEVANCE_PRODUCTION_FAILURE_POLICY = FAIL_CLOSED_PROPAGATE
NONE_USED_AS_FAILURE_SIGNAL = NO
PARTIAL_OPERATIONAL_FAILURE_RESULT = NO
FAILED_PRODUCTION_REPLACED_BY_ALL_NONE = NO
```

A distinct operational failure raised by the bound relevance authority propagates through
`ContextPackagePreparer` exactly like every other collaborator failure in this pipeline already
does today -- both `ContextPackagePreparer.prepare` and `DirectReasoningOperation.execute`
already propagate projector, assembler, and composer errors unchanged, with no compensating
rollback of prior work. A relevance-production failure aborts the current DIRECT operation the
same way. No fail-open fallback -- silently continuing with an unscored batch as if production had
returned all `None` -- is authorized: doing so would misrepresent a failed attempt as a
successful result in which `NO_RELEVANCE_JUDGMENT_EXISTS` for those candidates, which is not
what happened.

### Empty candidate batch

```text
ZERO_CANDIDATE_RELEVANCE_POLICY = SKIP_PRODUCER
```

When projection returns zero candidates, the relevance authority is not invoked, exactly as
`ContextComposer` is already skipped in that case today (confirmed by an existing test). There is
no contextual information for anything to be judged pertinent to; an empty relevance operation
would have no subject and no useful judgment to produce.

### Activation

```text
RELEVANCE_PRODUCTION_ACTIVATION_POLICY = BOUND_AUTHORITY
SEPARATE_RELEVANCE_FEATURE_FLAG = NO
```

Relevance production activates purely by whether a concrete realization of the relevance
authority is bound into the runtime object graph -- mirroring the existing
`context_composer: ContextComposer | None` bound-or-absent pattern the preparer already uses. No
new configuration setting or feature flag is introduced: dependency-injection presence is already
a sufficient and unambiguous signal, and ADR-0039 authorizes no new flag. If no authority is
bound, candidates keep `relevance=None`, exactly as today. If one is bound and candidates exist,
exactly one production operation is attempted.

### Backward compatibility

```text
CURRENT_DISABLED_PATH_PRESERVED = YES
CURRENT_ENABLED_NO_PRODUCER_PATH_PRESERVED = YES
ALL_NONE_COMPATIBILITY = YES
```

| Configuration | Behavior |
| --- | --- |
| `prior_task_context_enabled = false` | Unchanged |
| Enabled, zero candidates | Unchanged |
| Enabled, candidates, no authority bound | Unchanged -- production not attempted |
| Enabled, bound authority, successful all-`None` result | Equivalent to current runtime, unconditionally, under `REQUIRED_WHEN_PRIOR_EXISTS` |
| Enabled, bound authority, mixed known/`None` result | Consumed by `ContextComposer`'s existing, already-tested eligibility and ranking logic unchanged |
| Enabled, bound authority, all-known result | Same as above |
| Enabled, bound authority, operational producer failure | Operation fails, via existing propagation convention |

Every configuration that exists today keeps behaving identically; the only new reachable state is
one that cannot occur until a concrete producer is actually bound.

### Generic design versus implementation authorization

```text
PRODUCER_INTEGRATION_SEMANTICS_DECISION_COMPLETE = YES
PRODUCER_INTEGRATION_SEMANTICS_READY = YES
GENERIC_RELEVANCE_INTEGRATION_FOUNDATION_DESIGN_READY = YES
GENERIC_RELEVANCE_INTEGRATION_FOUNDATION_IMPLEMENTATION_READY = YES
GENERIC_RELEVANCE_INTEGRATION_FOUNDATION_IMPLEMENTATION_AUTHORIZED = NO
CURRENT_CONCRETE_RELEVANCE_PRODUCER_EXISTS = NO
AUTHORIZED_DETERMINISTIC_RELEVANCE_ALGORITHM_EXISTS = NO
MODEL_OR_PROVIDER_SELECTED = NO
CONTEXT_RELEVANCE_PRODUCER_IMPLEMENTATION_READY = NO
```

This ADR fixes responsibilities and data semantics only. It does not name a concrete Python
class, `Protocol`, method name, signature, or exception type -- those remain implementation
design questions, not architecture-significant ones, unless future evidence proves otherwise.
`IMPLEMENTATION_READY` means the generic integration design now contains enough decisions for
implementation planning to begin; `IMPLEMENTATION_AUTHORIZED = NO` means this ADR does not itself
authorize writing that runtime code. These are distinct: recording that the design is complete
and ready does not itself authorize the work.

## Not Decided Here

- Any concrete Python type, `Protocol`, method signature, or exception class for the relevance
  authority realization.
- Any scoring algorithm, embedding technique, LLM, provider, or vector store.
- Any change to an architecture dependency allow-list, including whether `cognition.ports` should
  ever be permitted to reference `cognition.domain.context_composition`.
- Any new model or tool call, and any `CognitiveBudget` change.
  `MODEL_BACKED_REALIZATION_IS_SEPARATE_FRONTIER = YES`;
  `MODEL_BACKED_RELEVANCE_FEASIBILITY = REQUIRES_NEW_DECISIONS`;
  `NEW_RUNTIME_MODEL_CALL_AUTHORIZED = NO`; `COGNITIVE_BUDGET_CHANGE_AUTHORIZED = NO`;
  `SYNC_VS_ASYNC_MODEL_BACKED_DECISION = DEFERRED`;
  `PORT_BOUNDARY_CHANGE_FOR_MODEL_BACKED_REALIZATION = UNRESOLVED`.
- A milestone identifier. `NEXT_MILESTONE_IDENTIFIER = UNASSIGNED`; `M0_19_ASSIGNED = NO`.

## Consequences

**Positive:**

- Every integration-side question -- timing, orchestration seam, layer placement, reconstruction
  and validation ownership, failure policy, empty-batch policy, and activation policy -- is now
  closed, entirely independent of any concrete algorithm or provider.
- Every configuration reachable today keeps behaving identically; the only new behavior is
  reachable exclusively once a concrete producer is actually bound, which does not exist yet.
- The chosen shape (`PREPARER_DELEGATES_TO_DISTINCT_RELEVANCE_AUTHORITY`) supplements ADR-0031
  with one narrowly-scoped responsibility rather than relocating any of its existing guarantees.
- A previously undocumented risk -- a legitimate low score defeating required-task coverage -- is
  now recorded as an accepted, understood consequence of preserving ADR-0031 exactly, rather than
  left to be discovered by surprise.

**Tradeoff:**

- `CURRENT_RUNTIME_CHANGED_BY_ADR_0040 = NO`: no executable capability exists after this ADR.
  `PRODUCER_INTEGRATION_SEMANTICS_READY = YES`, but
  `CONTEXT_RELEVANCE_PRODUCER_IMPLEMENTATION_READY = NO`.
  `CURRENT_CONCRETE_RELEVANCE_PRODUCER_EXISTS = NO`; the next architecture blocker is
  `NEXT_CONTEXT_RELEVANCE_ARCHITECTURE_BLOCKER = CONCRETE_RELEVANCE_PRODUCER_REALIZATION` --
  someone must design and implement a concrete class conforming to the integration this ADR
  specifies. This ADR does not authorize starting that work; ADR-0040 must first become canonical.
  These are distinct blockers: `CURRENT_LIFECYCLE_BLOCKER = ADR_0040_CANONICALIZATION` concerns
  this ADR itself becoming canonical, while `NEXT_CONTEXT_RELEVANCE_ARCHITECTURE_BLOCKER` is the
  architecture frontier that opens only after that happens.
  `NEXT_MILESTONE_IDENTIFIER = UNASSIGNED`; `M0_19_ASSIGNED = NO`.
- The known-low required-coverage failure mode remains accepted, not mitigated; if it ever proves
  operationally unacceptable, a future, separately-justified consumer-side decision is required.
- A model-backed realization's execution-modality and port-boundary questions remain fully
  unresolved and are deliberately deferred to whenever that frontier is actually pursued.

## ADR Relationship

ADR-0040 supplements ADR-0031, ADR-0037, ADR-0038, and ADR-0039.

```text
ADR_0040_SUPERSEDES_ADR_0037 = NO
ADR_0040_SUPERSEDES_ADR_0038 = NO
ADR_0040_SUPERSEDES_ADR_0039 = NO
ADR_0031_RELATIONSHIP = SUPPLEMENTED
```

It adds one authorized relevance-delegation step to `ContextPackagePreparer`'s existing
responsibilities while preserving ADR-0031's single-observation ownership, prior-`TASK`
projection, `REQUIRED_WHEN_PRIOR_EXISTS` activation, `ContextRequest` assembly, and
`ContextComposer` invocation exactly as already specified. It does not claim ADR-0005 decided any
implementation detail here; it only notes that no new top-level Cognition subsystem is introduced
and no frozen component's structure changes.
