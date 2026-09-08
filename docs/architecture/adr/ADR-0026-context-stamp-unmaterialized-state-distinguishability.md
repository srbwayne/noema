# ADR-0026: ContextStamp Unmaterialized-State Distinguishability

- Status: Accepted
- Date: 2026-09-07

> Status `Accepted` records approval of the semantic decision by its decision review. Repository
> `main` authority is established by repository history and merge state, independently of this
> status label.

## Context

`ContextStamp` (`src/noema/cognition/domain/context/context_stamp.py`) currently declares five
mandatory fields:

```text
workspace_version
situation_version
identity_version
goal_version
policy_version
```

Each field structurally accepts only a non-negative `int` (booleans, negatives, and any other
runtime type are rejected without coercion). The class docstring describes it as "Versions of
cognitive state observed when an operation starts," and its `__post_init__` docstring frames its
own validation purpose as rejecting "versions that cannot represent an observed state." This ADR
distinguishes two different properties of any given field value:

- **structural version validity** — whether the stored value is a well-typed, non-negative
  integer, which the existing implementation already enforces;
- **semantically observed state version** — whether that integer actually corresponds to a real,
  versioned state dimension that was legitimately observed for the operation it describes.

A first attempt at real runtime-composition work (constructing an actual `ContextRequest`, and
therefore an actual `ContextStamp`, for the already-approved minimal DIRECT-strategy Reasoning
path) required a real answer to this question and, in doing so, surfaced a pre-existing semantic
gap rather than creating a new one: `ContextStamp` was authored in the repository's original
foundation commit without an accompanying rationale document, and no ADR, prior to this one, has
ever addressed what a version means for a dimension whose architecturally named owner is not
materialized. `RUNTIME_NEED_DISCOVERED_THE_GAP`, not `RUNTIME_CONVENIENCE_DETERMINED_THE_DECISION`
— this decision does not rest on making the first runtime easier to build.

Two of `CognitiveWorkspace` and `SituationModel` already exist as real, versioned domain state
owners, each defaulting a freshly constructed instance to `version = 0`. The other three
dimensions currently have no comparable status, and not identically so:

- `identity_version` names Identity, an official Noema bounded context (`Agent != LLM`: agent
  identity belongs to the runtime, independently of any model provider), which currently has no
  domain implementation at all;
- `goal_version` names a "goal" concept that has no identified, versioned domain owner anywhere in
  the repository;
- `policy_version` names a "policy" concept whose owner is unidentified — several unrelated,
  unversioned policy value objects exist (`AttentionPolicy`, `CognitiveModePolicy`,
  `ContextCompositionPolicy`), but none is a singular, versioned, cross-cutting governance-state
  concept matching what this field appears intended to track.

`CURRENT_AUTHORITY_DID_NOT_DEFINE_UNMATERIALIZED_OWNER_SEMANTICS`. No accepted architecture, prior
to this ADR, states whether an ordinary observed-version value such as `0` may legitimately stand
in for a dimension with no materialized (or, for identity/goal/policy, not-yet-identified) state
owner.

## Decision

### Unmaterialized-state distinguishability requirement

An unmaterialized `ContextStamp` state dimension is semantically distinct from every
materialized-and-observed state version. This distinction includes an observed initial version of
`0`: a dimension with a real, tracked state owner that has legitimately never been mutated is not
the same thing, semantically, as a dimension whose owner does not exist or has not been identified
at all.

Conceptually: `CONTEXT_STAMP_UNMATERIALIZED_STATE_DISTINGUISHABILITY = REQUIRED`.

### Zero semantic firewall — critical boundary

`ZERO_VERSION != UNMATERIALIZED_STATE`. Zero remains, and has always been, a fully legitimate
observed version for a real state owner — `CognitiveWorkspace` and `SituationModel` both default a
freshly constructed instance to `version = 0`, and this ADR does not disturb that. What this ADR
freezes is narrower: that `0` (or any other ordinary version value) must not be used to silently
stand in for a dimension whose owner is not materialized. Observed-zero and unmaterialized-absent
are two different states; this ADR requires that they remain distinguishable, not that zero itself
becomes forbidden, unusual, or reinterpreted as an absence marker.

### Structural validity is unchanged

This ADR is semantic authority, not a code change. `ContextStamp(0, 0, 0, 0, 0)` remains exactly as
structurally constructible as it was before this ADR — nothing in `context_stamp.py` is modified by
this decision. `CURRENT_STRUCTURAL_ACCEPTANCE != SEMANTIC_AUTHORIZATION_FOR_UNMATERIALIZED_STATE`:
the fact that the constructor accepts a value has never been, and is not hereby treated as,
evidence that using that value to represent an unmaterialized owner is semantically sound.

### Representation explicitly unresolved

`CONTEXT_STAMP_UNMATERIALIZED_STATE_REPRESENTATION = UNRESOLVED`. This ADR does not select, name,
or sketch any mechanism for representing the required distinction. It does not approve, and this
ADR does not create, any of: `Optional[int]`, `None`, a negative sentinel, a `0` sentinel, a new
`Enum`, a wrapper type, an availability flag, field removal, field addition, a narrower
`ContextStamp`, a replacement stamp type, or any other carrier. The minimum representation strategy
remains a separate, later, dedicated decision.

### No materialization requirement

`DISTINGUISHABILITY_REQUIRED != MISSING_STATE_OWNERS_MUST_BE_IMPLEMENTED`. This ADR does not decide
that Identity, Goal, or Policy state must be implemented before runtime composition may proceed.
Requiring real owners to exist is only one of several possible future strategies for satisfying the
distinguishability requirement; this ADR does not select it, or any other strategy, now.

### Owner ambiguity preserved

`GOAL_VERSION_OWNER = UNIDENTIFIED` and `CONTEXT_STAMP_POLICY_OWNER = UNIDENTIFIED` remain exactly
as unresolved as they were before this ADR. This ADR does not invent a `Goal` aggregate, a
`GlobalPolicy`, a `PolicyState`, an `AgentPolicy`, a `GovernanceState`, or any other replacement
concept to serve as either field's owner.

### Identity architecture unchanged

Identity remains an official Noema bounded context, and agent identity remains the runtime's
responsibility, independent of any model provider (`Agent != LLM`, ADR-0002). This ADR does not
define Identity structure, does not create an Identity domain class, and does not decide how
Identity versioning — if any — will eventually work. `IDENTITY_ARCHITECTURE_UNCHANGED = YES`.

### Materialized-but-unobserved firewall

This decision applies only to `UNMATERIALIZED_STATE_OWNER` — a dimension whose architecturally
named owner does not exist, or has not been identified, in the current domain model.
`MATERIALIZED_BUT_UNOBSERVED_STATE_SEMANTICS = DEFERRED`: this ADR does not decide the semantics
for a state owner that exists and is materialized but was not read, was temporarily unavailable, or
was intentionally omitted for a given operation. Those remain separate, undecided questions for a
possible future frontier.

### Workspace / Situation firewall

`CognitiveWorkspace` and `SituationModel` are real, versioned domain state owners whose fresh
instances default to `version = 0`. This ADR does not thereby authorize using that default without
actually constructing or observing the relevant instance. `WORKSPACE_ZERO_WITHOUT_OBSERVATION =
NOT_ESTABLISHED` and `SITUATION_ZERO_WITHOUT_OBSERVATION = NOT_ESTABLISHED` remain exactly as
unresolved as this ADR found them; whether a value may legitimately be cited without constructing a
real instance is a representation-and-observation question left to later, separate discovery.

### Concurrency wording

Preserving distinguishability avoids preemptively collapsing information that may be relevant to
future version/concurrency semantics. This ADR does not state or imply that `ContextStamp` already
performs optimistic concurrency control, or that any current production code compares its versions
for staleness. `VERSION_WITHOUT_STATE_OWNER_HAS_CONCURRENCY_MEANING = NOT_ESTABLISHED`.

### Runtime-composition relationship

The first minimal DIRECT runtime-composition analysis required a real `ContextRequest`, and
therefore a semantically legitimate `ContextStamp`, to exist before a `ReasoningRequest` could be
constructed at all. That practical need is what surfaced this pre-existing gap; it is not the
justification for this decision. `RUNTIME_NEED_DISCOVERED_THE_GAP != RUNTIME_CONVENIENCE_
DETERMINED_THE_DECISION`.

### Verification isolation

This is not a Verification decision and does not touch any Verification contract. Process state
`M0_15_VERIFICATION_WORKSTREAM_PARKED = YES` is preserved, unaffected by this ADR.

### Architecture freeze relationship

This ADR adds semantic authority for an existing, already-accepted COGNITION V1 contract
(`ContextStamp`). It does not itself modify the frozen COGNITION V1 structure that ADR-0005
establishes. Any later structural representation change — for example, one of the families
discussed under "Alternatives Considered" below — remains fully subject to ADR-0005 governance and
requires its own explicit ADR before implementation.

### Decision summary

| Concern | Decision |
| --- | --- |
| Unmaterialized-state distinguishability | Required |
| Zero as a valid observed version | Unchanged, remains valid |
| Zero as the sole unmaterialized-state marker | Not permitted; zero remains a valid observed version |
| `ContextStamp` structural shape | Unchanged |
| Representation mechanism | Unresolved |
| Missing-owner implementation requirement | Not decided |
| Goal / Policy owner identity | Unidentified, unchanged |
| Identity structure | Unchanged |
| Materialized-but-unobserved semantics | Deferred |
| Workspace / Situation zero-without-observation | Not established |
| Concurrency behavior | Not established |
| Runtime composition readiness | Remains blocked |

## Alternatives Considered

### Reuse the observed-version domain (rejected)

An unmaterialized state dimension could reuse the same ordinary non-negative integer domain already
used for materialized, observed state (for example, using `0` for an absent owner). This was
rejected as the semantic decision here because it collapses two materially different states —
"owner exists and was genuinely observed at version zero" and "owner is not materialized at all" —
into an identical stored value, without any positive accepted authority establishing that the
collapse is safe. The only supporting evidence found (that the constructor structurally accepts
such values) demonstrates structural validity only, not semantic soundness.

### Require distinguishability (accepted)

Adopted as recorded above. Representation is deliberately left open.

### Leave distinguishability unresolved (rejected)

The decision review that preceded this ADR found sufficient semantic evidence — the class and
`__post_init__` docstrings' own "observed state" framing, the forward-materialization collision
risk, the information-preservation and reversibility asymmetry between the two positions, and the
architectural risk of fabricating Identity state in particular — to resolve the requirement question
without needing to select a representation. Leaving it unresolved was therefore rejected as
unnecessarily indecisive given the available evidence.

## Non-Decisions / Deferred

- No representation is selected.
- No `ContextStamp` field or type is changed.
- No absence marker is selected.
- No Identity model is defined.
- No Goal model or owner is defined.
- No Policy owner is defined.
- No composition-root ownership is decided.
- No `CognitiveMode` bootstrap source is decided.
- No `CognitiveBudget` source or default is decided.
- No Ollama configuration value is decided.
- No runtime implementation is authorized.
- Materialized-but-unobserved state semantics remain deferred.

## Consequences

**Positive:**

1. An ordinary observed version can no longer silently stand in for a state dimension whose owner
   does not exist, preserving information that later architectural work may need.
2. Zero remains fully legitimate as an observed version for real state owners (`CognitiveWorkspace`,
   `SituationModel`); nothing about its existing behavior changes.
3. The decision is representation-neutral: it commits to no specific mechanism, keeping future
   design flexibility fully open.
4. Fabricating apparent Identity, Goal, or Policy state is explicitly disallowed as a way to satisfy
   `ContextStamp`, protecting Identity's ownership boundary in particular.

**Tradeoff:**

1. `ContextStamp` cannot yet be legitimately constructed for any dimension lacking a materialized,
   identified owner; runtime composition for the minimal DIRECT path remains blocked pending a
   separate representation decision.
2. A later, potentially structural, decision is still required to actually satisfy this
   requirement, and that decision may itself require its own ADR under ADR-0005 governance.
3. Goal and Policy owner ambiguity is not resolved by this ADR and continues to block any concrete
   representation strategy that would depend on knowing those owners.

## Relationship to Existing Architecture

This ADR complements ADR-0005 (COGNITION V1 frozen) and ADR-0002 (agent independent from any LLM
provider). It does not supersede either. ADR-0005 remains authoritative for COGNITION V1's frozen
structure; this ADR adds semantic authority for `ContextStamp`'s existing, unchanged shape without
altering that structure. ADR-0002 remains authoritative for the Agent-!=-LLM boundary that this
ADR's Identity-preservation guard exists to protect. This ADR does not modify, narrow, or extend
any prior ADR in the M0-15 Verification sequence (ADR-0015 through ADR-0025); it addresses an
unrelated, previously undiscovered gap in the Context Composition domain surfaced by unrelated
runtime-composition discovery work.
