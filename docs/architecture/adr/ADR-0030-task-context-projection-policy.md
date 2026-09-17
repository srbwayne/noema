# ADR-0030: Task Context Projection Policy

- Status: Accepted
- Date: 2026-09-17

## Context

M0-17 established that a single first-DIRECT runtime instance can execute more than one
sequential reasoning operation, accumulating one canonical `SituationEntryKind.TASK` entry per
operation in `SituationModel`. M0-18 established `RuntimeContentReferenceAuthority`, a
runtime-instance-scoped, register/resolve-only authority through which every canonical `TASK`
entry's exact input payload remains resolvable for the runtime's lifetime.

Neither milestone made this accumulated state usable as cognitive context: `ContextComposer`
(frozen, unintegrated) had no production `ContextCandidate` provider, `ContextCandidate.relevance`
had no representation for "no relevance judgment exists," and `ContextSlice.token_estimate`,
`ContextRequest.max_tokens`, and `ContextPackage.total_token_estimate` claimed model-tokenizer
semantics that no component in the repository could honestly produce -- `model_router` exposes no
tokenizer, and `cognition/domain/context_composition` is architecturally forbidden from depending
on it (`tests/architecture/test_domain_dependencies.py`).

This ADR records the frozen decisions that make prior canonical `TASK` entries into constructible,
honestly-classified `ContextCandidate` values, corrects the token-shaped schema to a truthful
provider-independent content-size budget, and introduces a standalone application-layer projector.
It does not integrate any of this into runtime execution.

## Decision

### Projection scope

```text
PROJECTION_KIND_SCOPE = TASK_ONLY
RUNTIME_SCOPE = FIRST_DIRECT_RUNTIME_GENERAL
TASK_PROJECTION_SCOPE = PRIOR_TASKS_ONLY
```

`TASK` is the only `SituationEntryKind` with a production producer in the first-DIRECT runtime
(`CanonicalInputIngestor`). Only *prior* `TASK` entries are projected.

### Current-task identity

```text
CURRENT_TASK_IDENTIFICATION = positionally most-recent SituationEntryKind.TASK entry
    among TASK-kind entries in the supplied Situation snapshot
CURRENT_TASK_CONTEXT_DUPLICATION = FORBIDDEN
```

Identity is positional, never `content_ref`-based: two distinct canonical `TASK` entries may
legitimately share a `content_ref` (M0-18's write-once registration is idempotent on repeat
registration, while canonical ingestion still appends a fresh entry per operation). The current
task is excluded from projection because it already travels separately as
`ReasoningRequest.problem_statement`; projecting it would duplicate it.

### Ordering

```text
PROJECTION_ORDER = preserve canonical Situation entry order
PROJECTOR_PERFORMS_RANKING = NO
```

### Reference-based slice mapping

```text
SituationEntryKind.TASK -> ContextSliceType.TASK
ContextSlice.content_ref = SituationEntry.content_ref (exact pass-through)
ContextSlice.provenance_ref = str(SituationEntry.entry_id)
```

No new identifier is introduced. `content_ref` remains the exact `RuntimeContentReferenceAuthority`
lookup key; `provenance_ref` distinguishes distinct canonical entries that happen to share a
`content_ref`.

### Classification (static, V1)

```text
zone = ContextPackageZone.COGNITIVE_STATE
sensitivity = ContextSensitivity.SECRET   # CONSERVATIVE_HANDLING_UPPER_BOUND, fail-closed
trust = ContextTrustLevel.UNVERIFIED       # absence of positive origin verification
instruction_authority = None               # historical content never carries active authority
```

`sensitivity=SECRET` is an explicit, disclosed conservative policy, not a claim that task content
is intrinsically secret: no fixed value can truthfully classify arbitrary task text, and no
payload-aware classifier is authorized in this frontier, so classification fails closed. This
requires an operator to explicitly configure `max_sensitivity=SECRET` before prior-TASK context
becomes eligible for composition -- an intentional governance property, not an oversight.

### Age

```text
TASK_CONTEXT_AGE_SEMANTICS = CANONICAL_ENTRY_AGE_AT_PROJECTION_SNAPSHOT
age = projection_snapshot.updated_at - prior_entry.created_at
AGE_REQUIRES_PAYLOAD = NO
NEGATIVE_AGE_POLICY = EXPLICIT_FAILURE
```

No wall-clock read. Both operands are already-frozen fields on the observed immutable snapshot.

### Content-size budget (schema correction)

```text
CONTEXT_COMPOSITION_BUDGET_SEMANTICS = PROVIDER_INDEPENDENT_EXACT_CONTENT_SIZE
CONTEXT_SIZE_UNIT = RAW_UNICODE_CODE_POINT_COUNT
content_size = len(exact_resolved_payload)
UNICODE_NORMALIZATION_BEFORE_MEASUREMENT = NO
```

`token_estimate`/`max_tokens`/`total_token_estimate` falsely implied model-tokenizer semantics
that no component in the repository could honestly produce, and the word "estimate" was itself
inaccurate for what is always an *exact* measurement. Renamed:

```text
ContextSlice.token_estimate           -> ContextSlice.content_size
ContextRequest.max_tokens             -> ContextRequest.max_total_content_size
ContextPackage.total_token_estimate   -> ContextPackage.total_content_size
```

`CognitiveBudget.max_tokens` is a separate, untouched abstraction; its relationship to
context-composition size, if any, remains an open question for a future decision.

### Relevance epistemics

```text
ContextCandidate.relevance: float | None
None = NO RELEVANCE JUDGMENT EXISTS (never a numeric sentinel: not 0.0, 0.5, or 1.0)
```

Every projected prior-`TASK` candidate has `relevance = None`: no repository-backed scoring
authority exists (no production relevance provider; `AttentionEngine` is unwired, operates on a
different domain object, and does not resolve the same missing signal). Recency, canonical
position, and same-runtime membership are explicitly rejected as relevance substitutes.

### Unknown-relevance composition semantics

```text
REQUIRED_TYPE_AUTHORITY_SCOPE = COVERAGE_BOUND
REQUIRED_TYPE_CARDINALITY = AT_LEAST_ONE_PER_TYPE
```

Known relevance must satisfy `policy.minimum_relevance` in both required and optional phases,
exactly as before. Unknown relevance may compete for required coverage only while its slice type
is explicitly unsatisfied in `request.required_slice_types` -- the consumer's explicit requirement
supplies positive authority in the specific absence of a relevance judgment; it never overrides a
known, below-threshold score (`ContextPackage`'s own required-type validation is a set-membership
check -- "at least one slice of this type" -- never "every eligible candidate of this type,"
confirming the requirement is a coverage guarantee, not an ongoing license). Unknown relevance is
never eligible for optional enrichment, and a surplus unknown-relevance candidate that does not
win a required slot is never subsequently admitted as optional enrichment once another candidate
has satisfied that requirement.

At the relevance ranking dimension, known relevance always precedes unknown; among known values
higher relevance is preferred; among unknown values candidates tie and the comparison falls
through to the next existing dimension (age, then input position) -- mirroring the composer's
existing `age is None` handling. This ranking dimension sits exactly where relevance already sat
in both existing sort keys; it does not outrank the dimensions that already precede it
(content size, sensitivity, trust in the required key).

### Projector ownership and realization

```text
PROJECTOR_NAME = PriorTaskContextProjector
PROJECTOR_LAYER = cognition.application
```

`cognition/domain/context_composition` cannot own this: it is architecturally forbidden from
importing `cognition.application` (`RuntimeContentReferenceAuthority`'s home), confirmed by
`tests/architecture/test_domain_dependencies.py::test_cognition_domain_does_not_import_cognition_application`.
No existing application component owns this responsibility without violating its own frozen,
narrower scope (`CanonicalInputIngestor`, `ContextRequestAssembler`, `DirectReasoningOperation` all
explicitly exclude constructing `ContextCandidate` values or resolving runtime content).

```text
PriorTaskContextProjector(runtime_content_authority: RuntimeContentReferenceAuthority)
    .project(*, situation: SituationModel) -> tuple[ContextCandidate, ...]
```

The projector performs no canonical-state observation of its own -- it receives an
already-observed `SituationModel` snapshot from its caller, rather than calling
`CognitiveStateOwner.current_snapshots()` itself. `ContextRequestAssembler` already performs
exactly one such observation per assembly; a second, independent observation inside the projector
would risk two divergent snapshots backing one operation. It resolves each prior entry's exact
payload through the bound authority, read-only, purely to measure `content_size`; it never stores,
returns, or otherwise exposes payload text. It performs no ranking, no policy selection, no
`ContextComposer` invocation, no `ContextPackage` construction, and mutates neither the supplied
`SituationModel` nor the bound authority.

### Zero/one/multi-TASK behavior

```text
zero TASK entries  -> return ()   (not a failure -- mirrors SituationModel.entries_of_kind's
                                    existing graceful-empty behavior; unreachable in the normal
                                    integrated runtime path, since a current operation's own
                                    ingest_task always runs first)
one TASK entry     -> return ()   (no prior task exists)
multiple TASK      -> project every entry except the positionally last one
```

### Failure propagation

Existing exceptions propagate unchanged; no projector-specific wrapper is introduced:

```text
missing registered content  -> RuntimeContentReferenceNotFoundError
negative derived age        -> InvalidContextCandidateError
invalid constructed slice   -> InvalidContextSliceError
invalid constructed candidate -> InvalidContextCandidateError
```

### Duplicate content_ref

Two distinct prior `SituationEntry` values may share a `content_ref` (different `entry_id`). They
project to two distinct `ContextCandidate` values with the same `content_ref` but different
`provenance_ref`. No deduplication.

### Snapshot-version coherence (future integration requirement, not implemented here)

```text
SNAPSHOT_VERSION_COHERENCE_REQUIRED = YES
```

A future integration must guarantee that the same `SituationModel` observation backs both the
projector's input and `ContextRequest.context_stamp.situation_version`, so that projected
candidates and the accompanying `ContextRequest` never silently reference different canonical
states. This ADR does not implement that integration and does not change
`ContextRequestAssembler`'s existing single-observation-per-assembly contract.

## Explicit non-decisions and firewalls

```text
CONTEXT_COMPOSER_RUNTIME_INTEGRATION = NO
NONEMPTY_CONTEXT_PACKAGE_RUNTIME_USE = NO
MODEL_CONTEXT_MATERIALIZATION = NO
DIRECT_REASONING_OPERATION_RUNTIME_WIRING = NOT_CHANGED
DIRECT_PRIOR_TASK_CONCATENATION = UNACCEPTABLE

MODEL_HISTORY = NO
DURABLE_MEMORY = NO
DATABASE = NO
VECTOR_STORE = NO
SEMANTIC_RETRIEVAL = NO
CROSS_PROCESS_CONTENT_RESOLUTION = NO
```

`RuntimeContentReferenceAuthority` and the canonical `Situation` it resolves against remain
same-runtime cognitive state (M0-18), not persistent memory. This ADR does not claim runtime
integration exists: `PriorTaskContextProjector` is realized and independently testable, but no
production code path constructs or consumes its output yet.

## Non-decisions

This ADR does not assign a milestone identifier, does not decide the relationship between
`ContextRequest.max_total_content_size` and `CognitiveBudget.max_tokens`, does not select a token
estimation or model-context rendering approach, and does not decide goal, mode-arbitration, or
planning integration.

## Consequences

Positive:

- prior canonical `TASK` entries are now constructible, honestly-classified `ContextCandidate`
  values, independently testable without any runtime wiring;
- the context-composition schema no longer makes an unbacked model-tokenizer claim;
- `ContextComposer`'s required/optional eligibility correctly distinguishes a genuine absence of
  relevance judgment from a known-low judgment, with no surplus-authority leak.

Deferred:

- runtime integration of the projector into `DirectReasoningOperation`;
- `ContextComposer` wiring into runtime execution;
- model-context materialization and any real token/size accounting for a specific provider;
- the `ContextRequest.max_total_content_size` / `CognitiveBudget.max_tokens` relationship;
- relevance scoring beyond the frozen unknown-relevance eligibility policy.
