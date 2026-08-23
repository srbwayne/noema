# ADR-0015: Verification Foundation Semantics

- Status: Accepted
- Date: 2026-08-22

## Context

ADR-0005 freezes `Verification Engine` as a component of COGNITION V1, distinct from `Evaluation
Engine`, `Confidence Engine`, and every other frozen component. ADR-0005 freezes the structure
only; it does not specify or implement Verification.

ADR-0007 assigns to the future Verification Engine the semantic responsibility for "Verification
of derived consequences," alongside the ownership tables repeated by ADR-0008 and ADR-0009.
ADR-0010 and ADR-0011 preserve `verified` and `verification_status` as concerns explicitly
excluded from the Prediction / Counterfactual result, assigning their future ownership to
Verification Engine without freezing any concrete representation. ADR-0012 establishes explicitly
that `Evaluation != Verification`: Evaluation produces a utility/value judgment against normative
semantic content, while "Verification owns correctness, validity, and verification semantics."

None of ADR-0007 through ADR-0014 positively defines what kind of correctness or validity
Verification concerns, what it operates against, or whether it is minimally shared between
Prediction and Counterfactual. M0-15A through M0-15G performed sequential, read-only discovery to
resolve exactly this gap, each time preferring the minimum semantically justified answer over
speculative structure, per `AGENTS.md`'s governing principle: do not introduce abstractions before
a concrete use demonstrates they are needed. That discovery found no production `verification`
package, no request/result/status contract, no port/engine/adapter, and no concrete consumer; it
established that ownership does not by itself resolve consumption or operation semantics; it tested
retrospective actuality correspondence against the shared Prediction / Counterfactual component and
found it not viable as a shared minimum, because an explicit hypothetical divergence does not
assert occurrence and therefore has no general actuality to correspond to; and it found
derived-content validity within its derivation context semantically compatible with both Prediction
and Counterfactual, requiring no new mode, temporal model, or discriminator. This ADR records the
cumulative result of that discovery. It does not extend it, and it does not create any production
contract.

## Decision

### Verification minimum semantic category

Verification, in minimum V1, concerns the **correctness/validity of derived content**.

### Semantic scope

That correctness/validity is evaluated **within the derivation context under which the content was
produced** — not in the abstract, and not against a subsequent real-world occurrence of that
context.

### Not abstract judgment

Verification does not judge derived content in isolation from the scenario that produced it. The
derivation context is semantically relevant to determining correctness/validity, even though this
ADR does not freeze any concrete representation of that context (see "Derivation context is a
semantic concept only" below).

### Not retrospective actuality correspondence

Minimum V1 Verification is not "does derived content correspond to what was later observed or
accepted as actual." See "Actuality correspondence" below for the full rationale.

### Not utility/value

Verification is not Evaluation. Verification does not judge whether derived content is desirable,
beneficial, or valuable against a normative frame. Correctness/validity is not utility.

### Not confidence

Verification is not the Confidence Engine. Correctness/validity is not a confidence score or
threshold.

### Not epistemic qualification

Verification does not perform epistemic status classification, provenance tracking, or conflict
resolution. Those remain Epistemic Model responsibilities, unaffected by this ADR.

### Uniform Prediction / Counterfactual applicability

This minimum semantic axis is uniform for derived content produced by **both** Prediction and
Counterfactual. Prediction derives content relative to a baseline without an explicit hypothetical
divergence. Counterfactual derives content relative to a baseline under one or more explicit
hypothetical divergences. A Counterfactual divergence does not assert occurrence, does not alter
current belief, and exists only within the hypothetical scenario under consideration (ADR-0007).
Correctness/validity within the derivation context remains meaningful in both cases, because it
does not require the scenario to ever become actual — it is evaluated relative to the scenario
itself, real or hypothetical. This ADR does not create a Verification mode, a discriminator, or any
distinction between Prediction-derived and Counterfactual-derived content for the purpose of this
minimum semantic category.

### Derivation context is a semantic concept only

"Derivation context" in this ADR is a semantic boundary, not a structural freeze. It means only
that the scenario under which content was derived is relevant to judging that content's
correctness/validity. It does not approve, and this ADR does not create, any of: a
`DerivationContext` class, a `VerificationContext` class, a `baseline_ref` field on a Verification
contract, a `divergence_refs` field, a `world_model_ref`, an `evidence_ref`, a `scenario_ref`, a
`context_ref`, a direct type dependency on Prediction / Counterfactual request or result types, or
any other concrete representation. How the derivation context reaches a future Verification
operation is entirely deferred.

### Derived content, not derivation process

This minimum freezes **derived-content validity**, not **derivation-process validity**. No
derivation trace, proof artifact, process representation, or execution trace exists anywhere in the
repository today capable of grounding a semantics of verifying the mechanism or algorithm that
produced derived content. Verification of the derivation process itself is therefore not part of
this minimum freeze. This does not declare that process verification can never exist — only that it
is not part of minimum V1 semantics.

### Actuality correspondence

Retrospective correspondence between derived content and later observed/accepted actuality is not
part of the minimum Verification semantic freeze. This kind of correspondence may make sense for
Prediction specifically, but it is not applicable uniformly across the shared Prediction /
Counterfactual component, because a Counterfactual hypothetical divergence does not assert
occurrence, and the repository has no general representation of "the hypothetical having become
actual." Excluding actuality correspondence from the minimum does not prohibit it from ever
existing: it remains a possible future specialized concern, subject to its own evidence and its own
architectural decision, without contradicting the minimum frozen here.

### Shared Prediction / Counterfactual result context

Prediction and Counterfactual currently share one result contract, `PredictionCounterfactualResult`,
which carries no intrinsic mode discriminator — no field of that result identifies whether a given
consequence was produced by a Prediction or a Counterfactual derivation. This is recorded here as
contextual evidence supporting the uniform applicability of this minimum semantic category; it is
not used to approve a dependency. This ADR does not create or approve any relationship between a
future Verification contract and `PredictionCounterfactualResult`, `PredictionRequest`, or
`CounterfactualRequest`.

### First/minimum Verification subject: deferred

This ADR does not decide the first/minimum Verification subject. Although "derived content" makes
an individual Prediction / Counterfactual consequence the strongest textual candidate discovered so
far, the concrete subject decision — whether it is one individual consequence, a consequence
collection, the whole `PredictionCounterfactualResult`, an `EpistemicClaim`, a `ReasoningOutcome`, a
`Plan`, an `EvaluationResult`, or any other candidate — remains for a separate gate. This ADR does
not create `VerificationSubject`, `VerifiedSubject`, `SubjectRef`, `VerificationTarget`, or any
equivalent.

### Subject cardinality: deferred

This ADR does not decide whether the minimum subject is exactly one, one-or-more, or the whole
result.

### Correlation: deferred

This ADR does not copy Evaluation's `target_ref + consequence` correlation pattern, and does not
approve `target_ref`, `subject_ref`, `consequence_ref`, `request_ref`, `result_ref`, or
`verification_ref` as a Verification correlation contract.

### Reference representation: deferred

Ownership does not by itself resolve consumption: a component may reference or consume a concept
owned by another component without acquiring its ownership, as already demonstrated by existing
repository precedent (for example, `baseline_ref` referencing a scenario without importing
`SituationModel`). This ADR records that principle but does not choose how a future Verification
operation would receive its derivation context — opaque reference, by-value transport,
application-provided semantic content, or another mechanism all remain possible and undecided.

### Output semantics: deferred

This ADR does not infer any concrete output representation from "correctness," "validity,"
"verified," or "verification_status." None of `bool`, pass/fail, valid/invalid,
verified/unverified, an enum, a textual judgment, an evidence set, a score, or a confidence value
is approved. `verified` and `verification_status` remain historical ownership vocabulary from
ADR-0010/ADR-0011, not structure approved by this ADR.

### Non-success semantics: deferred

This ADR does not decide `UNKNOWN`, `UNVERIFIED`, `NOT_VERIFIABLE`, `INSUFFICIENT_EVIDENCE`,
`INDETERMINATE`, or `UNRESOLVED` as Verification vocabulary. It does not reuse
`EvaluationStatus.NO_JUDGMENT`, `PredictionCounterfactualStatus.INSUFFICIENT_KNOWLEDGE`, or any
other contract's vocabulary by analogy.

### Evaluation boundary

Evaluation and Verification remain distinct, exactly as ADR-0012 established. Evaluation concerns a
utility/value judgment against normative semantic content. Verification concerns correctness/
validity of derived content within its derivation context. Correctness is not utility; validity is
not utility. Verification does not use a normative frame as a consequence of this ADR. No
dependency between Evaluation and Verification, in either direction, is approved here.

### Epistemic / Confidence boundary

Confidence, provenance, `EpistemicStatus`, supporting evidence, counter evidence, and conflict
tracking remain Epistemic Model / Confidence Engine responsibilities, unaffected by this ADR.
Verification does not absorb these concerns. This does not prohibit a future, separately decided
Verification capability from referencing or consuming an existing Epistemic concept without owning
it — ownership does not imply prohibition of consumption — but no such consumption is approved
here.

### Situation Model boundary

The agent's current believed situation remains the Situation Model's responsibility. This ADR does
not transform `SituationModel`, `SituationDelta`, or any observed/applicable state into Verification
ground truth, and it creates no dependency between Verification and Situation Model.

### World Model boundary

World Model production remains **BLOCKED** by ADR-0006. This minimum Verification semantics does
not depend on the existence of a production World Model, and this ADR does not unblock it.

### Prediction / Counterfactual execution boundary

This ADR does not unblock `PredictionExecutor`, `CounterfactualExecutor`, `PredictionEngine`, or
`CounterfactualEngine`. Prediction / Counterfactual Implementation Gate item 4 (execution port)
remains **PARKED**. No Prediction / Counterfactual contract is altered by this ADR.

### Verification execution boundary

This ADR is semantic foundation only. It does not approve `VerificationRequest`,
`VerificationResult`, `VerificationStatus`, `VerificationExecutor`, `VerificationPort`, a
`VerificationEngine` implementation, `VerificationService`, `VerificationPolicy`,
`VerificationAdapter`, or `VerificationExecutionError`. All remain future decisions.

### Provider independence

This semantic category is independent of any LLM, `ModelRouter`, provider, prompt, temperature,
tool calling, JSON schema, or model confidence, consistent with ADR-0002. No technical mechanism
defines correctness or validity.

### Minimum-novelty rationale

Actuality correspondence as a shared minimum would require additional decisions about temporal
semantics, an actuality/outcome concept, occurrence identity, and a Prediction/Counterfactual
asymmetry. Derived-content validity does not require resolving those additional decisions in order
to freeze this minimum semantic axis.

### Reversibility

Freezing derived-content validity as the minimum does not prevent a future capability of
retrospective actuality correspondence from being introduced later. Such a capability would require
its own evidence and its own architectural decision; this ADR does not promise it will be created.

### Decision summary

| Concern | Decision |
| --- | --- |
| Verification minimum semantic category | Derived-content correctness/validity |
| Semantic scope | Within the derivation context |
| Applies to Prediction | Yes |
| Applies to Counterfactual | Yes |
| Requires scenario to become actual | No |
| Retrospective actuality correspondence | Not minimum; possible future separate concern |
| Derivation-process verification | Not minimum / deferred |
| First/minimum subject | Deferred |
| Subject cardinality | Deferred |
| Correlation | Deferred |
| Reference representation | Deferred |
| Output representation | Deferred |
| Non-success semantics | Deferred |
| Execution topology | Deferred |
| Provider dependency | None |

## Not Decided Here

- exact Verification subject
- subject cardinality
- correlation
- reference representation
- request structure
- result structure
- output representation
- status vocabulary
- non-success semantics
- evidence representation
- temporal/actuality specialization
- execution port
- application/engine
- adapter/provider
- execution error
- concrete consumer
- persistence
- API/serialization

## Consequences

**Positive:**

1. Verification now has a positive semantic foundation instead of an ownership label alone.
2. The subject question, blocked in M0-15B pending operation semantics, can now be resumed in a
   separate gate.
3. The minimum semantic category is uniform across Prediction and Counterfactual, avoiding a mode
   discriminator or premature asymmetry.
4. Evaluation, Epistemic Model, Confidence Engine, Situation Model, and World Model boundaries
   remain intact and unaffected.
5. No speculative structure, wrapper, or identity is introduced.

**Tradeoff:**

1. Structural contract discovery (request/result) remains blocked until subject, cardinality,
   correlation, reference representation, and output semantics are each separately decided.
2. Execution topology remains entirely blocked; no Verification operation can be executed end to
   end yet.
3. Retrospective actuality correspondence, while not prohibited, has no approved path forward and
   would require its own future decision.
4. Derivation-process verification remains unaddressed, so a mechanism-level correctness concern
   cannot yet be expressed by this foundation.

## ADR Relationship

ADR-0015 complements ADR-0005, ADR-0006, ADR-0007, ADR-0008, ADR-0009, ADR-0010, ADR-0011, and
ADR-0012. It supersedes none of them. ADR-0012 remains authoritative for the boundary between
Evaluation and Verification; ADR-0015 resolves only the minimum semantic axis that ADR-0012 left
open.
