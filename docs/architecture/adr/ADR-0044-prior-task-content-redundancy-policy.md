# ADR-0044: Prior-TASK Content Redundancy Policy

- Status: Accepted
- Date: 2026-10-06

## Context

ADR-0030 made prior canonical `TASK` entries projectable as `ContextCandidate` values. It
identifies the current task positionally and forbids projecting it as context:

```text
CURRENT_TASK_IDENTIFICATION = positionally most-recent SituationEntryKind.TASK entry
    among TASK-kind entries in the supplied Situation snapshot
CURRENT_TASK_CONTEXT_DUPLICATION = FORBIDDEN
```

The same ADR states that identity is "positional, never `content_ref`-based", and that two
distinct prior entries sharing a `content_ref` project to two distinct candidates with different
`provenance_ref`, with "No deduplication".

ADR-0031 integrated prior-`TASK` context end to end. `CanonicalInputIngestor` appends one fresh
`TASK` entry per operation, and `REQUIRED_WHEN_PRIOR_EXISTS` makes `TASK` a required slice type
exactly when at least one prior candidate is projected.

ADR-0037 through ADR-0040 defined Context relevance as `CURRENT_TASK_PERTINENCE`: a per-candidate
judgment that asserts neither utility nor necessity, owned by `COGNITION_CONTEXT_RELEVANCE_AUTHORITY`
and consumed, not produced, by `ContextComposer`.

ADR-0041 selected `NORMALIZED_EXACT_TASK_CONTENT_MATCH`: a candidate receives `1.0` exactly when its
payload, normalized only by line-ending unification (CRLF, then CR, to LF) and Unicode NFC, is
substantive and equal to the normalized current-task payload; every other candidate receives
`None`. ADR-0041 recorded as a runtime consequence that "repeated identical prior tasks with
substantive content may contribute multiple slices of identical content", and both ADR-0041 and
ADR-0042 listed "Deduplication of repeated identical prior tasks" under "Not Decided Here".

The production binding ADR-0042 describes is canonical on `main`, and ADR-0043 clarified that it is
technically active whenever prior-`TASK` context is enabled. The deferred question therefore now
governs reachable runtime behavior:

- the first-DIRECT process generates a fresh `task_ref` per problem, and canonical ingestion
  appends a fresh entry with a fresh `entry_id`, so repeated problems become distinct prior
  entries with distinct `content_ref` and `provenance_ref` values;
- every candidate the ADR-0041 realization judges `1.0` is normalized-equal to the current task,
  so all of them are mutually equivalent;
- the existing `ContextComposer` structural-duplicate check compares whole `ContextSlice` values,
  which always differ across distinct entries, so content-equivalent candidates can all be
  selected -- one for required `TASK` coverage and the rest as optional enrichment, bounded by
  `max_slices` and `max_total_content_size`;
- a prior entry whose content equals the current task can be selected even though the current
  entry itself is excluded positionally;
- `PriorTaskContextMaterializer` renders each selected slice as its own block, so equivalent
  payloads appear more than once in model input.

The canonical test
`test_enabled_runtime_bound_relevance_authority_enriches_exact_matching_prior_tasks` in
`tests/unit/test_bootstrap.py` already asserts this behavior through the real production graph:
with three sequential operations carrying the same problem, the second model input contains the
repeated payload once and the third contains it twice.

No existing invariant is violated by this behavior, and no existing ADR decides whether content
equivalence should affect selection. This ADR decides that question.

## Decision

### Normative policy

Each distinct canonical prior `TASK` entry is a distinct prior-`TASK` context unit.

Equality of task content -- raw or normalized, between prior entries or between a prior entry and
the current task -- is not a redundancy criterion and has no effect on projection, relevance,
required-`TASK` activation, or composition.

ADR-0030's prohibition on current-task context duplication applies only to the current `TASK`
entry itself, identified positionally, and does not extend to distinct earlier entries with
equivalent content.

Repeated equivalent prior `TASK`s remain independently eligible under the existing
`ContextComposer` rules and are bounded only by the existing `max_slices` and
`max_total_content_size` limits.

ADR-0041 normalized equality remains a relevance/pertinence judgment only.

### Context unit identity

```text
PRIOR_TASK_CONTEXT_UNIT_IDENTITY = CANONICAL_ENTRY_IDENTITY
PRIOR_TASK_CONTENT_EQUIVALENCE_AFFECTS_SELECTION = NO
RAW_CONTENT_EQUALITY_IS_REDUNDANCY_CRITERION = NO
NORMALIZED_CONTENT_EQUALITY_IS_REDUNDANCY_CRITERION = NO
```

A prior-`TASK` context unit is identified by its canonical `SituationEntry` (`entry_id`, carried as
`provenance_ref`). Neither `content_ref` equality nor payload equality merges, suppresses, or
otherwise relates two units.

### Current-task equivalence

```text
CURRENT_TASK_ENTRY_DUPLICATION_POLICY = FORBIDDEN_POSITIONALLY
CURRENT_TASK_EQUIVALENT_PRIOR_POLICY = ALLOWED_AS_HISTORICAL_CONTEXT
```

The current `TASK` entry itself is never projected, exactly as ADR-0030 decides. A distinct earlier
entry whose content equals the current task -- byte-for-byte or after ADR-0041 normalization -- is a
separate canonical event recording that the same task occurred before. It is ordinary historical
context, not a duplicate of the current entry.

### Historical equivalence

```text
HISTORICAL_EQUIVALENT_PRIOR_POLICY = ALL_DISTINCT_ENTRIES_ALLOWED
```

Several prior entries with equal raw or normalized content are each independently eligible. No
equivalence class, representative, or one-per-content limit exists.

### Required coverage

```text
REQUIRED_WHEN_PRIOR_EXISTS_EVALUATION = UNCHANGED
```

ADR-0031's activation is evaluated exactly as today: after projection and relevance
reconstruction, over the full projected candidate population. `TASK` becomes required exactly when
at least one prior candidate is projected, regardless of content equivalence.

### Stage and ownership

```text
REDUNDANCY_STAGE = NONE
REDUNDANCY_POLICY_OWNER = NONE_REQUIRED
```

No redundancy stage exists in the preparation pipeline. Selection remains governed solely by the
existing `ContextComposer` eligibility, ordering, and limits. `ContextPackagePreparer`'s
responsibilities under ADR-0031 and ADR-0040 are unchanged.

### Relevance preserved

```text
RELEVANCE_ASSERTS_REDUNDANCY = NO
RELEVANCE_NORMALIZED_EQUALITY_MEANING = CURRENT_TASK_PERTINENCE_ONLY
RELEVANCE_SEMANTICS_CHANGED = NO
RELEVANCE_ALGORITHM_CHANGED = NO
```

ADR-0041's normalized equality establishes maximal pertinence of a candidate to the current task.
It says nothing about whether a candidate is redundant with the current task or with another
candidate. ADR-0037's `RELEVANCE_ASSERTS_UTILITY = NO` and `RELEVANCE_ASSERTS_NECESSITY = NO`, and
ADR-0039's independent-axis firewall, are preserved.

### Composition preserved

```text
CONTEXT_COMPOSER_ORDERING_CHANGED = NO
MAX_SLICES_SEMANTICS_CHANGED = NO
MAX_TOTAL_CONTENT_SIZE_SEMANTICS_CHANGED = NO
```

Required-slot and optional-enrichment eligibility, both sort orders, the structural-duplicate check,
`max_slices`, and `max_total_content_size` keep their current meaning.

### Implementation state

```text
IMPLEMENTATION_REQUIRED = NO
TEST_CHANGES_REQUIRED = NO
```

The canonical runtime already behaves as this ADR decides. The following canonical tests already
pin the decided behavior:

- `tests/unit/test_bootstrap.py`:
  - `test_enabled_runtime_bound_relevance_authority_enriches_exact_matching_prior_tasks`
- `tests/unit/cognition/application/test_normalized_exact_task_content_relevance_authority.py`:
  - `test_duplicate_matching_candidates_each_receive_full_relevance`
- `tests/unit/cognition/application/test_prior_task_context_projector.py`:
  - `test_duplicate_content_ref_among_prior_entries_creates_two_candidates`
  - `test_same_content_ref_as_current_task_does_not_affect_positional_exclusion`
- `tests/unit/cognition/domain/context_composition/test_context_composer.py`:
  - `test_context_composer_accepts_same_content_ref_for_distinct_slices`
  - `test_two_known_candidates_one_required_remainder_may_become_optional`

### Deferred items closed

```text
ADR_0041_IDENTICAL_PRIOR_TASK_DEDUPLICATION_DEFERRAL = RESOLVED_BY_ADR_0044
ADR_0042_IDENTICAL_PRIOR_TASK_DEDUPLICATION_DEFERRAL = RESOLVED_BY_ADR_0044
```

### Milestone state

```text
NEXT_MILESTONE_IDENTIFIER = UNASSIGNED
M0_19_ASSIGNED = NO
```

## Rationale

- **Canonical history is a sequence of distinct events.** ADR-0030 and ADR-0031 append one `TASK`
  entry per operation and identify the current task positionally, never by content. Treating
  content-equal entries as one unit would introduce a content identity that canonical state itself
  does not have.
- **Repetition carries information.** Repeated occurrence of the same task records historical
  frequency, and each occurrence keeps its own provenance and age. Suppression would discard both.
- **Relevance is pertinence, not utility.** Relevance is a per-candidate judgment of pertinence to
  the current task (ADR-0037, ADR-0039). Whether a slice adds anything beyond another slice is a
  utility or necessity question that relevance explicitly does not assert, so it cannot be derived
  from the existing relevance judgment.
- **No harm is established.** No repository evidence shows that repeated equivalent context harms
  model output. A policy that suppresses context on that ground would be solving an unproven
  problem.
- **The mechanical costs are already bounded.** Repeated slices consume `max_slices` slots, raw
  content-size capacity, and rendered model input, but only within the limits an operator already
  configures through `max_slices` and `max_total_content_size`.
- **Suppression would add unrequired semantics.** Any suppression policy needs a content-identity
  notion, representative semantics, a new owning stage, and an explicit ordering against
  `REQUIRED_WHEN_PRIOR_EXISTS`. No current evidence requires any of these.
- **The canonical relevance binding stays meaningful.** Under ADR-0041, every candidate judged `1.0`
  belongs to the single class of content equivalent to the current task. Suppressing historical
  equivalents (P2) would cap the binding's effect at one added slice; suppressing current-task
  equivalents (P3, P4) would remove exactly the candidates it judges, making the realization
  behaviorally inert.

## Alternatives Considered

### P1: Keep current behavior

```text
P1_KEEP_CURRENT_BEHAVIOR = ACCEPTED
```

Selected, as decided above.

### P2: Suppress historical equivalents

```text
P2_SUPPRESS_HISTORICAL_EQUIVALENTS = REJECTED
```

At most one selected slice per content-equivalence class among prior tasks, while a prior
equivalent to the current task remains eligible. Rejected because it introduces a content identity
for context units that canonical history does not define, discards the provenance and recurrence
frequency of suppressed entries, and requires new representative and ownership semantics -- all
motivated only by mechanical capacity costs that existing limits already bound. Because every
ADR-0041 `1.0` judgment falls in one equivalence class, it would also reduce the canonical
relevance binding to at most one added slice.

### P3: Suppress current-task-equivalent priors

```text
P3_SUPPRESS_CURRENT_EQUIVALENT_PRIORS = REJECTED
```

Prior tasks equivalent to the current task are excluded from context. Rejected because it would
extend ADR-0030's positional current-entry rule into a content-based rule, contrary to ADR-0030's
explicit "never `content_ref`-based" identity; it would change ADR-0031 coverage, since a runtime
whose priors all equal the current task would project no usable candidate and lose required `TASK`
coverage; and it would remove exactly the candidates ADR-0041 judges relevant, making the canonical
ADR-0041/ADR-0042 relevance binding behaviorally inert.

### P4: Suppress both

```text
P4_SUPPRESS_BOTH = REJECTED
```

The union of P2 and P3. Rejected for every reason given for P3, which dominate, together with P2's
unrequired identity, representative, and ownership semantics.

## Not Decided Here

- The relation between `ContextRequest.max_total_content_size` and `CognitiveBudget.max_tokens`,
  or any token conversion.
- Model context-window authority.
- Required-slot ranking, including whether relevance should outrank `content_size`.
- Lexical or graded relevance.
- Model-backed relevance.
- Relevance or redundancy for `ContextCandidate` families other than prior `TASK`.
- Deployment or service governance.
- Any future, evidence-driven reopening of redundancy policy.

A future redundancy policy would require a new architectural decision. This ADR prescribes neither
its owner nor its algorithm.

## Consequences

**Positive:**

- No production code change.
- No test change required; the decided behavior is already pinned by canonical tests.
- The canonical ADR-0041/ADR-0042 relevance binding remains behaviorally meaningful.
- Provenance and recurrence frequency of repeated tasks remain representable in context.
- Existing deterministic `ContextComposer` behavior remains unchanged.

**Tradeoffs:**

- Repeated equivalent prior `TASK`s can consume multiple `max_slices` slots.
- Repeated equivalent prior `TASK`s consume raw content-size capacity.
- Repeated equivalent prior `TASK`s increase rendered model input.
- Repetition may be redundant for some model tasks, but no quality harm is currently established.

## ADR Relationship

ADR-0044 supplements ADR-0030 (Task context projection policy), ADR-0031 (End-to-end prior-task
context runtime integration), ADR-0041 (First deterministic context relevance realization), and
ADR-0042 (Production relevance authority binding conditionality). It supersedes none of them.

```text
ADR_0044_SUPPLEMENTS_ADR_0030 = YES
ADR_0044_SUPPLEMENTS_ADR_0031 = YES
ADR_0044_SUPPLEMENTS_ADR_0041 = YES
ADR_0044_SUPPLEMENTS_ADR_0042 = YES
ADR_0044_SUPERSEDES_ADR_0030 = NO
ADR_0044_SUPERSEDES_ADR_0031 = NO
ADR_0044_SUPERSEDES_ADR_0041 = NO
ADR_0044_SUPERSEDES_ADR_0042 = NO
```

It clarifies that ADR-0030's current-task duplication prohibition remains positional and
entry-based, and that ADR-0041's duplicate-slice runtime consequence is an explicitly accepted
policy outcome rather than merely an observed tradeoff.

ADR-0037, ADR-0038, ADR-0039, ADR-0040, and ADR-0043 are preserved unchanged. ADR-0044 introduces no
new top-level Cognition subsystem and changes no frozen ADR-0005 component's structure.
