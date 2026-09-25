# ADR-0038: Context Relevance Ownership

- Status: Accepted
- Date: 2026-09-25

## Context

ADR-0037 defines what `ContextCandidate.relevance` means: when a known value exists, it asserts
`CURRENT_TASK_PERTINENCE` -- the normalized degree to which one candidate's contextual information
is judged pertinent to the current task designated by `ContextRequest.task_ref`, for the one context
composition in which the candidate is considered. The score is comparable only within that same
composition, and `ContextCompositionPolicy.minimum_relevance` is interpreted relative to the
applicable relevance authority's normalized scale. ADR-0037 explicitly declined to decide who
produces a known relevance value, how it is computed, or what happens when production fails.

Current production state, unchanged by this ADR:

- `PriorTaskContextProjector` (ADR-0030) projects every prior canonical `TASK` entry into a
  `ContextCandidate` with `relevance=None`. Its contract explicitly applies no relevance judgment.
- `ContextPackagePreparer` (ADR-0031) owns the single per-operation canonical-state observation and
  coordinates projection, request assembly, and composition, but scores no relevance.
- `ContextComposer` consumes `relevance` for eligibility and ranking; it derives no value.
- `RuntimeContentReferenceAuthority` resolves opaque content references to exact runtime-local
  payloads; it carries no cognitive interpretation of what it resolves.
- No known relevance value has ever been produced in this repository: every candidate that exists
  in the runtime today carries `relevance=None`.

A read-only architecture discovery pass (POST-M0-18CQ) examined every component that could
plausibly already own production of a known relevance judgment -- the projector, the preparer, the
composer, the request assembler, the runtime content authority, the canonical input ingestor,
`AttentionEngine`, `CognitiveWorkspace`/`CognitiveItem`, `SituationModel`, the caller/process layer,
and `model_router` -- and found that none of them does, and none of them could without an explicit
contract change. A subsequent decision pass (POST-M0-18CR) resolved one narrow question left open by
that discovery: whether a new Cognition-owned authority, once introduced, should own
`CURRENT_TASK_PERTINENCE` generically for any `ContextCandidate`, or only for candidates originating
from prior-`TASK` projection. This ADR records that decision.

ADR-0012 records a directly relevant precedent: the numeric scores already in this repository --
`AttentionDecision.score`, `CognitiveModeDecision.intrinsic_score`/`effective_score`,
`ContextCandidate.relevance`, `EpistemicClaim.confidence` -- each measure a different axis governed
by its own component-specific policy, and none is transferable to another by analogy alone. This ADR
treats that precedent as a reason to keep Context relevance's own axis under one coherent authority
rather than letting it fragment by candidate type.

## Decision

### Ownership scope

```text
RELEVANCE_OWNERSHIP_SCOPE_AUTHORITY = GENERIC_CONTEXT_CANDIDATE
```

Ownership of `CURRENT_TASK_PERTINENCE` production applies to known relevance judgments for any
`ContextCandidate` participating in a context composition -- not only candidates produced by
`PriorTaskContextProjector`. This follows ADR-0037's own subject, which is already generic
(`ONE_CONTEXT_CANDIDATE_CONTEXTUAL_INFORMATION`, not a TASK-specific subject), and it avoids a
foreseeable coherence problem: `ContextSliceType` already declares seventeen distinct values
(`IDENTITY`, `GOAL`, `TASK`, `SITUATION`, `MEMORY`, `EVIDENCE`, `CLAIM`, `HYPOTHESIS`, `PLAN`,
`POLICY`, `CONSTRAINT`, `EMOTION`, `SELF_MODEL`, `CAPABILITY`, `TOOL`, `HISTORY`, `ENVIRONMENT`), and
`ContextRequest.required_slice_types`/`forbidden_slice_types` already allow more than one of them to
participate in a single composition. `ContextComposer` already applies one relevance ranking
dimension and one `minimum_relevance` threshold uniformly across whatever types appear in a
composition, without branching on slice type. Splitting relevance ownership per candidate type would
require, the moment two types coexisted in one composition, either an explicit mapping between
independently-produced scores or a re-derivation of comparability that ADR-0037 already grants for
free under one authority.

This is an ownership-scope decision, not an implementation-coverage claim:

```text
CURRENT_RUNTIME_CONTEXT_CANDIDATE_PRODUCER_SCOPE      = PRIOR_TASK_ONLY
GENERIC_OWNER_WITH_PRIOR_TASK_ONLY_CURRENT_RUNTIME    = COHERENT
```

Generic semantic ownership does not require every candidate family to have an implemented relevance
producer today, and does not require `PriorTaskContextProjector` or any other component to change.
`CURRENT_CONCRETE_RELEVANCE_PRODUCER_EXISTS = NO`.

### Semantic and production authority

```text
CONTEXT_RELEVANCE_SEMANTIC_OWNER      = COGNITION_CONTEXT_RELEVANCE_AUTHORITY
CONTEXT_RELEVANCE_PRODUCTION_AUTHORITY = COGNITION_CONTEXT_RELEVANCE_AUTHORITY
RUNTIME_RELEVANCE_PRODUCER_OWNER       = COGNITION_CONTEXT_RELEVANCE_AUTHORITY
```

`COGNITION_CONTEXT_RELEVANCE_AUTHORITY` is a conceptual architecture authority inside Cognition. It
is not a Python class, module, package, `Protocol`, or service instance -- none of those are named or
required by this ADR. `CONCRETE_RELEVANCE_SCORER_IMPLEMENTATION = UNRESOLVED`.

The normative invariant this authority establishes:

> The Cognition Context Relevance Authority owns production authority for known
> `ContextCandidate.relevance` judgments: for any candidate considered in one context composition,
> any known relevance value must represent `CURRENT_TASK_PERTINENCE` under that authority's coherent
> normalized scale for that composition.

No component may emit a known `ContextCandidate.relevance` value except under this authority. This
definition names no algorithm, provider, timing, or failure behavior.

```text
SAME_COMPOSITION_SCORE_AUTHORITY_COHERENCE_REQUIRED       = YES
ONE_AUTHORITY_PER_COMPOSITION_SCORE_SET                   = YES
GENERIC_AUTHORITY_ALLOWS_MULTIPLE_REALIZATION_STRATEGIES  = YES
OWNERSHIP_MUST_ACCOUNT_FOR_THRESHOLD_SCALE_COHERENCE       = YES
```

Every known relevance value compared within one composition must be governed by this one authority.
This does not require one scoring algorithm: the authority may, in the future, be realized by more
than one mechanism across different candidate families, as long as every realization answers to the
same semantic authority and the same normalized scale that `ContextCompositionPolicy.minimum_relevance`
is interpreted against. No threshold value or calibration is chosen here.

```text
CONTEXT_RELEVANCE_SEMANTIC_PROVIDER_INDEPENDENT  = YES
CONTEXT_RELEVANCE_SEMANTIC_ALGORITHM_INDEPENDENT = YES
```

No provider (Ollama, an LLM, an embedding model, a vector store) and no algorithm (lexical overlap,
semantic similarity, embedding distance, classifier output, LLM judgment, heuristic weighting) is
selected, required, or precluded by this ADR.

### Semantic home, not physical placement

```text
CONTEXT_COMPOSITION_IS_SEMANTIC_HOME       = YES
NEW_TOP_LEVEL_COGNITIVE_SUBSYSTEM_REQUIRED = NO
```

The ownership concern belongs conceptually to the existing Context Composition concern: its subject
is `ContextCandidate`, its consumer is `ContextComposer`, its threshold is
`ContextCompositionPolicy.minimum_relevance`, and its scope is per context composition -- all of
which already live inside `cognition.domain.context_composition`. ADR-0005 freezes `Context Composer`
as one of COGNITION V1's structural components; this ADR introduces no new top-level V1 Cognition
subsystem and does not claim ADR-0005 decided relevance ownership -- it only notes that nothing here
requires reopening ADR-0005's frozen component set.

This is a semantic-home finding, not a package or class placement decision:

```text
CONCRETE_LAYER_PLACEMENT = UNRESOLVED
```

Prior discovery found: a pure domain-layer judgment type is feasible in principle but constrained
today by each domain package's individually enforced dependency allow-list
(`DOMAIN_LAYER_RELEVANCE_JUDGMENT_FEASIBLE = PARTIAL`); the application layer already has every
dependency such an authority would need (`APPLICATION_LAYER_ORCHESTRATION_FIT = HIGH`); a port typed
directly with `ContextCandidate` is not legal today
(`CURRENT_PORT_LAYER_CAN_REFERENCE_CONTEXT_COMPOSITION = NO`, enforced by
`tests/architecture/test_domain_dependencies.py::test_cognition_ports_has_only_allowed_noema_dependencies`,
whose allow-list for `cognition.ports` permits only `cognition.domain.planning`,
`cognition.domain.reasoning`, and `cognition.ports` itself); and infrastructure must not originate
semantics (`INFRASTRUCTURE_CAN_OWN_SEMANTICS = NO`). None of this is resolved here.
`PORT_BOUNDARY_CHANGE_AUTHORIZED = NO` -- the current dependency rule forbids a
context-composition-typed port today, and this ADR does not decide whether a later architecture
change should permit it.

### Existing-component boundaries, unchanged

This ADR changes no existing component's contract. It records, for the avoidance of doubt, that none
of the following owns Context relevance semantics, and this ADR does not authorize any of them to:

```text
CONTEXT_PACKAGE_PREPARER_OWNS_RELEVANCE_SEMANTICS               = NO
CONTEXT_PACKAGE_PREPARER_ORCHESTRATION_ROLE                     = POTENTIAL_SEAM_NOT_YET_AUTHORIZED
RELEVANCE_JUDGMENT_SNAPSHOT_COHERENCE_REQUIRED                  = YES
RELEVANCE_JUDGMENT_SNAPSHOT_COORDINATOR                         = ContextPackagePreparer

PRIOR_TASK_CONTEXT_PROJECTOR_OWNS_RELEVANCE_SEMANTICS           = NO

CONTEXT_COMPOSER_OWNS_RELEVANCE_PRODUCTION                      = NO
CONTEXT_COMPOSER_ROLE                                           = RELEVANCE_CONSUMER

RUNTIME_CONTENT_REFERENCE_AUTHORITY_OWNS_RELEVANCE_SEMANTICS    = NO

ATTENTION_OWNS_CONTEXT_RELEVANCE_SEMANTICS                      = NO
WORKSPACE_OWNS_CONTEXT_RELEVANCE_SEMANTICS                      = NO
SITUATION_OWNS_CONTEXT_RELEVANCE_SEMANTICS                      = NO
MODEL_ROUTER_CAN_OWN_RELEVANCE_SEMANTICS                        = NO
```

`ContextPackagePreparer` remains the single-snapshot coordination seam it already is (ADR-0031); this
ADR does not elevate it to semantic owner and authorizes no invocation wiring. `PriorTaskContextProjector`
keeps exactly the contract ADR-0030 gave it: it projects prior `TASK` candidates and applies no
relevance judgment. `ContextComposer` keeps consuming relevance for eligibility and ranking, never
producing it -- production and consumption remain distinct components, independent of ADR-0005's
structural freeze. `RuntimeContentReferenceAuthority` may continue to supply resolved content as an
input to a future producer without owning the judgment itself. `AttentionEngine`'s score (a weighted
composite across urgency, novelty, risk, and other axes ADR-0037 requires to stay independent) is not
Context relevance, is not reusable as one by direct substitution, and no mapping from it is
authorized. `CognitiveWorkspace`/`CognitiveItem.relevance` carries no established
`CURRENT_TASK_PERTINENCE` semantic and no mapping from it is authorized. `SituationModel` remains
canonical situational state, not a relevance authority. A future model-backed realization, if ever
separately authorized, remains governed by this Cognition-owned semantic authority --
`model_router` cannot itself own Cognition relevance semantics.

## Not Decided Here

- `CONCRETE_RELEVANCE_SCORER_IMPLEMENTATION` -- no scorer is named or designed.
- `CONTEXT_RELEVANCE_PRODUCER_CONTRACT_READY = NO` -- no method signature, input/output DTO,
  batch-vs-single-candidate shape, or sync/async choice is made.
- `RELEVANCE_PRODUCER_TIMING = UNRESOLVED` -- whether production happens during projection, after
  projection but before composition, or elsewhere is not decided.
- `RELEVANCE_JUDGMENT_CORRELATION_AUTHORITY = UNRESOLVED` -- whether `content_ref`, `provenance_ref`,
  `entry_id`, or candidate position is the correlation identity is not decided.
- `RELEVANCE_PRODUCTION_FAILURE_SEMANTICS = UNRESOLVED` -- failure-to-None, retry, candidate
  exclusion, and operation failure are all undecided; `None` is not defined as a producer-failure
  signal by this ADR.
- `KNOWN_LOW_REQUIRED_TASK_FAILURE_POLICY = UNRESOLVED`.
- `RELEVANCE_RETENTION_AUTHORITY = NONE` -- ownership does not imply persistence.
- Concrete layer placement (domain, application, ports, or infrastructure).
- Any dependency allow-list change, including whether `cognition.ports` should ever be permitted to
  reference `cognition.domain.context_composition`.
- Any model or tool call, and any `CognitiveBudget` change.
  `MODEL_BACKED_RELEVANCE_FEASIBILITY = REQUIRES_NEW_DECISIONS`;
  `OWNERSHIP_DECISION_REQUIRES_NEW_RUNTIME_CALL = NO` -- this ADR authorizes no call.
- A milestone identifier. `NEXT_MILESTONE_IDENTIFIER = UNASSIGNED`; `M0_19_ASSIGNED = NO`.

## Consequences

**Positive:**

- The question left open by ADR-0037 -- who may own production of a known relevance value -- now has
  a settled, durable answer at the semantic-scope level, without inventing a class, package, or port.
- Future `ContextCandidate` producers beyond `PriorTaskContextProjector` inherit one coherent
  semantic authority and scale instead of each needing their own relevance semantics or an
  after-the-fact reconciliation between independently-produced scores.
- `CURRENT_PRIOR_TASK_RUNTIME_COMPATIBLE_WITH_OWNERSHIP_DECISION = YES`: every existing candidate
  keeps `relevance=None` exactly as before -- "no relevance judgment exists" remains legal, and this
  ADR does not require immediate production. `CURRENT_RUNTIME_VALUE_OF_RELEVANCE_PRODUCTION = MEDIUM`:
  `ContextComposer` already makes unknown-relevance candidates ineligible for optional enrichment, so
  producing real values would unlock capability that is structurally unreachable today -- but that
  value is bounded to today's one producer and gated behind an opt-in flag, not immediately realized
  by this ADR.
- Existing frozen and previously-decided boundaries (`ContextComposer` as consumer, `ContextPackagePreparer`
  as snapshot coordinator, `PriorTaskContextProjector`'s no-judgment contract, Attention/Workspace/
  Situation/`model_router` exclusion) are reaffirmed rather than reopened.

**Tradeoff:**

- No executable relevance-production capability exists after this ADR. `CONTEXT_RELEVANCE_OWNERSHIP_DECISION_COMPLETE = YES`,
  but `CONTEXT_RELEVANCE_PRODUCER_CONTRACT_READY = NO` and
  `CONTEXT_RELEVANCE_PRODUCER_IMPLEMENTATION_READY = NO`.
- `NEXT_CONTEXT_RELEVANCE_BLOCKER = PRODUCER_CONTRACT`: timing, correlation identity, and failure
  semantics all remain open and are not started here.
- Layer placement remains unresolved, so no structural or dependency-allow-list change can yet be
  derived from this ADR alone.

## ADR Relationship

ADR-0038 supplements ADR-0037 (context relevance semantics, the prerequisite this ADR records
ownership against), ADR-0030 (unknown-relevance representation and rejected relevance substitutes),
ADR-0031 (the current prior-TASK-only production pipeline and its explicit deferral of relevance
scoring), and ADR-0012 (independent-score-axes precedent, cited above). It mentions ADR-0005 only to
note that no new top-level Cognition subsystem is introduced; it does not claim ADR-0005 decided
relevance ownership. ADR-0038 supersedes none of these.
