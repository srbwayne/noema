# ADR-0027: ContextStamp Unmaterialized-State Representation

- Status: Accepted
- Date: 2026-09-08

> Status `Accepted` records approval of the architectural decision by its decision review. Repository
> `main` authority is established by repository history and merge state, independently of this
> status label.

## Context

ADR-0026 froze that an unmaterialized `ContextStamp` state dimension must remain semantically
distinguishable from every materialized-and-observed state version, including an observed initial
version of `0`, while explicitly leaving the representation mechanism unresolved:
`CONTEXT_STAMP_UNMATERIALIZED_STATE_REPRESENTATION = UNRESOLVED`. ADR-0026 also froze that `0`
remains a fully legitimate observed version, that a bare version value alone may not serve as the
sole marker of absence, and that materialized-but-unobserved state semantics remain a wholly
separate, deferred question.

A sequence of read-only architectural discoveries and decision reviews then decomposed and resolved
that representation question. Discovery work found the current owner-materialization status differs
by dimension on accepted authority, not by incidental implementation accident:

- `workspace_version` and `situation_version` each name a real, materialized, versioned domain
  owner — `CognitiveWorkspace` and `SituationModel` — both of which default a freshly constructed
  instance to `version = 0`;
- `identity_version` names Identity, an official Noema bounded context (`Agent != LLM`, ADR-0002),
  which currently has no materialized versioned domain owner at all;
- `goal_version` and `policy_version` each name a dimension whose versioned owner remains
  unidentified — no `Goal` domain class exists anywhere in the repository, and none of the
  repository's several unrelated, unversioned "Policy" value objects (`AttentionPolicy`,
  `CognitiveModePolicy`, `ContextCompositionPolicy`) is a plausible singular, versioned owner for
  `policy_version`.

A representation candidate space was constructed and normalized, admissibility criteria were
applied uniformly, and a decision review selected exactly one family and exactly one field-carrier
scope for that family, evaluated against the current, dimension-specific owner-materialization
authority above. This ADR records the result of that selection. It does not reopen ADR-0026's
distinguishability requirement, and it does not create any production contract by itself.

Process gate reports underlying this discovery are cited here only as process history establishing
how this question was decomposed. They are not architectural authority. This ADR's decision rests on
accepted architecture (ADR-0002, ADR-0005, ADR-0026) and on the completed decision review, not on the
gate reports themselves.

## Decision

### Selected representation family

The unmaterialized-state representation for `ContextStamp` is a **tagged scalar union**:

Conceptually: `CONTEXT_STAMP_UNMATERIALIZED_STATE_REPRESENTATION = F2_TAGGED_SCALAR_UNION`.

A relevant dimension's value is either:

- an **observed version** — a non-negative integer, exactly as today; or
- an explicitly named **`UNMATERIALIZED`** marker, distinct from every observed integer including
  zero.

`F2_STATE_VARIANTS = (OBSERVED_VERSION, UNMATERIALIZED)`. `F2_STATE_VARIANT_COUNT = 2`. No
additional variant (`UNKNOWN`, `UNAVAILABLE`, `NOT_OBSERVED`, `OMITTED`, `FAILED`, `STALE`,
`NOT_LOADED`, or any other) is introduced by this ADR.

### Field carrier scope — SCOPE-A

The union carrier type is applied **asymmetrically**, per current owner-materialization authority:

```text
workspace_version: OBSERVED_VERSION only
situation_version: OBSERVED_VERSION only

identity_version:  OBSERVED_VERSION | UNMATERIALIZED
goal_version:       OBSERVED_VERSION | UNMATERIALIZED
policy_version:     OBSERVED_VERSION | UNMATERIALIZED
```

Conceptually: `CONTEXT_STAMP_F2_FIELD_SCOPE = SCOPE_A`; `CONTEXT_STAMP_CARRIER_TYPE_SYMMETRY =
ASYMMETRIC`; `CONTEXT_STAMP_UNMATERIALIZED_ADMISSIBILITY = FIELD_SPECIFIC`.

`UNMATERIALIZED_ALLOWED_DIMENSIONS = (identity, goal, policy)`.
`UNMATERIALIZED_DISALLOWED_DIMENSIONS = (workspace, situation)`.

`TYPE_UNIFORMITY != DOMAIN_CORRECTNESS`: a uniformly-shaped carrier type across all five fields was
considered and not selected, because it would let `workspace_version`/`situation_version` structurally
represent a state (`UNMATERIALIZED`) that current accepted authority does not recognize for either
dimension — their owner classes are materialized today. SCOPE-A instead makes each field's type
directly reflect exactly the states current authority authorizes for it, with no reliance on
additional runtime validation to forbid an otherwise-representable illegal combination.

### Scope wording — critical boundary

`UNMATERIALIZED_ALLOWED_DIMENSIONS` and `UNMATERIALIZED_DISALLOWED_DIMENSIONS` describe **current
accepted-authority scope**, not a permanent metaphysical statement about any dimension. If future
accepted architecture changes a dimension's owner-materialization status — for example, if Workspace
or Situation's owning infrastructure were ever restructured such that their materialization status
changed — that would require its own separately evidenced architectural decision under the same
governance this ADR itself required (see "Relationship to Existing Architecture" below); it is not
authorized, implied, or precluded by this ADR.

### Identity owner-status normalization

`IDENTITY_OWNER_STATUS = UNMATERIALIZED_OWNER`. Identity is an official architectural bounded
context (AGENTS.md; ADR-0002's `Agent != LLM` boundary), but no versioned Identity state owner is
currently materialized anywhere in the repository. This ADR does not define Identity structure, does
not create an Identity domain class, and does not decide how Identity versioning will eventually
work. `IDENTITY_ARCHITECTURE_UNCHANGED = YES`.

### Workspace / Situation semantics preserved

`WORKSPACE_OWNER_STATUS = MATERIALIZED_VERSIONED_OWNER`; `SITUATION_OWNER_STATUS =
MATERIALIZED_VERSIONED_OWNER`. Current authority therefore does not permit using `UNMATERIALIZED`
for either field. `WORKSPACE_ZERO_WITHOUT_OBSERVATION = NOT_ESTABLISHED` and
`SITUATION_ZERO_WITHOUT_OBSERVATION = NOT_ESTABLISHED` remain exactly as unresolved as before — those
are runtime cognitive-state lifetime/ownership questions (this ADR's "B2 firewall" below), not
representation questions, and this ADR does not touch them.

### Critical semantic firewall — unmaterialized vs. unobserved

`UNMATERIALIZED_OWNER != MATERIALIZED_OWNER_BUT_UNOBSERVED`. `MATERIALIZED_BUT_UNOBSERVED_STATE_
SEMANTICS = DEFERRED`, exactly as ADR-0026 left it. The `UNMATERIALIZED` marker introduced by this
ADR may be used **only** to represent that a dimension's versioned owner does not currently exist. It
must not be reused, now or by any future code, to represent: an owner that exists but was not read
for a given operation; a temporarily unavailable owner; a read failure; an intentionally omitted
state; or a stale observation. Each of those remains a separate, undecided future question.

### Observed-version domain unchanged

`OBSERVED_VERSION` remains exactly what it already was: a non-negative integer. `ZERO_AS_OBSERVED_
VERSION = VALID` (ADR-0026, unchanged). This ADR does not alter the meaning or validity of any
existing observed-version value.

### Concrete marker spelling deferred

`CONCRETE_UNMATERIALIZED_MARKER_SPELLING = DEFERRED`. This ADR is an information-model decision, not
an implementation decision. It does not select, name, or sketch any concrete Python realization of
the `UNMATERIALIZED` marker — not `Enum`, not a singleton, not a dedicated marker class, not a
sentinel integer, not `None`, not any specific class, module, or member name. Those remain
implementation detail for a later, non-architectural step.

### Structural consequence — implementation not yet authorized

The current implementation —

```text
workspace_version: int
situation_version: int
identity_version: int
goal_version: int
policy_version: int
```

— cannot yet represent the information model this ADR accepts (`identity_version`, `goal_version`,
and `policy_version` need to admit a second, non-integer variant). `B1_ARCHITECTURAL_DECISION_
COMPLETE = YES`; `B1_IMPLEMENTATION_COMPLETE = NO`. This ADR records architectural authority only; it
does not modify `ContextStamp`, and no implementation is authorized by it alone.

### B2 firewall — runtime cognitive-state lifetime and ownership

`RUNTIME_COGNITIVE_STATE_LIFETIME_AND_OWNERSHIP = UNRESOLVED`. `SELECTED_REPRESENTATION_SOLVES_B2 =
NO`. This ADR does not define Workspace lifetime, Situation lifetime, any canonical runtime instance,
any operation-observation boundary, any state persistence mechanism, or any `CognitiveCoordinator`
ownership. Those remain entirely separate, unresolved questions.

### B3 firewall — composition-root placement

`COMPOSITION_ROOT_PLACEMENT = UNRESOLVED`. `SELECTED_REPRESENTATION_SOLVES_B3 = NO`. This ADR does
not select `main.py`, a bootstrap module, a composition module, a runtime container, or any
dependency-injection framework as the location for future runtime wiring.

### No speculative shared abstraction

`SHARED_PACKAGE_JUSTIFICATION_ESTABLISHED = NO`. This ADR does not define a generic, reusable
version-state abstraction in `shared`. Any future implementation of the accepted information model
remains local to the appropriate cognition/context domain unless concrete evidence later establishes
genuine cross-context sharing (AGENTS.md: do not introduce abstractions before a concrete use
demonstrates they are shared).

### Verification isolation

This ADR is unrelated to Verification semantics. `M0_15_VERIFICATION_WORKSTREAM_PARKED = YES` is
preserved, unaffected.

### Decision summary

| Concern | Decision |
| --- | --- |
| Representation family | `F2_TAGGED_SCALAR_UNION` |
| State variants | `OBSERVED_VERSION`, `UNMATERIALIZED` (2 total) |
| Observed-version domain | Non-negative integer (unchanged) |
| Field carrier scope | `SCOPE_A` (asymmetric) |
| `workspace_version` / `situation_version` | `OBSERVED_VERSION` only |
| `identity_version` / `goal_version` / `policy_version` | `OBSERVED_VERSION \| UNMATERIALIZED` |
| Identity owner status | Unmaterialized owner |
| Workspace / Situation owner status | Materialized versioned owner (unchanged) |
| Materialized-but-unobserved semantics | Deferred (unchanged) |
| Concrete marker spelling | Deferred |
| Runtime cognitive-state lifetime/ownership (B2) | Unresolved |
| Composition-root placement (B3) | Unresolved |
| `ContextStamp` implementation | Not yet changed |
| Minimum DIRECT runtime readiness | Not ready |

## Alternatives Considered

### F0A — out-of-observed-domain integer sentinel (not selected)

A reserved integer value categorically outside the non-negative observed-version domain (e.g., a
negative value). Conceptually valid — unlike an in-domain sentinel, it cannot collide with any
legitimate observed version, and is therefore compatible with ADR-0026's semantic requirement. Not
selected: it offers materially weaker type-level self-documentation than F2 (the field would remain
annotated simply as `int`, with the reserved value's special meaning living only in documentation),
creating avoidable invariant debt for comparable structural cost.

### F0B — in-observed-domain integer sentinel (rejected by accepted authority)

Zero or a reserved positive integer drawn from the legitimate observed-version domain. Rejected: zero
is explicitly and directly forbidden as a sole absence marker by ADR-0026
(`ZERO_AS_SOLE_UNMATERIALIZED_STATE_MARKER = NOT_PERMITTED`); a reserved positive value collides with
the currently-unrestricted positive-integer observed-version space for the same underlying reason.

### F1 — nullable version field (not selected)

`int | None`, with `None` narrowly meaning `UNMATERIALIZED` only. Conceptually valid and adequate.
Not selected: Python's generic `None` carries no domain-specific name and offers materially weaker
type-level self-documentation than F2's explicitly named marker, for comparable structural cost.

### F3 — dedicated version-state value object (not selected)

A small domain value object encapsulating `OBSERVED_VERSION(n) | UNMATERIALIZED` as its own concept.
Conceptually the strongest on illegal-state prevention and future extensibility, but not selected by
decision review: the current two-state domain does not justify the additional abstraction and
construction burden (every construction site would need to wrap plain integers), consistent with
AGENTS.md's guidance against introducing abstractions before a concrete use demonstrates they are
needed.

### F4 — orthogonal per-dimension materialization metadata (not selected)

Keep the existing `int` fields unchanged; add separate metadata identifying which dimensions are
unmaterialized. Conceptually capable of satisfying the distinguishability requirement in combination,
but not selected: it carries a genuine dual-source-of-truth risk (a version field and its paired flag
could disagree) and, more fundamentally, no individual version field remains self-sufficient to read
in isolation without also checking its paired metadata — a domain-contract weakness, not merely a
style preference.

### F5 — split version/dimension-state carrier (not selectable at current decomposition)

A carrier that separates "which dimensions have observed versions" from "which are unmaterialized"
without necessarily retaining the current five-named-field shape. Not selectable: its own definition
does not specify a concrete-enough information model to test against the adequacy criteria without
inventing fields, which was not done.

### F6 — partial or narrower ContextStamp (not selectable at current decomposition)

Varying the field set itself per instance, omitting fields for unmaterialized dimensions. Not
selectable for the same specification-insufficiency reason as F5, and additionally found to change
what `ContextStamp` fundamentally is (a fixed snapshot of five known dimensions) rather than merely
representing one field's value more precisely.

### S1 — materialize missing owners and keep an integer-only stamp (outside this decision)

Implementing Identity, Goal, and Policy state owners so that every dimension could use an ordinary
observed integer, avoiding the need for any new representation mechanism at all. ADR-0026 already
established that missing-owner implementation is not required by the distinguishability decision;
this remains a possible, independent future strategy, entirely outside the scope of this
representation decision.

## Non-Decisions / Deferred

- Concrete Python spelling of the `UNMATERIALIZED` marker (`Enum`, singleton, dedicated marker class,
  or any other mechanism).
- Any change to `ContextStamp`'s source code.
- Materialized-but-unobserved state semantics.
- Runtime cognitive-state lifetime and ownership for Workspace or Situation (B2).
- Composition-root code placement (B3).
- Identity, Goal, or Policy domain implementation.
- Whether or how a future accepted decision might change Workspace's or Situation's
  owner-materialization status.
- `ContextRequest`, `ContextPackage`, `ReasoningRequest`, or any other consumer contract.
- Runtime implementation of any kind.

## Consequences

**Positive:**

1. `ContextStamp` now has a complete, evidence-grounded information model capable of honestly
   representing every dimension's current owner-materialization status, satisfying ADR-0026's
   distinguishability requirement without collapsing it into any ordinary observed-version value.
2. The field-carrier scope (SCOPE-A) lets the type system itself, rather than runtime validation
   alone, prevent an already-known illegal combination (`workspace_version = UNMATERIALIZED`) from
   ever being representable.
3. Zero production code or test changes are required by this ADR alone; `ContextStamp`'s current
   shape and every existing fully-observed construction remain valid and unchanged in meaning.
4. Concrete implementation detail (marker spelling) is deliberately left open, preserving future
   design flexibility.
5. Identity's ownership boundary (`Agent != LLM`) is protected: no fabricated identity version is
   authorized by this decision.

**Tradeoff:**

1. `ContextStamp` cannot yet be legitimately constructed for `identity_version`, `goal_version`, or
   `policy_version` until a follow-up, non-architectural implementation step actually changes the
   dataclass — this ADR alone does not unblock construction.
2. Two further, independent runtime blockers (B2, B3) remain fully unresolved; minimal DIRECT runtime
   composition readiness is unaffected by this decision.
3. A future decision to change Workspace's or Situation's owner-materialization status would require
   its own separate architectural review under ADR-0005 governance, since SCOPE-A's asymmetry is
   presently encoded in the type itself.

## Relationship to Existing Architecture

This ADR complements ADR-0002 (agent independent from any LLM provider), ADR-0005 (COGNITION V1
frozen), and ADR-0026 (ContextStamp unmaterialized-state distinguishability). It does not supersede
any of them. ADR-0002 remains authoritative for the Agent-!=-LLM boundary this ADR's Identity
firewall protects. ADR-0005 remains authoritative for COGNITION V1's frozen structure;
`STRUCTURAL_CONTEXT_STAMP_CHANGE_REQUIRES_EXPLICIT_ARCHITECTURAL_DECISION = YES` is exactly why this
ADR exists, and this ADR is itself that required explicit architectural decision for the
representation mechanism — it does not itself modify `ContextStamp`'s frozen structure; a future,
purely implementation-level change applying this decision remains subject to the same governance.
ADR-0026 remains authoritative for the distinguishability requirement itself
(`CONTEXT_STAMP_UNMATERIALIZED_STATE_DISTINGUISHABILITY = REQUIRED`, `ZERO_AS_OBSERVED_VERSION =
VALID`, `ZERO_AS_SOLE_UNMATERIALIZED_STATE_MARKER = NOT_PERMITTED`); this ADR operationalizes that
requirement with a concrete information model and does not reopen or narrow it. This ADR does not
modify, narrow, or extend any ADR in the M0-15 Verification sequence (ADR-0015 through ADR-0025); it
addresses an unrelated gap in the Context Composition domain.
