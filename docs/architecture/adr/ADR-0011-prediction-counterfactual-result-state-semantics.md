# ADR-0011: Prediction and Counterfactual Result State Semantics

- Status: Accepted
- Date: 2026-08-18

## Context

ADR-0010 froze the shared Prediction / Counterfactual result semantics up to the boundary of
item 2 of the Prediction / Counterfactual Implementation Gate: one shared result contract;
`target_ref` as the minimal correlation information; textual consequence statements with no
consequence identity; successful/non-empty cardinality of one-or-more; non-exhaustiveness of
returned consequences; and no ordering or relationship semantics among them. ADR-0010 explicitly
deferred the concrete consequence container, the meaning of an empty result, insufficient-
knowledge semantics, and result status to item 3 of the gate.

M0-13N (Empty Result / Insufficient Knowledge Semantics Discovery) resolved, by read-only audit,
the semantic distinction between a derivation that produces one or more consequences, a
derivation that cannot sustain any consequence given available knowledge, an affirmative
conclusion of no relevant effect, and a technical execution failure. It found the result's
semantic space to be binary, and identified exactly one open representation question: whether
that binary distinction requires an explicit state field or can be inferred solely from
consequence cardinality.

M0-13O (Explicit Result State vs. Cardinality-Only Decision) resolved that remaining question: an
explicit semantic-state representation is required, exactly two conceptual states are sufficient,
and the concrete consequence container becomes safely resolvable once that representation
decision is made.

This ADR records the consolidated result of M0-13N and M0-13O.

## Decision

### Two semantic states

The shared Prediction / Counterfactual result recognizes exactly two conceptual semantic states:

1. **Derived**
2. **Insufficient Knowledge**

No third semantic result state is approved. These are conceptual labels for this ADR's purpose;
they are not yet declared as final Python identifiers (see "Spelling deferred" below).

### Derived semantics

Derived means the available knowledge was sufficient to sustain one or more consequence
statements about the derivation target.

Conceptual invariant: Derived → one-or-more consequences.

Derived does not mean exhaustive, complete, verified, certain, or high-confidence. It carries no
claim beyond "at least one consequence statement was sustained."

### Insufficient Knowledge semantics

Insufficient Knowledge means:

- the request is valid;
- the derivation target is valid;
- the derivation is semantically executable;
- the available knowledge is insufficient to sustain any consequence statement.

Conceptual invariant: Insufficient Knowledge → zero consequences.

This is a legitimate semantic outcome of a valid derivation attempt. It is not an exception.

### Explicit state is required

The shared result carries an explicit representation of its semantic state. Semantic state is
not inferred solely from `bool(consequences)`.

Rationale: an empty consequence collection is a structural fact. "Available knowledge was
insufficient" is domain meaning that the contract assigns to that fact — it does not follow from
the fact by itself. That meaning must be named explicitly in the result rather than left as a
convention the consumer must already know.

### Intentional redundancy

The semantic state is logically bijective with consequence cardinality: Derived always
corresponds to one-or-more consequences, and Insufficient Knowledge always corresponds to zero.
This is acknowledged honestly as structural redundancy — the state field does not add new
structural information beyond what cardinality alone already carries.

This redundancy is accepted, not rejected, because:

- it makes domain semantics explicit and directly readable from the result;
- it is protected by a consistency invariant, so the redundant field cannot structurally diverge
  from the cardinality it mirrors;
- it follows existing Cognition domain precedents that make the same choice.

State is not claimed to add structural information; it adds explicit domain vocabulary.

### Precedents

`EpistemicClaim.status` keeps `EpistemicStatus.CONFLICTED` explicit even though it is
structurally bijective with the presence of `conflicting_claim_ids` — the domain
cross-validates the two rather than dropping the explicit status in favor of inferring it from
the tuple's emptiness.

`ReasoningOutcome` keeps an explicit `ReasoningStatus` alongside a payload-consistency matrix
(`conclusion` presence and `information_needs` presence), rather than inferring status purely
from payload shape.

`Plan.steps` is **not** a precedent for semantic-empty cardinality. `Plan` explicitly documents
that an empty `steps` collection carries no semantic meaning beyond "no steps" — it does not
itself represent success, failure, or an unresolved goal. This is the opposite situation from
Insufficient Knowledge, which is a genuine domain conclusion, not an absence of meaning.

### State / cardinality matrix

| State                     | Consequences | Validity |
| -------------------------- | ------------- | --------- |
| Derived                    | `>= 1`         | ✅ valid   |
| Derived                    | `0`            | ❌ invalid |
| Insufficient Knowledge     | `0`            | ✅ valid   |
| Insufficient Knowledge     | `>= 1`         | ❌ invalid |

No other combination exists.

### No-effect

A derivation that has sufficient knowledge to conclude the absence of a relevant effect returns a
textual consequence statement expressing that absence.

Therefore: no-effect → Derived → one-or-more consequences. No-effect is never represented by an
empty consequence collection.

### No separate NO_EFFECT state

A separate `NO_EFFECT` state is not created, because the information already belongs to the
consequence statement itself. A dedicated status would duplicate what the statement already
expresses.

### Technical failure boundary

Technical execution failure is not Insufficient Knowledge. Future examples include: an
unavailable provider, an I/O failure, a timeout, a malformed executor response, or an
adapter/runtime failure. Technical failure does not produce a legitimate semantic result; it
belongs to a future execution boundary (Gate 4). This ADR does not create an error contract for
it.

### Invalid request boundary

`InvalidPredictionRequestError` and `InvalidCounterfactualRequestError` represent structurally or
semantically invalid requests. Insufficient Knowledge only occurs after a request has already
been validated. Request-validation errors are not reused to represent Insufficient Knowledge.

### Epistemic UNKNOWN boundary

Insufficient Knowledge is not `EpistemicStatus.UNKNOWN`. A Prediction / Counterfactual result is
not an `EpistemicClaim`. No automatic translation between the two is approved.

### No PARTIAL

`PARTIAL` is not created. ADR-0010 already froze non-exhaustiveness: a returned consequence set
never claims to be the complete set of possible consequences, in any state. A valid consequence
does not become "partial" merely because other consequences might also exist.

### No generic UNRESOLVED

A generic `UNRESOLVED` semantic state is not created. There is no evidence for a third state in
which the request is valid, knowledge is sufficient, and consequences are still zero for some
distinct semantic reason.

### IMPOSSIBLE remains deferred

"Scenario impossible" remains deferred. No `IMPOSSIBLE` status is created. Its future ownership
(Verification, World Model, scenario validation, or a future coordination boundary) is not
resolved here.

### No information-needs payload

`information_needs`, `missing_information`, `missing_refs`, and `questions` are not added.
Insufficient Knowledge states only that available knowledge is insufficient; it does not describe
what is missing. No approved consumer requires that description.

### No reason summary

`reason`, `reason_summary`, and `explanation` are not added to the minimal result.

### Result state ownership

The semantic state belongs to the Prediction / Counterfactual domain component. It does not
belong to Reasoning, Epistemology, Evaluation, or Verification.

### Spelling deferred — critical

This ADR freezes:

- the concept of an explicit semantic state;
- exactly two state meanings (Derived, Insufficient Knowledge).

This ADR does **not** freeze:

- the Python enum class name;
- the field name (`state` vs. `status` vs. any other spelling);
- the exact member spelling;
- the concrete shared-result class name.

The words "Derived" and "Insufficient Knowledge" appear in this ADR only as conceptual labels,
not as approved code identifiers.

### Consequence container

The future minimal consequence collection uses `tuple[str, ...]`.

Rationale:

- immutable representation, consistent with the frozen Cognition dataclasses;
- direct precedent from `CounterfactualRequest.divergence_refs`;
- direct precedent from `ReasoningOutcome.information_needs`;
- can represent both zero cardinality (Insufficient Knowledge) and one-or-more cardinality
  (Derived) without a second concrete type.

### Tuple order nuance

A tuple preserves producer-provided order as representation. Tuple position does not imply rank,
priority, importance, causal precedence, temporal precedence, or relationship. This ADR does not
assert permutation equivalence. Structural equality may naturally remain order-sensitive.

### Duplicates

Exact textual duplicate consequence statements are invalid representation duplicates. For
example, `("latency increases", "latency increases")` is invalid.

`("latency increases", " latency increases ")` is not automatically treated as a duplicate via
normalization, because the original string values are preserved exactly with no trim mutation.

Semantic equivalence and paraphrase equivalence are not detected.

### String semantics

Each future consequence item is: a `str`; non-empty after a strip validation; the exact original
value preserved; no normalization; no coercion. This follows the existing request contracts. No
semantic parser is introduced.

### target_ref in both states

`target_ref` is present in both semantic states:

- Derived: `target_ref` + one-or-more consequences.
- Insufficient Knowledge: `target_ref` + zero consequences.

It remains an opaque semantic correlation anchor in both cases.

### One shared result preserved

ADR-0010's "one shared result type" direction is preserved. No semantic result variants
(`DerivedResult`, `InsufficientKnowledgeResult`) are created. The explicit semantic state lives
inside the single future shared result contract.

### Empty collection meaning

With an explicit semantic state, an empty consequence collection is structurally permitted only
when the semantic state is Insufficient Knowledge. Empty does not mean no-effect, technical
failure, invalid request, Epistemic UNKNOWN, or impossible scenario.

### Non-empty collection meaning

A non-empty consequence collection is permitted only when the semantic state is Derived. This
does not mean exhaustiveness, completeness, confidence, or verification.

### No Optional sentinel

`None`, `Optional`, or an absent consequences field are not used as an Insufficient Knowledge
sentinel. The collection exists in both states.

### Insufficient Knowledge is not an exception

Insufficient Knowledge is legitimate result semantics, not an exception. Technical failure
remains a future exception-boundary concern, separate from this semantic state.

### Result validation error deferred

A future implementation will need a `DomainError` for invalid structural combinations (for
example, an invalid state/cardinality pairing), but its concrete name is deferred to the
structural contract step.

### Result class name deferred

The concrete shared-result class name remains deferred. This ADR does not choose
`PredictionResult`, `CounterfactualResult`, `PredictionCounterfactualResult`, `DerivationResult`,
or `DerivationOutcome` by aesthetic preference.

### Probability / confidence preserved

ADR-0010's exclusion of probability, likelihood, and confidence from the minimal result is
preserved and not reopened.

### Evaluation / verification preserved

Utility, rank, priority, score, `verified`, and `verification_status` are not included, preserving
future Evaluation Engine and Verification Engine ownership.

### World Model exclusion

`WorldModel`, `DynamicsRule`, `TransitionRule`, `CausalRule`, mechanism, and causal path are not
included. World Model production remains blocked by ADR-0006.

### Item 3 gate

Prediction / Counterfactual Implementation Gate item 3 — empty-result and insufficient-knowledge
semantics — is **RESOLVED** by this ADR. Its constituent decisions: exactly two semantic states;
explicit semantic state required; Derived ↔ one-or-more consequences; Insufficient Knowledge ↔
zero consequences; no-effect belongs to Derived; technical failure remains outside the result;
`tuple[str, ...]` consequence container; exact textual duplicate rejection; no `PARTIAL`; no
generic `UNRESOLVED`; no `NO_EFFECT` status.

### Remaining implementation gaps

Although Gate 3 is semantically closed, the following remain not yet frozen for code — structural
and naming decisions, not a reopening of Gate 3:

- concrete shared-result class name;
- concrete semantic-state type name;
- field spelling (`state` vs. `status`);
- enum/member spelling;
- result-validation `DomainError` name.

### Remaining gates

Item 4 — execution-port requirement — remains **NOT RESOLVED**. This ADR does not decide it.

### World Model gate

World Model production remains blocked by ADR-0006. This ADR does not create a dynamics
representation.

## Not Decided Here

- concrete result class name
- semantic-state enum/type name
- state field spelling
- enum member spelling
- result validation error spelling
- execution port
- application boundary
- provider/model adapter
- probability semantics
- temporal semantics
- scenario-impossible ownership
- information-needs payload
- persistence
- runtime tracing identity
- World Model representation

## Consequences

**Positive:**

- An empty result can no longer silently mean no-effect.
- Insufficient knowledge becomes explicit domain language rather than an implicit convention.
- Technical failures remain outside the semantic result.
- The single shared result direction from ADR-0010 is preserved.
- Result invariants are machine-checkable, following existing Cognition precedents.
- Tuple representation remains provider-independent.
- Exact duplicate consequence statements can be rejected structurally.
- Non-exhaustiveness from ADR-0010 remains fully preserved.

**Tradeoff:**

- The semantic state is structurally redundant with consequence cardinality.
- Invalid state/cardinality combinations must be explicitly rejected by a future invariant.
- A small structural naming decision still remains before implementation.
- No information-needs explanation is carried for Insufficient Knowledge.
- No execution boundary exists yet for technical failure.

## ADR Relationship

ADR-0011 complements ADR-0005, ADR-0006, ADR-0007, ADR-0008, ADR-0009, and ADR-0010. It
supersedes none of them.
