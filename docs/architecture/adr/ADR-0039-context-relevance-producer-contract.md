# ADR-0039: Context Relevance Producer Contract

- Status: Accepted
- Date: 2026-09-26

## Context

ADR-0037 defined what a known `ContextCandidate.relevance` value means:
`CURRENT_TASK_PERTINENCE`, scoped to one context composition, comparable only within that
composition. ADR-0038 decided who may produce such a value: a generic, Cognition-owned
authority (`COGNITION_CONTEXT_RELEVANCE_AUTHORITY`) applying to any `ContextCandidate`, not
only candidates originating from prior-`TASK` projection. Neither ADR decided the shape of a
production operation itself -- what a conforming producer receives, what it returns, how its
inputs correlate to its outputs, or how a genuine operational failure is distinguished from a
legitimate absence of judgment.

A read-only discovery pass (POST-M0-18DA) traced the full current runtime pipeline end to end
-- from current-task registration through canonical ingestion, projection, request assembly,
composition, materialization, and model execution -- and established, among other things, that
both the current task's exact content and every candidate's exact content are already
resolvable before composition through the existing `RuntimeContentReferenceAuthority`, that no
existing component owns or could own relevance production without a contract change, and that
`ContextComposer` already lets a known relevance value make a currently-succeeding required-slot
composition fail (a real, structural consequence, not a hypothetical one).

A first decision pass (POST-M0-18DB) chose composition-batch granularity, positional
correlation, and a minimal `float | None` result shape, but over-specified the producer's input
by making exact resolved task and candidate content mandatory. A narrow correction pass
(POST-M0-18DBR) identified that this contradicted ADR-0037 itself: `task_ref` is defined there
as an *opaque* semantic reference, and the ADR explicitly states its definition requires neither
payload resolution, text comparison, embedding, LLM execution, nor semantic-search
infrastructure. This ADR records the corrected, final contract.

## Decision

### Inherited semantic authority (ADR-0037)

These are inherited from ADR-0037 unchanged and not reinterpreted here:

```text
CONTEXT_RELEVANCE_SEMANTIC = CURRENT_TASK_PERTINENCE
CONTEXT_RELEVANCE_SEMANTIC_SCOPE = PER_CONTEXT_COMPOSITION
CONTEXT_RELEVANCE_REFERENCE = CURRENT_TASK_DESIGNATED_BY_CONTEXT_REQUEST_TASK_REF
CONTEXT_RELEVANCE_SUBJECT = ONE_CONTEXT_CANDIDATE_CONTEXTUAL_INFORMATION
RELEVANCE_SCALE = NORMALIZED_0_TO_1
NONE_RELEVANCE_SEMANTIC = NO_RELEVANCE_JUDGMENT_EXISTS
RELEVANCE_SCORE_COMPARABILITY_SCOPE = WITHIN_SAME_COMPOSITION_ONLY
CONTEXT_RELEVANCE_SEMANTIC_PROVIDER_INDEPENDENT = YES
CONTEXT_RELEVANCE_SEMANTIC_ALGORITHM_INDEPENDENT = YES
```

### Inherited ownership authority (ADR-0038)

These are inherited from ADR-0038 unchanged; this ADR does not reopen ownership:

```text
RELEVANCE_OWNERSHIP_SCOPE_AUTHORITY = GENERIC_CONTEXT_CANDIDATE
CONTEXT_RELEVANCE_SEMANTIC_OWNER = COGNITION_CONTEXT_RELEVANCE_AUTHORITY
CONTEXT_RELEVANCE_PRODUCTION_AUTHORITY = COGNITION_CONTEXT_RELEVANCE_AUTHORITY
SAME_COMPOSITION_SCORE_AUTHORITY_COHERENCE_REQUIRED = YES
ONE_AUTHORITY_PER_COMPOSITION_SCORE_SET = YES
```

### What one production operation concerns

```text
RELEVANCE_PRODUCER_GRANULARITY = COMPOSITION_BATCH
ONE_PRODUCER_OPERATION_PER_COMPOSITION_BATCH = YES
```

One successful producer operation concerns exactly one context composition's ordered candidate
set, not one candidate at a time. ADR-0037 requires that known relevance scores compared within
one composition share one coherent normalized scale under one applicable authority; it does not
itself mandate how a producer operation is scoped. Single-candidate production could
theoretically preserve that same coherence, but only under an additional invariant enforced
externally to the contract -- that every independent call concerning one composition happens to
be bound to the same authority instance. This ADR selects composition-batch as the canonical
contract instead, because it makes `ONE_AUTHORITY_PER_COMPOSITION_SCORE_SET` true by
construction: one operation invocation is one composition's worth of judgments, under one
authority, with no cross-call coordination required. A composition with exactly one candidate is
simply the degenerate case of a batch of size one; this ADR does not define a canonical contract
shaped around one call per candidate.

### What identifies the current task

```text
CURRENT_TASK_REFERENCE_REQUIRED = YES
CURRENT_TASK_RESOLVED_CONTENT_REQUIRED_BY_CONTRACT = NO
TASK_REF_IS_OPAQUE_SEMANTIC_REFERENCE = YES
```

The generic contract requires the current task's reference -- an opaque semantic identifier,
exactly as ADR-0037 already defines it -- and nothing more. It does not require the task's
exact resolved text, embeddings, model input, or any provider-specific representation. ADR-0037
is explicit that its definition states *what* is judged, not *how* the task is understood or by
what means a judgment is reached; mandating resolved content at the contract level would import
a resolution requirement the semantic itself disclaims. A concrete realization remains entirely
free to resolve the reference into text on its own -- for example through the existing
`RuntimeContentReferenceAuthority` -- but that is a realization or integration choice, not part
of what makes an implementation a conforming Context relevance producer.

### What identifies the candidates being judged

```text
CANDIDATE_RESOLVED_CONTENT_REQUIRED_BY_CONTRACT = NO
GENERIC_PRODUCER_CONTRACT_REQUIRES_RUNTIME_CONTENT_REFERENCE_AUTHORITY = NO
RESOLVED_CONTENT_FORBIDDEN = NO
CONTRACT_IS_GENERIC_ACROSS_CONTEXT_CANDIDATE_TYPES = YES
TASK_SPECIFIC_CONTRACT_REQUIRED = NO
CURRENT_RUNTIME_FIRST_COVERAGE = PRIOR_TASK_ONLY
```

The ordered inputs to one production operation represent the `ContextCandidate` subjects whose
contextual information is being judged, described in terms of the existing `ContextCandidate`/
`ContextSlice` domain representation -- not their resolved payload text. Resolved content is not
forbidden (a realization may still resolve and use it), but it is not mandatory at the contract
level, for the same reason the task reference is not: ADR-0037's subject is "the contextual
information represented by that candidate," and nothing in that definition requires the
information to already be resolved to text before a judgment can be attributed to it. Requiring
exact resolved payload as the only representation (rejected here) would silently import a
text-comparison assumption into a contract ADR-0037 keeps algorithm-independent, and would
exclude any realization built on other separately authorized evidence or realization strategies
that do not require pre-resolved payload text. The contract is generic across all seventeen `ContextSliceType`
values recognized by the domain today; nothing in it names `PriorTaskContextProjector`,
`SituationEntry`, or any prior-`TASK`-specific identity convention. That the only production
runtime coverage that exists today is prior-`TASK`-only is a fact about current realization
coverage, not a constraint the generic contract itself imposes.

### Independent-axis firewall

```text
RELEVANCE_ASSERTS_TRUST = NO
RELEVANCE_ASSERTS_SENSITIVITY = NO
RECENCY_AS_RELEVANCE_AUTHORIZED = NO
RELEVANCE_ASSERTS_ATTENTION_PRIORITY = NO
RELEVANCE_ASSERTS_CONFIDENCE = NO
RELEVANCE_ASSERTS_TRUTH = NO
RELEVANCE_ASSERTS_UTILITY = NO
```

That a candidate's existing classification fields (trust, sensitivity, age, instruction
authority, slice type, content size, provenance) are visible to a producer implementation, by
virtue of being part of the candidate it is asked to judge, does not by itself authorize any of
them as a relevance substitute. ADR-0030 already rejected recency, canonical position, and
same-runtime membership as relevance surrogates; ADR-0012 already established that this
repository's several existing numeric scores (`AttentionDecision.score`,
`CognitiveModeDecision.intrinsic_score`/`effective_score`, `EpistemicClaim.confidence`) each
measure independent axes, none transferable to another by analogy alone. A future realization
may only use a signal in a way separately justified as compatible with `CURRENT_TASK_PERTINENCE`
-- visibility is not authorization.

### Independence from composition policy

```text
PRODUCER_REQUIRES_FULL_CONTEXT_REQUEST = NO
PRODUCER_RECEIVES_MINIMUM_RELEVANCE = NO
PRODUCER_RECEIVES_CONTEXT_COMPOSITION_POLICY = NO
RELEVANCE_PRODUCTION_THRESHOLD_INDEPENDENT = YES
SCORE_CAN_CHANGE_ONLY_BECAUSE_MINIMUM_RELEVANCE_CHANGED = NO
```

The producer judges pertinence; it does not decide eligibility. `ContextComposer` already owns
comparing a known relevance value against `ContextCompositionPolicy.minimum_relevance` for both
required and optional eligibility -- that comparison is unchanged by this ADR. None of
`ContextRequest`'s other fields (`required_slice_types`, `forbidden_slice_types`,
`max_sensitivity`, `minimum_trust`, `allowed_authorities`, `max_age`,
`max_total_content_size`) bear on what pertinence means; they are composition guardrails, not
part of the relevance judgment, so the full `ContextRequest` is not part of the producer's
semantic input either. Keeping the threshold outside the producer means a policy change (a
different `minimum_relevance`) can never, by itself, change what a score *means* -- only whether
an unchanged score clears an unchanged or different bar.

### Correlation

```text
RELEVANCE_CORRELATION_AUTHORITY = POSITIONAL
INPUT_CANDIDATE_ORDER_IS_AUTHORITATIVE = YES
OUTPUT_JUDGMENT_ORDER_MATCHES_INPUT_ORDER = YES
RESULT_CARDINALITY_EQUALS_INPUT_CANDIDATE_CARDINALITY = YES
```

Judgments correlate to candidates by position in the ordered input, not by any field carried on
the candidate itself. `content_ref` is not a valid correlation identity: ADR-0030 already
documents and relies on two distinct prior-`TASK` candidates legitimately sharing one
`content_ref` while differing only in `provenance_ref`. `provenance_ref` carries no
generic uniqueness contract of its own -- its current uniqueness is only
`PriorTaskContextProjector`'s practice for the one candidate family that exists today, not a
guarantee `ContextSlice` makes for every future producer. `SituationEntry.entry_id` is not
generic across candidate types, since a future non-`TASK`-sourced candidate family may have no
`SituationEntry` behind it at all. `slice_type` is not unique -- many candidates in one
composition can share one type. Candidate position within the exact ordered tuple supplied to
one production operation is the only identifier that is simultaneously unique within that
composition, stable for its duration, and generic across every candidate type.

### Successful result

```text
RELEVANCE_PRODUCER_RESULT_SEMANTICS = ORDERED_POSITION_ALIGNED_FLOAT_OR_NONE_TUPLE
```

A successful production operation returns one ordered judgment element for every input
candidate. Each element is exactly one of: a finite float in `[0.0, 1.0]`, representing a known
relevance judgment; or `None`, representing exactly what it already means everywhere else in
this domain -- `NO_RELEVANCE_JUDGMENT_EXISTS` (never a numeric sentinel, never a failure signal).
This is deliberately the smallest shape that preserves the required distinction: it reuses
`ContextCandidate.relevance`'s own existing `float | None` representation rather than
introducing a new value object, a candidate-to-relevance mapping, or copies of `ContextCandidate`
itself carrying a filled-in score. A dedicated wrapper type was considered and rejected here as
an unjustified abstraction on top of a binary this codebase already represents correctly.

```text
SUCCESSFUL_BATCH_MAY_MIX_KNOWN_AND_NO_JUDGMENT = YES
```

A successful batch may legitimately return a known relevance for one candidate and `None` for
another within the same operation -- that is two ordinary, independent semantic outcomes, not
partial failure.

### Operational failure

```text
RELEVANCE_PRODUCTION_FAILURE_SEMANTICS = OPERATION_LEVEL_FAILURE_DISTINCT_FROM_RESULT
NONE_CAN_BE_USED_AS_FAILURE_SIGNAL_WITHOUT_SEMANTIC_AMBIGUITY = NO
OPERATIONAL_FAILURE_IS_RESULT_ELEMENT = NO
OPERATIONAL_FAILURE_DISTINCT_FROM_NONE = YES
PARTIAL_OPERATIONAL_FAILURE_RESULT_AUTHORIZED = NO
```

`None` already means, canonically, that no relevance judgment exists -- a legitimate, expected
outcome ADR-0037 defines. It cannot also mean that an attempt to judge a candidate broke, without
collapsing two operationally distinct states (one ordinary, one an error) into one existing
semantic. This ADR therefore requires that a genuine operational failure be represented as one
signal distinct from the returned judgment tuple, not smuggled into it: if a production operation
cannot successfully complete, the operation fails as a whole and no judgment tuple is returned
for it at all -- there is no partial result mixing real judgments with a per-candidate failure
marker. This mirrors a pattern this repository already uses at a comparable boundary:
`ModelReasoningExecutor` translates provider- and execution-level failures into one distinct
error at its port boundary rather than returning a partially-successful `ReasoningOutcome`. This
ADR does not name a concrete exception type, nor decide retry or timeout behavior; it only fixes
that the distinction between "no judgment" and "failed to judge" must exist and must not be
collapsed onto `None`.

### Same-composition scale authority

```text
ONE_AUTHORITY_PER_COMPOSITION_SCORE_SET = YES
CANDIDATE_RELATIVE_RENORMALIZATION_REQUIRED = NO
```

Because one operation already corresponds to one composition's batch, every known score returned
by that operation is, by construction, produced under the same authority invocation and therefore
shares one coherent scale for that composition -- no separate mechanism is needed to enforce this,
and no candidate-relative mathematical renormalization across results is required. The semantic
only requires that scores be interpretable on one coherent normalized scale for the composition
they belong to, not that they be re-normalized against each other after the fact.

### Known-low required-coverage consequence (not resolved here)

```text
KNOWN_RELEVANCE_CAN_REDUCE_REQUIRED_COVERAGE_ELIGIBILITY = YES
KNOWN_LOW_REQUIRED_TASK_FAILURE_POLICY = UNRESOLVED
KNOWN_LOW_REQUIRED_TASK_POLICY_REQUIRED_BEFORE_RUNTIME_PRODUCTION = YES
LOW_SCORE_CLAMP_TO_MINIMUM_RELEVANCE_AUTHORIZED = NO
LEGITIMATE_LOW_SCORE_TO_NONE_SUBSTITUTION_AUTHORIZED = NO
PRODUCER_MAY_CHANGE_SCORE_TO_PRESERVE_REQUIRED_COVERAGE = NO
```

`ContextComposer` today lets a candidate with unknown relevance satisfy required-type coverage
unconditionally, but rejects a *known* relevance value below `minimum_relevance` even for a
required slot. This means introducing a real producer can turn a composition that currently
succeeds -- because the relevant candidate's relevance is unknown -- into one that fails with
`ContextCompositionUnsatisfiedError`, purely because a real, legitimate low score replaced an
unknown one. This is a genuine downstream consequence, not a hypothetical risk, and this ADR
does not decide how to handle it. What it does fix is a boundary on the producer itself: a
producer must never clamp a legitimate low score upward to avoid this outcome, never substitute
`None` for a real low judgment to dodge composer rejection, and never otherwise adjust its own
judgment to preserve required coverage. If that failure mode needs to be prevented, the fix
belongs in `ContextComposer`'s or the orchestrator's consumer-side policy, not in the producer
lying about what it found.

### Snapshot coherence

```text
PRODUCER_CONTRACT_REQUIRES_CURRENT_SNAPSHOTS_CALL = NO
RELEVANCE_JUDGMENT_SNAPSHOT_COHERENCE_REQUIRED = YES
RELEVANCE_JUDGMENT_SNAPSHOT_COORDINATOR = ContextPackagePreparer
```

The producer contract does not require its own canonical-state observation. `ContextPackagePreparer`
remains the sole owner of the single per-operation snapshot observation established by ADR-0031.
Any producer input that is itself derived from canonical cognitive state -- for example, which
candidates exist in this composition -- must derive from that one existing observation; this ADR
does not authorize a second, independent `current_snapshots()` call. This is not a claim that
every producer input originates there: `task_ref` and other non-snapshot authorities are not
canonical-state observations, and resolving a content reference through
`RuntimeContentReferenceAuthority` is a separate concern from observing canonical
Workspace/Situation state -- it is not reclassified as canonical-state observation merely because
it may participate in producer input. This ADR does not choose how the producer receives its
input.

### Current runtime and lifecycle consequence

```text
CURRENT_CONCRETE_RELEVANCE_PRODUCER_EXISTS = NO
CURRENT_RUNTIME_CONTEXT_CANDIDATE_PRODUCER_SCOPE = PRIOR_TASK_ONLY
CURRENT_RUNTIME_CHANGED_BY_ADR_0039 = NO
```

ADR-0039 defines a producer contract; it does not itself make relevance production executable,
does not wire any component, and does not change what the current runtime does.

```text
CONTEXT_RELEVANCE_PRODUCER_CONTRACT_DECISION_COMPLETE = YES
CONTEXT_RELEVANCE_PRODUCER_CONTRACT_READY = YES
CONTEXT_RELEVANCE_PRODUCER_IMPLEMENTATION_READY = NO
NEXT_CONTEXT_RELEVANCE_BLOCKER = PRODUCER_INTEGRATION_SEMANTICS
NEXT_MILESTONE_IDENTIFIER = UNASSIGNED
M0_19_ASSIGNED = NO
```

This records architectural state only; it does not authorize or begin producer-integration work.

## Explicitly Not Decided Here

```text
RELEVANCE_PRODUCER_TIMING = UNRESOLVED
CONTEXT_COMPOSER_PRODUCTION_SEAM_ALLOWED = NO
PRIOR_TASK_CONTEXT_PROJECTOR_PRODUCTION_SEAM_AUTHORIZED = NO
CONTEXT_PACKAGE_PREPARER_RUNTIME_WIRING_AUTHORIZED = NO

CONCRETE_LAYER_PLACEMENT = UNRESOLVED
CURRENT_PORT_LAYER_CAN_REFERENCE_CONTEXT_COMPOSITION = NO
PORT_BOUNDARY_CHANGE_AUTHORIZED = NO
APPLICATION_LAYER_ORCHESTRATION_FIT = HIGH
INFRASTRUCTURE_CAN_OWN_SEMANTICS = NO

EXECUTION_MODALITY_IS_SEMANTIC = NO
SYNC_VS_ASYNC = IMPLEMENTATION_DECISION

AUTHORIZED_DETERMINISTIC_RELEVANCE_ALGORITHM_EXISTS = NO
MODEL_OR_PROVIDER_SELECTED = NO
MODEL_BACKED_RELEVANCE_FEASIBILITY = REQUIRES_NEW_DECISIONS
MODEL_ROUTER_CAN_OWN_RELEVANCE_SEMANTICS = NO
NEW_RUNTIME_CALL_AUTHORIZED = NO
COGNITIVE_BUDGET_CHANGE_AUTHORIZED = NO

RELEVANCE_RETENTION_AUTHORITY = NONE
```

This ADR does not name a concrete Python type, a `Protocol`/interface name, a method signature,
or a choice of synchronous versus asynchronous execution -- none of that follows necessarily
from the semantic contract decided above, and pinning one down here would be exactly the
speculative structure `AGENTS.md` asks this project to avoid. It does not choose a concrete
package or layer (domain, application, ports, or infrastructure) for a future realization, does
not authorize any change to an architecture dependency allow-list -- `cognition.ports` still
cannot reference `cognition.domain.context_composition` today, and this ADR does not decide
whether that should ever change -- and does not select a runtime invocation seam
(`ContextComposer`, `PriorTaskContextProjector`, and unauthorized `ContextPackagePreparer`
wiring all remain exactly as frozen or unauthorized as before). It selects no algorithm, no
provider, no model, no embedding technique, and no vector store; it authorizes no new model or
tool call and no `CognitiveBudget` change. It defines no failure exception class, no retry
behavior, and no timeout behavior beyond requiring that failure be distinct from `None`. It does
not resolve the known-low required-coverage policy from the previous section, does not create any
persistence or cross-composition retention authority, and does not introduce a runtime feature
flag or assign an implementation milestone. `ADR-0005`'s frozen COGNITION V1 component set is
unaffected: this ADR adds no new top-level Cognition subsystem and changes no frozen component's
structure -- it says nothing about how any of those components are implemented internally.

## Consequences

**Positive:**

- The producer contract is now fully specified at the semantic level -- input identity, batch
  granularity, correlation, result shape, and failure separation -- without committing to any
  concrete type, layer, or realization technology.
- Correcting the input boundary (removing the mandatory-resolved-content requirement) keeps the
  contract compatible in principle with deterministic, model-backed, caller-supplied, and hybrid
  realizations alike, exactly preserving ADR-0037's provider and algorithm independence.
- The minimal `float | None` result shape and positional correlation avoid inventing new domain
  types where the existing ones already suffice, and avoid a correlation mechanism ADR-0030's own
  evidence already rules out.
- A previously undocumented but real risk -- known relevance production breaking currently-
  succeeding required-coverage compositions -- is now recorded explicitly, with the producer
  forbidden from papering over it, rather than left to be discovered by surprise during
  implementation.

**Tradeoff:**

- No executable producer exists after this ADR. `CONTEXT_RELEVANCE_PRODUCER_CONTRACT_READY = YES`,
  but `CONTEXT_RELEVANCE_PRODUCER_IMPLEMENTATION_READY = NO`.
- Timing, layer placement, and execution modality remain open, so no runtime wiring or dependency
  change can yet be derived from this ADR alone.
- The known-low required-coverage policy remains unresolved; until it is, enabling any real
  relevance production against required-type candidates carries a known, undecided risk of
  composition failure.

## ADR Relationship

ADR-0039 supplements ADR-0037 (Context relevance semantics, the prerequisite this ADR's contract
serves) and ADR-0038 (Context relevance ownership, which this ADR's generic, `ContextCandidate`-
wide contract shape is consistent with).

```text
ADR_0039_SUPERSEDES_ADR_0037 = NO
ADR_0039_SUPERSEDES_ADR_0038 = NO
```

It supersedes neither. It does not claim ADR-0005 decided any implementation detail of this
contract; it only notes that nothing here reopens ADR-0005's frozen COGNITION V1 component set.
