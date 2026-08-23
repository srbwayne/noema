# ADR-0017: Verification Minimum Explicit Derivation-Context Axes

- Status: Accepted
- Date: 2026-08-23

## Context

ADR-0006 assigns Prediction / Counterfactual ownership of scenario-specific consequence
derivation, keeps Situation Model and World Model as separate ownership concerns, and leaves
World Model production blocked. ADR-0007 establishes that derivation occurs relative to a
baseline; that Prediction introduces zero explicit hypothetical divergences from that baseline;
that Counterfactual introduces one or more explicit hypothetical divergences; that baseline and
divergence references cross domain boundaries opaquely; and — critically — that Prediction having
zero explicit hypothetical divergence "does not mean prediction without context, prediction
without implicit assumptions, factual or verified prediction, or prediction with automatic
confidence." ADR-0007 also keeps reusable dynamics knowledge (a future World Model consumption
concern) conceptually separate from scenario input. ADR-0008 establishes that every derivation has
exactly one derivation target, a semantic focus distinct from both baseline and divergence.
ADR-0009 froze the concrete request contracts that expose these axes structurally:
`PredictionRequest` (`baseline_ref`, `target_ref`, `target_statement`) and `CounterfactualRequest`
(the same three fields plus `divergence_refs`).

ADR-0015 froze the minimum V1 Verification semantic axis — correctness/validity of derived
content, evaluated within the derivation context under which that content was produced — while
leaving concrete derivation-context representation deferred. ADR-0016 froze the first/minimum
Verification subject as one individual Prediction / Counterfactual consequence item, keeping
derivation context distinct from that subject and keeping `target_ref` outside the minimum subject.

M0-15AE through M0-15AG performed sequential, read-only discovery to narrow what "derivation
context" means for Verification without inventing structure. That discovery produced two findings
that required correction before being frozen: an initial claim that derivation context alone is
sufficient as the Verification judgment basis, and an initial claim that baseline plus explicit
divergences exhaustively compose the derivation context. Both claims were rejected on review,
because neither is supported by positive evidence — ADR-0007 itself explicitly denies that the
explicit axes exhaust context, and no ADR establishes that context alone suffices to determine
correctness/validity. This ADR records the corrected, narrower result of that discovery. It does
not extend it, and it does not create any production contract.

## Decision

### Minimum explicit derivation-context axes

The minimum **explicit** derivation-context axes currently established at the Prediction /
Counterfactual boundary are:

1. the baseline relative to which the derivation is made;
2. for Counterfactual only, the explicit hypothetical divergences assumed from that baseline.

Prediction introduces **zero** explicit hypothetical divergences. Counterfactual introduces **one
or more** explicit hypothetical divergences.

### Non-exhaustiveness

Baseline plus explicit divergences do **not** exhaustively define every assumption, context
element, knowledge source, or semantic resource that may participate in a derivation.
`DERIVATION_CONTEXT_NOT_EXHAUSTIVELY_DEFINED`. This ADR does not claim, and does not approve any
future reading that would claim, "the derivation context consists of baseline plus divergences"
without this qualifier. No closed-world semantics is implied by freezing these two explicit axes.

### Prediction qualification

Preserving ADR-0007 exactly: Prediction has no **explicit** hypothetical divergence at the
requesting boundary. This does not mean prediction without context, prediction without implicit
assumptions, factual prediction, verified prediction, or prediction with automatic confidence. It
means only that no explicit counterfactual divergence has been introduced by the requesting
boundary.

### Counterfactual qualification

Counterfactual explicitly assumes one or more hypothetical divergences from the baseline. Per
ADR-0007's authority, those divergences do not assert occurrence, do not update current belief,
are scenario input rather than result or effect, are not `SituationDelta`, and are not
automatically an `EpistemicClaim`.

### Implicit assumptions

Implicit assumptions are **not excluded** by this explicit-axis decision. Their identity, content,
ownership, relationship to derivation context, representation, transport, and materialization all
remain unresolved: `IMPLICIT_ASSUMPTIONS_POSSIBLE_RELATION_UNRESOLVED`. This ADR does not create
`implicit_assumptions`, `assumptions`, `premises`, or any equivalent field or contract.

### Target boundary

The derivation target remains a distinct semantic focus, answering "what is this derivation
about?" It is not one of the minimum explicit scenario/context premises frozen by this ADR. This
does not mean target is irrelevant to future Verification; its possible future role in semantic
scoping, correlation, transport, or a broader judgment context remains entirely deferred.

### Subject / context boundary

Preserving ADR-0016: the Verification subject is one individual Prediction / Counterfactual
consequence item; the context axes frozen here are semantic information relative to which that
subject was derived. This ADR does not combine subject and context into `VerificationSubject`,
`VerifiedConsequence`, `VerificationContext`, `VerificationInput`, or any wrapper.

### Judgment basis — critical boundary

This ADR distinguishes explicitly between:

- "correctness/validity is evaluated within the derivation context" (approved, per ADR-0015);
- "the derivation context alone is sufficient to establish correctness/validity" (not approved).

Only the first is frozen. `JUDGMENT_BASIS_STATUS = ADDITIONAL_BASIS_REMAINS_UNRESOLVED`: no
additional basis is currently required by an authoritative ADR; no positive evidence proves
context-alone sufficiency; future correctness/evidence/knowledge consumption remains open. This ADR
does not approve `CONTEXT_SUFFICIENT_AS_MINIMUM_SEMANTIC_BASIS`, and it does not approve
`ADDITIONAL_BASIS_REQUIRED`.

### World Model / dynamics boundary

World Model reusable dynamics knowledge is conceptually distinct from the explicit scenario input
frozen here. A future derivation may consume dynamics knowledge through a separately approved
boundary, per ADR-0007's own conceptual flow. This ADR does not make World Model a Verification
requirement. World Model production remains **BLOCKED** by ADR-0006. This ADR does not freeze
`world_model_ref`, `dynamics_ref`, `rule_ref`, or any condition/effect representation.

### Epistemic / evidence boundary

Epistemic ownership of status, provenance, supporting evidence, counter evidence, and conflict
semantics remains intact. This ADR does not approve the Epistemic Model as a required Verification
basis, and it does not prohibit future, separately approved consumption. Evidence representation
remains **DEFERRED**.

### Result-only information boundary

`PredictionCounterfactualResult` contains `target_ref`, `status`, and `consequences`. It does not
preserve baseline, divergences, or a Prediction-vs-Counterfactual discriminator. Consequently, the
current Prediction / Counterfactual result alone does not retain the minimum explicit
derivation-context axes needed to reconstruct that explicit context. This is an
information-sufficiency observation about the existing result shape; it is not converted into a
structural decision about a future Verification request.

### Opaque-reference boundary

The current Prediction / Counterfactual request contracts use `baseline_ref` and `divergence_refs`
as opaque references. This ADR does not freeze those exact fields for Verification. It does not
approve `baseline_ref`, `divergence_refs`, `scenario_ref`, `context_ref`, `evidence_ref`,
`target_ref`, `request_ref`, or `result_ref` on any future Verification contract. Reference
representation remains **DEFERRED**.

### Materialization

This ADR does not create or approve `ContextResolver`, `ScenarioResolver`, `BaselineResolver`,
`DivergenceResolver`, or any `Materializer`. How opaque references would be resolved, or how
semantic context would be materialized, remains **DEFERRED**.

### Correctness / validity

Preserving ADR-0015: correctness/validity remains one `UNDIFFERENTIATED_SEMANTIC_AXIS`. This ADR
does not define separate correctness and validity modes, and it does not define entailment,
consistency, formal proof, deduction, theorem proving, or constraint solving as Verification
semantics.

### Actuality boundary

Preserving ADR-0015: retrospective actuality correspondence is not minimum shared Verification
semantics. This ADR does not reintroduce observed outcome, ground truth, or "did it happen?" as
required shared context or basis.

### Evaluation / Confidence boundaries

Evaluation concerns a utility/value judgment against normative content; Verification concerns
correctness/validity; confidence is not correctness/validity. This ADR does not introduce
`normative_statement`, a utility judgment, a confidence threshold, or model confidence into the
context decision.

### Provider independence

This decision remains independent of any LLM, `ModelRouter`, provider, prompt, temperature, tool
calling, JSON schema, or model confidence.

### Request cardinality

Remains **DEFERRED**. This ADR does not decide one subject per Verification request, many
subjects, batch transport, tuple/list shape, or one operation per subject.

### Operation cardinality

Remains **DEFERRED**. This ADR does not infer one Verification operation per consequence.

### Correlation

Remains **DEFERRED**. This ADR does not approve consequence text alone, `target_ref` + consequence,
`baseline_ref` + consequence, scenario + consequence, or any request/result/subject/verification
identifier as a correlation mechanism.

### Output

Remains **DEFERRED**. This ADR does not approve `bool`, pass/fail, valid/invalid,
verified/unverified, a textual judgment, a score, a confidence value, or `VerificationStatus`.

### Non-success

Remains **DEFERRED**. This ADR does not approve `UNKNOWN`, `UNVERIFIED`, `NOT_VERIFIABLE`,
`INSUFFICIENT_EVIDENCE`, `INDETERMINATE`, or `UNRESOLVED` as Verification contract vocabulary.

### Structural contracts

Not approved: `VerificationRequest`, `VerificationResult`, `VerificationStatus`,
`VerificationSubject`, `VerificationContext`, `VerificationBasis`, `VerificationReference`.
Structural contract discovery remains **BLOCKED**.

### Execution

Not approved: `VerificationExecutor`, `VerificationPort`, a `VerificationEngine` implementation,
`VerificationService`, `VerificationPolicy`, `VerificationAdapter`, `VerificationExecutionError`.
Verification execution remains **BLOCKED**. Prediction / Counterfactual execution Gate 4 remains
**PARKED/BLOCKED**.

### Prediction / Counterfactual contract preservation

`PredictionRequest` remains unchanged. `CounterfactualRequest` remains unchanged.
`PredictionCounterfactualResult` remains unchanged. No field, identity, or wrapper is added to any
of them by this ADR.

### Decision summary

| Concern | Decision |
| --- | --- |
| Minimum explicit context axis — Prediction | Baseline |
| Explicit hypothetical divergences — Prediction | None |
| Minimum explicit context axes — Counterfactual | Baseline + one-or-more explicit hypothetical divergences |
| Exhaustively defines all derivation context | No |
| Implicit assumptions | Possible; exact relation unresolved |
| Derivation target part of explicit scenario premises | No |
| Target future Verification role | Deferred |
| Result alone retains explicit derivation context | No |
| Reference representation | Deferred |
| Materialization | Deferred |
| Additional judgment basis | Unresolved |
| Request cardinality | Deferred |
| Operation cardinality | Deferred |
| Correlation | Deferred |
| Output | Deferred |
| Non-success | Deferred |
| Structural contracts | Blocked |
| Execution | Blocked |

## Not Decided Here

- complete/exhaustive derivation-context composition
- implicit assumption identity/content
- implicit assumption ownership
- implicit assumption representation
- implicit assumption transport
- target future Verification role
- additional judgment basis
- evidence representation
- dynamics/knowledge consumption
- reference representation
- materialization/resolution
- request cardinality
- operation cardinality
- correlation
- request structure
- result structure
- status vocabulary
- output
- non-success
- occurrence identity
- consequence identity
- future Verification subject categories
- execution topology
- concrete consumer
- persistence
- API/serialization

## Consequences

**Positive:**

1. Context semantics is narrowed to what is already explicitly established, without claiming
   exhaustiveness.
2. Prediction/Counterfactual uniformity is preserved — both share the same baseline-plus-divergence
   axis structure, differing only in divergence cardinality.
3. Current Prediction / Counterfactual semantics (ADR-0007/0008/0009) are reused rather than
   reinterpreted.
4. The derivation target remains distinct from context, avoiding premature conflation.
5. Future basis, evidence, and knowledge-consumption design remains entirely open.
6. No speculative structure is introduced.

**Tradeoff:**

1. The full derivation context is still not defined.
2. Implicit assumptions remain unresolved in identity, ownership, and representation.
3. Additional judgment basis remains unresolved — Verification cannot yet be exercised end to end.
4. Structural contracts remain blocked.
5. Execution remains blocked.
6. The current Prediction / Counterfactual result does not preserve the explicit derivation-context
   axes, so a future Verification design consuming only the result would need additional
   information from elsewhere.

## ADR Relationship

ADR-0017 complements ADR-0015 and ADR-0016. ADR-0015 remains authoritative for the minimum
Verification semantic axis, the semantic relevance of derivation context, the actuality boundary,
and the content-vs-process boundary. ADR-0016 remains authoritative for the minimum Verification
subject, the subject/context separation, `target_ref` not being part of the subject, and the
structural deferrals established there. ADR-0007 remains authoritative for baseline semantics,
Prediction's zero explicit divergence, Counterfactual's one-or-more explicit divergences, the
implicit-assumption qualification, and hypothetical-divergence boundaries. ADR-0008 remains
authoritative for derivation-target semantics. ADR-0009 remains authoritative for the current
Prediction / Counterfactual request structure. ADR-0017 supersedes none of them.
