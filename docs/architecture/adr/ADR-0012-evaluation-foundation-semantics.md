# ADR-0012: Evaluation Foundation Semantics

- Status: Accepted
- Date: 2026-08-19

## Context

ADR-0005 freezes `Evaluation Engine` as a distinct component of COGNITION V1, separate from
`Verification Engine`, `Confidence Engine`, and every other frozen component. ADR-0005 freezes the
structure only; it does not specify or implement Evaluation.

ADR-0007 assigns `Utility/ranking of consequences` to the future Evaluation Engine, as part of the
ownership table established alongside hypothetical divergence semantics. ADR-0008 and ADR-0009
repeat the same ownership row. ADR-0010 states explicitly: `"Utility, rank, priority, and score are
not included [in the Prediction / Counterfactual result]. Their ownership belongs to the future
Evaluation Engine."` ADR-0011 repeats the same list, dividing it further between Evaluation Engine
(utility, rank, priority, score) and Verification Engine (`verified`, `verification_status`).

None of ADR-0007, ADR-0008, ADR-0009, ADR-0010, or ADR-0011 defines utility, rank, priority, or
score as a single unified representation. They establish an ownership boundary only: if these
concerns exist, Evaluation Engine owns them. No ADR prior to this one has examined what Evaluation
actually is, what it evaluates, how it correlates to what it evaluates, what it produces, or what
that output requires to be meaningful.

M0-14A through M0-14J performed sequential, read-only discovery to answer exactly these questions,
each time preferring the minimum semantically justified answer over speculative structure, per
`AGENTS.md`'s governing principle: do not introduce abstractions before a concrete use demonstrates
they are needed. This ADR records the cumulative result of that discovery. It does not extend it,
and it does not create any production contract.

## Decision

### Evaluation subject

The first/minimum supported Evaluation subject in V1 is **one individual Prediction /
Counterfactual consequence** — one textual consequence statement, as already represented inside
`PredictionCounterfactualResult.consequences`.

This is a first/minimum-supported-subject finding, not an exclusivity claim. It does not declare
that Evaluation will only ever evaluate a P/C consequence, and it does not foreclose other subjects
(a `Plan`, a `ReasoningOutcome`, an `EpistemicClaim`) from being evaluated in the future under their
own evidence and their own decision.

### Whole result rejected as subject

The entire `PredictionCounterfactualResult` is **not** the minimum Evaluation subject. Multiple
consequence statements returned by one derivation are not exhaustive (ADR-0010), carry no AND/OR or
other relationship semantics (ADR-0010 "No relationship semantics"), and carry no ordering (ADR-0010
"No ordering semantics"). Treating the whole result as one evaluated subject would require
aggregation/composition semantics across those statements that no ADR has approved. This ADR does
not approve them here either.

### Consequence collection rejected as subject

A collection of consequence statements — short of the whole result, but more than one item — is
similarly **not** frozen as a minimum subject, for the same reason: no composition or aggregation
semantics across multiple consequence statements exists or is approved.

### Subject value semantics

An individual consequence, as an Evaluation subject, remains exactly what ADR-0010 already defines
it as: a plain textual consequence statement belonging to the P/C result. This ADR does not add
`consequence_id`, `consequence_ref`, or a dedicated `Consequence` value object. ADR-0010's explicit
refusal to wrap a bare string is preserved and not reopened.

### Subject correlation

The evaluated subject is described, at the semantic-value level, by:

```text
target_ref
+
exact consequence statement
```

This is **value-level semantic correlation**: it identifies *which* textual consequence, in *which*
target's scope, a judgment concerns. It is explicitly **not**:

- global identity;
- occurrence identity;
- scenario identity;
- result identity;
- request identity;
- provenance.

### target_ref role, preserved

`target_ref` keeps exactly the meaning ADR-0008/ADR-0009/ADR-0010 already gave it: an opaque
semantic-scope correlation anchor for the derivation target. It does not identify the individual
consequence, and it does not identify an Evaluation operation. ADR-0010 and ADR-0011 are not
altered by this ADR.

### No consequence identity

The fact that Evaluation is a semantic consumer of one individual consequence is not, by itself,
sufficient new evidence to introduce consequence identity. ADR-0010's threshold — "no approved
consumer needs to reference one consequence individually" — is not met by a consumer that merely
reads the value. The minimum V1 Evaluation semantics are **value-oriented**, not
occurrence-tracing-oriented. If concrete future evidence demonstrates a need to distinguish
otherwise-identical consequence occurrences, identity may be reconsidered through its own explicit
decision. This ADR does not foreclose that; it only declines to approve it now.

### No Prediction / Counterfactual contract change

`PredictionCounterfactualResult` does **not** change as a result of this ADR. No field is added, no
consequence wrapper is created, and no discriminator is introduced. M0-13 (Prediction /
Counterfactual execution) remains a fully separate, unaddressed concern.

### Output semantic category

Evaluation produces, semantically, a **utility/value judgment** about the evaluated consequence.
This ADR does not freeze the concrete representation of that judgment (see below).

### Vocabulary limit

No synonym set is frozen. `desirable`, `undesirable`, `beneficial`, `harmful`, `positive`,
`negative`, `good`, and `bad` are not approved contract vocabulary. The only approved conceptual
label is **utility/value judgment**.

### Normative reference requirement

Utility/value is not intrinsic to the consequence. A minimum judgment requires some **normative
semantic reference content**, external both to the consequence being judged and to the derivation
target that scoped it.

### Target is not the normative frame

ADR-0008 is preserved without modification: a derivation target is semantic focus, not goal; it
does not gain utility, desirability, or objective semantics merely by existing. `target_ref` and
`target_statement` therefore do not, by themselves, supply the normative reference content
Evaluation needs.

### Normative frame owner deferred

The semantic owner/source of the normative frame remains **deferred by design**. This ADR does not
assign that ownership to Planning, Identity, Autonomy, Evaluation itself, Memory, Emotions, or
Metacognition. No bounded context is authorized to produce or hold this content by virtue of this
ADR.

### Planning goal status

`PlanningRequest.goal_ref`/`goal_statement` remain **precedent only** — evidence of how a normative
textual statement is typically shaped in this repository (`str`, non-empty after strip, exact value
preserved, no coercion, no normalization). They are not reused. Evaluation gains no dependency on
Planning by this ADR. No generic `Goal` concept is created.

### Criterion status

`Criterion`, `EvaluationCriterion`, `criterion_ref`, and `criterion_statement` are not approved. The
term "criterion" appears nowhere in this repository with positive, Evaluation-specific meaning; its
use in prior discovery was a conceptual placeholder for an unresolved reference point, not a
repository-grounded domain concept, and is not frozen as one here.

### Preference / agent-value status

`Preference`, `AgentPreference`, `AgentValue`, `ValueProfile`, `Objective`, `Drive`, and
`Motivation` are not approved. Current repository evidence — including entirely empty `identity`,
`autonomy`, `emotions`, `metacognition`, and `memory` bounded contexts — does not define any of
these as an owner or a contract.

### Minimum normative frame representation

The minimum V1 normative frame is represented, semantically, as **exactly one textual normative
semantic value**. No opaque reference of its own is required.

### Frame string semantics

That textual value follows the same invariant family already used throughout the cognition domain
(`target_statement`, `goal_statement`, `problem_statement`, `InformationNeed.description`): a `str`;
non-empty after a strip validation; the exact original value preserved; no trim mutation; no
normalization; no coercion. This freezes representation *semantics*, not a field name.

### Frame cardinality

The minimum V1 normative frame cardinality is **exactly one** per utility/value judgment. A judgment
with zero normative frame content is not semantically complete. Multiple simultaneous normative
frames, and any composition semantics between them, are not approved by this ADR and are not
decided here.

### No frame reference

The minimum V1 normative frame does not require `frame_ref`, `criterion_ref`, `goal_ref`,
`normative_ref`, an opaque identity, or a stable correlation identity of its own. No semantic
identity distinct from the normative content itself is currently evidenced.

### Owner/source distinction not made

The minimum contract does not distinguish the same normative textual value arriving from different
future sources/owners. This is not an ontological claim that such sources are equivalent; it means
only that source/occurrence distinction is not part of minimum V1 Evaluation semantics.

### Frame explicitness deferred

Whether the normative frame is delivered as an explicit field of a future request, or made
available implicitly through an engine/policy/state mechanism, is not decided here. The frame is
semantically required; how it reaches the evaluation operation is deferred. This ADR does not use
the phrase "explicit input" as a structural freeze.

### Utility judgment cardinality

The minimum Evaluation operation produces **exactly one** semantic utility/value judgment about the
evaluated consequence. This is a semantic-cardinality finding. It does not freeze a Python field,
container, class, or numeric type.

### Utility representation deferred

Numeric representation, categorical representation, textual representation of the output, enum
representation, and value-object representation are all explicitly deferred. This ADR freezes
*meaning*, not concrete output encoding.

### Numeric scales not approved

None of `[0, 1]`, `[-1, 1]`, or an unbounded numeric scalar is approved as the utility
representation. No semantics currently exist for what zero, one, or a negative value would mean;
no unit, anchor, precision, or comparability rule has been established. This is a "not required in
minimum V1" finding, not a claim that a numeric scale can never exist.

### No generic score

`score: float` is not approved as the utility representation. The existing numeric scores in this
repository — `AttentionDecision.score`, `CognitiveModeDecision.intrinsic_score`/`effective_score`,
`ContextCandidate.relevance`, `EpistemicClaim.confidence` — each measure a different axis (attention
salience, cognitive demand, context relevance, epistemic confidence, respectively) governed by its
own component-specific policy. None is transferable to utility/value by analogy alone.

### Orderability

The minimum utility/value judgment does **not** require ordering. Ordering is not part of the
necessary minimum V1 utility meaning. A single judgment about one consequence, relative to one
normative frame, is semantically complete on its own, without reference to any other judgment.

### Same-frame comparability

Two judgments sharing the same normative frame are not, by that fact alone, established as
comparable. A shared frame may be *necessary* for a future comparison to make sense, but it is not,
by itself, sufficient evidence of comparison semantics. This ADR does not approve same-frame
comparability.

### Rank, priority, and score as future concerns

`rank`, `priority`, and `score` remain **future Evaluation Engine concerns**, per the ownership
boundary established across ADR-0007/0008/0009/0010/0011. They are not minimum utility fields, they
do not automatically derive from utility, utility does not depend on them, and no relationship
contract between any of them is approved by this ADR.

### Shared owner is not shared representation

ADR-0010 and ADR-0011 list `utility`, `rank`, `priority`, and `score` under one ownership sentence.
This is **ownership grouping**, established for the same reason the repository's other ownership
tables group unrelated concerns under one owner (`AttentionDecision` bundles `priority`, `score`,
and `disposition` as three distinct, non-reducible outputs of one component; `CognitiveModeDecision`
bundles `intrinsic_score`, `effective_score`, `selected_mode`, and `reasons` the same way). It is
**not** evidence of one unified output, one scale, one pipeline, or one dependency graph between
utility and rank/priority/score.

### Future ranking capability

A future ranking capability may be introduced on its own evidence. This ADR does not decide its
input shape, its comparison-set semantics, its sort keys, its policy, its dependency (or lack
thereof) on the utility representation frozen here, or tie-breaking semantics. `ContextComposer`'s
existing ranking implementation — a consumer-side composite sort key over multiple independent
fields, entirely external to the ranked value type — is recorded as the closest repository
precedent for how such a capability could be built later without requiring the individual judgment
itself to pre-declare order semantics today.

### Unknown / not-evaluable deferred

`UNKNOWN`, `NOT_EVALUABLE`, `INSUFFICIENT_CONTEXT`, `UNRESOLVED`, and any corresponding status are
not decided here. This ADR does not decide what happens when Evaluation cannot produce a valid
utility/value judgment, and does not create such a status by symmetry with Reasoning or Prediction /
Counterfactual.

### Evaluation is not Verification

Evaluation produces a utility/value judgment. Verification owns correctness, validity, and
verification semantics (ADR-0010, ADR-0011). Evaluation does not represent its judgment as
`pass`/`fail` or `valid`/`invalid`, and does not introduce `verified`/`verification_status`.

### Evaluation is not Confidence

Utility/value remains distinct from confidence. Confidence remains an Epistemic Model /
Confidence Engine concern (ADR-0007). No scale is shared between the two by this ADR.

### Evaluation is not Probability

Probability, likelihood, and expected utility are not introduced. Probability remains deferred
throughout the Prediction / Counterfactual domain (ADR-0010); combining it with utility into an
expected-utility calculation is explicitly outside this ADR's minimum freeze.

### Evaluation is not Attention

`AttentionPriority`, `AttentionDecision.score`, and `AttentionFactors` are not reused. Utility/value
is not attention salience or urgency.

### Evaluation is not Mode Arbitration

`CognitiveModeDecision.intrinsic_score`/`effective_score` are not reused. Utility/value is not
cognitive demand.

### Provider independence

Every semantic decision in this ADR is independent of any LLM, `ModelRouter`, Ollama, prompt,
token, temperature, JSON schema, or provider output, consistent with ADR-0002 (agent independent
from LLM).

### No execution contract

This ADR does not create or approve `EvaluationEngine`, `EvaluationExecutor`, `EvaluationRequest`,
`EvaluationResult`, `EvaluationOutcome`, `EvaluationPolicy`, `EvaluationCriterion`, `Utility`,
`UtilityScore`, or `EvaluationStatus`. These remain structural/execution questions for a later,
separate decision.

### No package yet

This ADR does not create `src/noema/cognition/domain/evaluation/`. It is documentation-only. A
production Evaluation package remains unauthorized until a future structural decision approves one.

### No application consumer

No concrete production Evaluation application consumer exists today. This ADR resolves semantic
foundation only; it does not resolve execution topology.

### M0-13 boundary

The relationship established here — a P/C consequence as the minimum Evaluation subject — does not
unblock `PredictionExecutor`, `CounterfactualExecutor`, `PredictionEngine`, or
`CounterfactualEngine`. Prediction / Counterfactual Implementation Gate item 4 (execution port)
remains **PARKED**, untouched by this ADR.

### World Model boundary

World Model production remains **BLOCKED** by ADR-0006. This ADR does not alter that gate.

### Decision summary

| Concern | Decision |
| --- | --- |
| First/minimum subject | Individual P/C consequence |
| Subject correlation | `target_ref` + exact consequence statement |
| Consequence identity | Not required |
| P/C result modification | None |
| Output semantic category | Utility/value judgment |
| Normative frame required | Yes |
| Normative frame owner | Deferred |
| Minimum normative frame representation | One textual normative value |
| Frame identity/ref | Not required |
| Frame cardinality | Exactly one |
| Utility judgment cardinality | Exactly one semantic judgment |
| Utility concrete representation | Deferred |
| Numeric scale | Deferred / not approved |
| Ordering | Not required |
| Same-frame comparability | Not required |
| Rank | Future Evaluation concern |
| Priority | Future Evaluation concern |
| Score | Future Evaluation concern |
| Unknown/not-evaluable | Deferred |
| Execution boundary | Deferred |

### Ownership table

| Concern | Owner |
| --- | --- |
| Scenario-specific consequence derivation | Prediction / Counterfactual |
| Consequence textual semantics | Prediction / Counterfactual |
| Utility/value judgment | Evaluation Engine |
| Normative-frame source/owner | Deferred |
| Ranking | future Evaluation Engine |
| Priority | future Evaluation Engine |
| Score | future Evaluation Engine |
| Epistemic qualification/confidence | Epistemic Model |
| Verification | Verification Engine |
| World-model dynamics | World Model |

No new bounded context is introduced by this table.

## Not Decided Here

- `EvaluationRequest`
- `EvaluationResult`
- `EvaluationOutcome`
- utility field name
- concrete utility representation
- numeric scale
- numeric range
- direction
- utility ordering
- comparison semantics
- rank contract
- priority contract
- score contract
- normative frame field name
- frame explicit-vs-implicit delivery
- frame owner/source
- criterion abstraction
- preferences
- agent values
- unknown/not-evaluable status
- validation error
- execution port
- application service
- provider/model adapter
- persistence
- runtime tracing identity

## Consequences

**Positive:**

- Evaluation's minimum subject, correlation, and output category are settled without inventing
  speculative structure.
- No new identity, wrapper, or cross-domain dependency is introduced.
- `PredictionCounterfactualResult` remains untouched; Gate boundaries for P/C stay independent of
  Evaluation's foundation.
- The ownership bundle in ADR-0007/0008/0009/0010/0011 is clarified as grouping, not a unified
  representation, preventing premature numeric/ordering commitments.
- Evaluation, Verification, Confidence, Attention, and Mode Arbitration boundaries remain intact
  and mutually exclusive.
- Future ranking, priority, and score capabilities remain free to be designed on their own
  evidence, unconstrained by a premature utility representation.

**Tradeoff:**

- No executable Evaluation capability exists yet.
- The normative frame's owner is unresolved; Evaluation cannot yet be exercised end to end.
- The concrete utility representation (numeric, categorical, or textual) remains undecided, so no
  structural contract can be written from this ADR alone.
- Rank, priority, and score remain unimplemented, deferring on the ownership boundary ADR-0007
  through ADR-0011 already established.
- Unknown/not-evaluable semantics remain unresolved, so a complete Evaluation operation cannot yet
  be fully specified end to end.

## ADR Relationship

ADR-0012 complements ADR-0005, ADR-0006, ADR-0007, ADR-0008, ADR-0009, ADR-0010, and ADR-0011. It
supersedes none of them.
