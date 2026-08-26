# ADR-0018: Verification Partial Explicit Derivation-Context Correlation Semantics

- Status: Accepted
- Date: 2026-08-25

## Context

ADR-0015 froze the minimum V1 Verification semantic axis: correctness/validity of derived
content, evaluated within the derivation context under which that content was produced. ADR-0016
froze the first/minimum Verification subject as one individual Prediction / Counterfactual
consequence item, keeping derivation context distinct from that subject. ADR-0017 froze the
minimum explicit derivation-context axes — baseline, plus explicit hypothetical divergences for
Counterfactual — while explicitly establishing that these axes do not exhaustively define
derivation context, that implicit assumptions are not excluded and their relationship to context
is unresolved, and that correlation representation and reference representation both remain
deferred.

A sequence of read-only architectural discoveries (M0-15BI through M0-15BR) investigated exactly
what ADR-0017 left deferred: what semantic association a Verification judgment must preserve to
remain "within" its derivation context, what representation strategies are architecturally
possible for that association, and whether any such strategy could responsibly be decided while
concrete context membership remains open. That sequence established, without introducing
speculative structure: that the completeness principle governing derivation-context association
is itself already an implication of ADR-0015 and required no new semantic content; that concrete
context membership beyond the known explicit axes remains genuinely open; that a representation
strategy explicitly scoped to the known explicit axes only — never claiming completeness — is not
blocked by that open membership; and that reusing the opaque-reference pattern ADR-0007 already
established for baseline and explicit hypothetical divergences, specifically for Verification, is
a new but minimally novel, strongly precedented, and reversible decision. M0-15BR reviewed and
approved exactly that decision. This ADR records the result of that approval. It does not reopen
the discovery, and it does not create any production contract.

## Decision

### Decision scope

This ADR decides one thing only: for Verification's currently established minimum **explicit**
derivation-context axes, structural correlation semantics preserves the individual consequence
semantic value, the association to the derivation baseline by opaque reference, and the
association to explicit hypothetical divergences by opaque references when such divergences
exist.

Prediction has zero explicit hypothetical divergences. Counterfactual has one-or-more explicit
hypothetical divergences.

This is a **partial** explicit-axis correlation decision only. It does not represent, and does not
claim to represent, the complete derivation context.

### Reused upstream semantics

The following are already frozen by prior ADRs and are not reopened, redefined, or reconfirmed as
new content here:

- the individual textual consequence statement as the minimum Verification subject (ADR-0016);
- baseline semantics as the reference point of a Prediction / Counterfactual derivation (ADR-0007);
- hypothetical divergence semantics — an explicitly assumed difference from the baseline (ADR-0007);
- Prediction's zero explicit hypothetical divergences and Counterfactual's one-or-more explicit
  hypothetical divergences (ADR-0007, ADR-0017);
- the opaque-reference pattern by which baseline and divergence cross the Prediction /
  Counterfactual requesting boundary (ADR-0007);
- the non-exhaustiveness of baseline plus explicit divergences as derivation-context composition
  (ADR-0017).

This ADR treats every item above as settled precedent. It does not restate them as new decisions.

### Verification-specific opaque-reference reuse

The only genuinely new content of this ADR is narrow: that Verification, specifically, preserves
its association to the known explicit context axes using the same opaque-reference semantics
already established for baseline and explicit hypothetical divergences at the Prediction /
Counterfactual boundary.

ADR-0007's opaque-reference rule was decided to close the Prediction / Counterfactual
Implementation Gate. Its wording is general, but its binding decision scope is that boundary. It
did not, by itself, already decide reference representation for a future Verification boundary;
ADR-0015 and ADR-0017 both left Verification's correlation and reference representation
explicitly deferred. This ADR makes that bounded, Verification-specific reuse explicit. It is
justified by strong, direct precedent — the same opacity rationale ADR-0007 and ADR-0008 already
established ("must not require dereferencing by the domain itself") applies without modification
to Verification's situation as a new consumer of the same concepts — and by minimum novelty: it
reuses existing semantic reference values and an existing, repeatedly-used cross-boundary
opacity pattern, introducing no new abstraction, identity, resolver, or coupling.

### Subject-value boundary

The individual consequence semantic value is not a new decision of this ADR. It remains exactly
the textual consequence statement ADR-0010 and ADR-0016 already established. This ADR does not
rename it, wrap it, or give it a reference of its own.

### Baseline association

The baseline association for this partial explicit-axis Verification correlation decision is
opaque-reference based, consistent with ADR-0007. This ADR does not create `baseline_ref` as a
Verification field, `BaselineRef`, `ScenarioRef`, `ContextRef`, a `UUID`, a `TSID`, or a `str`
requirement. Field naming, concrete type, and validation rules remain entirely deferred to a
future, separate structural contract decision.

### Explicit divergence association

The explicit hypothetical-divergence association, when such divergences exist, is likewise
opaque-reference based, consistent with ADR-0007. Prediction's derivation carries zero explicit
divergence associations; Counterfactual's derivation carries one-or-more. This ADR does not decide
a container (`tuple`, `list`, `frozenset`), ordering, duplicate semantics, normalization, or field
names for any future Verification representation of this association.

### Prediction / Counterfactual precision

This ADR describes the upstream derivation semantics only: Prediction derives with zero explicit
hypothetical divergences; Counterfactual derives with one-or-more. It does **not** infer, from
that cardinality difference, a Verification request type split, a Verification mode
discriminator, an origin enum, a `mode` field, separate Verification engines, or separate
Verification operations. Verification request and operation topology remain entirely deferred, as
they were before this ADR.

### Partial / non-exhaustive boundary

This ADR is explicitly **not** the complete Verification correlation representation. It freezes
only the currently established minimum explicit derivation-context axes. The following remain
true and are not altered by this ADR:

- `CONCRETE_CONTEXT_MEMBERSHIP_REMAINS_PARTIALLY_UNRESOLVED`;
- `EXPLICIT_AXES_NOT_PROVEN_CORRELATION_COMPLETE`;
- `IMPLICIT_ASSUMPTION_CORRELATION_ROLE_REMAINS_UNRESOLVED`.

No closed-world context semantics is implied. Baseline and explicit divergences are not asserted
to be everything a Verification judgment could ever need to remain associated with.

### Context-completeness boundary

ADR-0015's principle is preserved without modification: a Verification judgment remains
semantically scoped to every derivation-context distinction material to interpreting the
correctness/validity of its subject. This ADR does not redefine, narrow, or supersede that
principle. It decides only the carrier semantics for the subset of that principle's membership
that is currently known and explicit — baseline and explicit hypothetical divergences. Any
additional member of that principle's scope, if and when identified, remains a separate, future
concern.

### Ownership

Referencing baseline and explicit hypothetical divergences does not transfer their ownership to
Verification. Ownership of baseline and hypothetical-divergence semantics remains exactly where
ADR-0007 places it: the Prediction / Counterfactual boundary. This ADR does not change any
existing component ownership. It does not give Verification ownership of `SituationModel`, of
World Model dynamics knowledge, or of any Prediction / Counterfactual concept referenced.

### Materialization

Materialization remains entirely deferred. An opaque association does not imply local
availability of baseline or divergence content, an ability to dereference either, or any of
`ContextResolver`, `ScenarioResolver`, `BaselineResolver`, `DivergenceResolver`, or `Materializer`.
No resolver of any kind is approved by this ADR.

### Judgment-basis boundary

`ADDITIONAL_BASIS_REMAINS_UNRESOLVED`, exactly as ADR-0017 left it. This ADR does not assert that
context association is sufficient to perform a correctness/validity judgment. Correlation —
preserving *what* a judgment concerns — is not the same question as judgment basis — *what
sustains* the determination of correctness/validity. This ADR answers only the former, for the
known explicit axes.

### Implicit-assumption boundary

This ADR makes no decision concerning implicit assumptions. Their identity, content, ownership,
membership in derivation context, representation, transport, and materialization all remain
exactly as unresolved as ADR-0017 left them. This ADR does not create `implicit_assumptions`,
`assumptions`, `premises`, `implicit_context`, or `implicit_context_ref`.

### Target boundary

`TARGET_ASSOCIATION_REMAINS_UNRESOLVED`. This ADR does not approve `target_ref`, `target_statement`,
or any target association for Verification. The derivation target remains outside this ADR's
explicit-axis carrier decision entirely — it is neither included nor excluded from a future
correlation mechanism by virtue of this ADR. This does not prohibit target from being found
relevant to Verification in the future, under its own, separate decision.

### Provenance / authenticity boundary

This ADR does not require provenance or correspondence validation before an asserted association
between a consequence, a baseline, and explicit divergences may be carried. This mirrors existing,
uniform repository practice: every existing opaque reference in this domain (`baseline_ref`,
`target_ref`, `problem_ref`, `goal_ref`) is accepted as caller-asserted, with only type and
non-emptiness validation, never cross-boundary existence or correspondence validation (ADR-0009,
ADR-0013). This ADR does not, however, establish a universal "trust the caller" architectural
rule; it records only that the absence of a provenance mechanism does not block representing the
association itself.

`PROVENANCE_VALIDATION_NOT_CURRENTLY_SUPPORTED` and `PROVENANCE_MECHANISM_REMAINS_UNRESOLVED`. This
ADR does not claim that occurrence identity is necessarily the mechanism a future provenance
decision would use; it commits to no such mechanism.

### Identity / occurrence boundary

`OCCURRENCE_DISTINCTION_NEED_REMAINS_UNRESOLVED`. Identity is **not approved** by this ADR. This
ADR does not create `consequence_id`, `subject_id`, `context_id`, `verification_id`,
`occurrence_id`, `request_id`, or `result_id`.

### Concrete representation deferred

All concrete structure remains deferred: field names, field types, dataclass shape, any wrapper,
container type, optionality, collection topology, serialization, and API/network representation.
This ADR does not sketch or imply a hypothetical `VerificationRequest` shape.

### Request cardinality

`REQUEST_SUBJECT_CARDINALITY_REMAINS_DEFERRED`. This ADR does not infer one subject per request,
many subjects, or any batch/tuple/collection shape.

### Operation cardinality

`OPERATION_JUDGMENT_CARDINALITY_REMAINS_DEFERRED`. This ADR does not infer one Verification
operation per consequence.

### Result cardinality

`RESULT_ENVELOPE_CARDINALITY_REMAINS_DEFERRED`. This ADR does not infer any result envelope
shape.

### Complete correlation representation

`COMPLETE_CORRELATION_REPRESENTATION_REMAINS_UNREADY`. The partial semantics recorded here must
not be read, now or later, as the complete Verification correlation mechanism. Concrete context
membership beyond the known explicit axes remains open, and no aggregate or extensible mechanism
capable of covering that open membership is approved by this ADR.

### Output

Output representation remains deferred. This ADR does not approve `bool`, pass/fail,
valid/invalid, verified/unverified, a score, a textual judgment, or `VerificationStatus`.

### Non-success

Non-success semantics remain deferred. This ADR introduces no status vocabulary for Verification.

### Structural contracts

Structural contracts remain explicitly **BLOCKED**. This ADR does not approve `VerificationRequest`,
`VerificationResult`, `VerificationStatus`, `VerificationSubject`, `VerificationContext`,
`VerificationReference`, or `VerificationBasis`. This ADR does not unblock structural contract
discovery; it narrows one of the dimensions ADR-0015 identified as a prerequisite to it, without
itself completing that prerequisite set.

### Execution

Verification execution remains **BLOCKED**. This ADR does not approve `VerificationExecutor`,
`VerificationPort`, a `VerificationEngine` implementation, `VerificationService`,
`VerificationPolicy`, `VerificationAdapter`, or `VerificationExecutionError`. Prediction /
Counterfactual Implementation Gate item 4 (execution port) remains **PARKED/BLOCKED**. World Model
production remains **BLOCKED** by ADR-0006.

### Existing-contract preservation

No change is implied for `PredictionRequest`, `CounterfactualRequest`,
`PredictionCounterfactualResult`, `EvaluationRequest`, or `EvaluationResult`. No field, wrapper,
discriminator, or back-reference is added to any of them by this ADR.

### Provider independence

This decision is independent of any LLM, `ModelRouter`, provider, prompt, tooling, temperature,
JSON schema, or model confidence, consistent with ADR-0002.

### Decision summary

| Concern | Decision |
| --- | --- |
| Verification minimum subject value | Existing textual consequence semantics preserved |
| Baseline association | Opaque-reference semantics approved for the partial explicit-axis Verification correlation decision |
| Explicit divergence association | Opaque-reference semantics approved when explicit divergences exist |
| Prediction explicit divergence | None |
| Counterfactual explicit divergence | One-or-more |
| Complete derivation-context representation | Not approved / unready |
| Concrete context membership | Partially unresolved |
| Implicit assumptions | Unresolved |
| Target association | Unresolved |
| Concrete reference type | Deferred |
| Materialization | Deferred |
| Provenance mechanism | Unresolved |
| Request cardinality | Deferred |
| Operation cardinality | Deferred |
| Result cardinality | Deferred |
| Output | Deferred |
| Non-success | Deferred |
| Structural contracts | Blocked |
| Execution | Blocked |

## Not Decided Here

- complete derivation-context composition
- additional concrete context members beyond baseline and explicit divergences
- implicit assumption identity, content, ownership, and membership
- implicit assumption representation and transport
- target's future Verification role
- occurrence identity
- consequence identity
- provenance mechanism
- correspondence validation
- concrete baseline reference type
- concrete divergence reference type
- field names
- collection/container shape
- materialization / resolution
- request cardinality
- operation cardinality
- result cardinality
- complete correlation representation
- Verification request structure
- Verification result structure
- output representation
- status vocabulary
- non-success semantics
- judgment basis
- execution topology
- concrete consumer
- persistence
- API / serialization

## Consequences

**Positive:**

- Verification now has an approved structural semantic mechanism for its currently known explicit
  context axes, rather than an unresolved reference-representation gap.
- The decision reuses established opaque-reference semantics instead of inventing a new context
  identity, aggregate, or resolver.
- Prediction / Counterfactual ownership boundaries are preserved unchanged.
- The decision remains compatible with open future context membership; nothing here forecloses a
  future mechanism covering additional material context distinctions.
- No premature contract, field, type, or container decision is made.

**Tradeoff:**

- Complete correlation representation remains unresolved; this ADR does not make Verification
  correlation semantics whole.
- Implicit-assumption membership remains unresolved.
- A future, richer context-transport mechanism, if introduced, may need to address duplication or
  consistency against the association recorded here — that design question is not solved by this
  ADR.
- Materialization of baseline/divergence content, if ever needed for judgment basis, remains
  unresolved.
- No executable Verification capability exists as a result of this ADR.
- Structural contracts and execution remain entirely blocked.

## ADR Relationship

ADR-0018 complements ADR-0015, ADR-0016, and ADR-0017. ADR-0015 remains authoritative for
correctness/validity evaluated within derivation context. ADR-0016 remains authoritative for the
minimum individual consequence subject. ADR-0017 remains authoritative for the minimum explicit
context axes, their non-exhaustiveness, the implicit-assumption deferral, the target boundary, and
the judgment-basis boundary. ADR-0007 remains authoritative for baseline and hypothetical
divergence semantics and their established Prediction / Counterfactual opaque-reference pattern.
ADR-0009 remains authoritative for the existing concrete Prediction / Counterfactual request
structure.

ADR-0018 resolves only a narrow subset of the Verification correlation and reference-representation
space ADR-0017 left deferred: the partial structural semantic representation of the currently
known explicit context-axis association. ADR-0018 does not supersede ADR-0017, and it supersedes
none of the ADRs listed above.
