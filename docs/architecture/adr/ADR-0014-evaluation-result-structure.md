# ADR-0014: Evaluation Result Structure

- Status: Accepted
- Date: 2026-08-20

## Context

ADR-0012 froze the semantic foundation of the future Evaluation Engine, including the utility/value
judgment category, the evaluated subject, and its value-level correlation. ADR-0013 froze the
concrete `EvaluationRequest` contract. Both ADRs deliberately deferred everything about the
Evaluation result: the concrete representation of a successful utility/value judgment, whether
Evaluation can semantically fail to produce one, and — if so — how that condition is represented.

A sequence of read-only discoveries (M0-14AG through M0-14AN) resolved these deferred questions one
at a time: the minimum successful judgment representation, its semantic field name, the recognition
and representation of a semantic no-judgment condition, the discriminator field and state
vocabulary, the exact result contract structure, and finally the exact scope of result-level
correlation. This ADR consolidates that cumulative result. It does not reopen any of it, and it does
not introduce execution topology.

ADR-0012 originally deferred utility representation, result structure, and non-success semantics as
open questions, not as permanent prohibitions. This ADR extends those earlier deferred decisions by
resolving them; it does not contradict or replace ADR-0012, and it does not contradict or replace
ADR-0013.

## Decision

### Successful utility/value judgment representation

The minimum V1 successful utility/value judgment is represented as **one textual string value**,
under the semantic field name `utility_judgment`.

`utility_judgment` follows the same invariant family already used throughout the cognition domain:
a string value; non-empty after strip validation; the exact caller-provided textual content
preserved; no normalization; no coercion. Validation is expressed as `isinstance`-style string
checking, consistent with every existing contract in this domain — not as a `type(value) is str`
requirement.

### Utility representation exclusions

Minimum V1 does not require, and this ADR does not introduce: a numeric utility (`int`, `float`,
`Decimal`, or any bounded scale); a categorical utility or polarity taxonomy; a boolean desirability
flag; multidimensional utility (benefit/cost/risk/tradeoff or similar); a dedicated `Utility` value
object; or any utility identity/reference.

### Orderability preserved

Consistent with ADR-0012: `utility_judgment` carries no intrinsic ordering requirement. No
same-frame comparability is created. No cross-target comparability is created. Rank, priority, and
score remain future Evaluation Engine concerns; they are not fields of the minimum result and are
not implied by it.

### utility_judgment naming rationale

`utility` alone risks implying a numeric magnitude or established measurement scale — exactly the
representation ADR-0012 declines to approve. `judgment` alone is less precise and more generic
outside an Evaluation-scoped context. `utility_judgment` preserves both words of the approved
conceptual vocabulary ("utility/value judgment") while avoiding the numeric-scale implication that
"utility" alone would carry. No synonym taxonomy (`desirable`, `undesirable`, `beneficial`,
`harmful`, `positive`, `negative`, `good`, `bad`, or equivalents) is introduced.

### Semantic no-judgment condition

Evaluation may semantically produce no valid utility/value judgment for a structurally valid
`EvaluationRequest`. This condition is distinct from all of the following:

- an `InvalidEvaluationRequestError` (a representation/invariant violation of the request itself);
- a domain representation invariant violation of the result (see "Result domain error" below);
- a technical execution failure (an infrastructure/technology failure, unrelated to this ADR since
  no execution boundary exists yet).

It is a valid semantic Evaluation result condition in its own right, exactly as `UNRESOLVED` is a
valid `ReasoningOutcome` and `INSUFFICIENT_KNOWLEDGE` is a valid `PredictionCounterfactualResult` —
neither is a technical failure.

### No hidden status inside utility_judgment

The semantic absence of a judgment must never be encoded as text inside `utility_judgment`.
Strings such as `"cannot evaluate"`, `"unknown"`, or `"insufficient information"` are not valid
substitutes for the no-judgment state. The textual `utility_judgment` is the judgment itself, not
metadata describing the absence of one.

### Result topology

Minimum V1 uses **one result contract**. That contract currently requires **two** mutually
exclusive semantic states. This is a minimum-V1 finding, not a permanent ceiling: minimum V1
currently requires two states, and no third state is authorized by this ADR. A future state may be
introduced through its own evidence and its own decision.

### Status field

The discriminator field is named `status`, matching the exact repository precedent already
established by `ReasoningOutcome.status` and `PredictionCounterfactualResult.status`.

### Status type

The status type is `EvaluationStatus`, an `Enum`, matching the exact repository convention already
established by `ReasoningStatus`, `PredictionCounterfactualStatus`, and `EpistemicStatus`. Its exact
members are:

```text
EvaluationStatus
- JUDGED
- NO_JUDGMENT
```

with conceptual values `"judged"` and `"no_judgment"`, following the existing repository `Enum`
convention of lowercase string values.

### JUDGED semantics

`JUDGED` means only that a valid `utility_judgment` exists. It does not mean technical execution
success, verification success, epistemic certainty, or ranking success — each of those remains the
responsibility of a different component (Verification Engine, Epistemic Model / Confidence Engine,
future ranking capability, respectively).

### NO_JUDGMENT semantics

`NO_JUDGMENT` means only that no valid `utility_judgment` was produced for semantic reasons. It does
not freeze *why*. Cause vocabulary such as `NOT_EVALUABLE`, `UNKNOWN`, `UNRESOLVED`,
`INSUFFICIENT_CONTEXT`, or `INSUFFICIENT_KNOWLEDGE` is not assigned to this state. Cause taxonomy
remains deferred to a future, separate decision, made on its own evidence.

### No-judgment payload

Minimum V1 `NO_JUDGMENT` carries no additional semantic payload. No `reason`, `reason_summary`,
`information_needs`, `missing_context`, `explanation`, or `error_message` field is introduced.

### Subject correlation

ADR-0012 is preserved exactly: the Evaluation subject is one individual Prediction / Counterfactual
consequence, and its value-level subject descriptor is `target_ref` + exact consequence statement.
Therefore `EvaluationResult` retains both `target_ref` and `consequence`. Both are required.

### target_ref limit

`target_ref` alone does not identify the individual consequence — it is only a target-scope
correlation anchor, and one target may scope multiple consequences. `target_ref`-only result
correlation is therefore insufficient on its own; `target_ref` and `consequence` together are the
minimum subject correlation.

### No identity

`evaluation_ref`, `request_ref`, `result_ref`, `subject_ref`, `consequence_ref`, and `judgment_ref`
are not introduced. `EvaluationResult` remains value-oriented, with no occurrence identity and no
provenance field.

### Normative statement retention

`normative_statement` remains a required field of `EvaluationRequest`. It is **not** duplicated in
the minimum V1 `EvaluationResult`.

Normative semantic content is required to *produce* the judgment, but no approved invariant requires
the result itself to repeat every operation input. This mirrors the repository-wide pattern already
established across every existing request/result pair in this domain: `problem_statement`,
`goal_statement`, `target_statement`, `baseline_ref`, and `divergence_refs` are all required inputs
for their respective operations, and none of them is duplicated in `ReasoningOutcome`,
`Plan`, or `PredictionCounterfactualResult`. Required input does not imply required result
representation.

### Normative ownership unaffected

The normative frame's owner/source remains deferred, exactly as ADR-0012 and ADR-0013 left it.
Omitting `normative_statement` from `EvaluationResult` does not change that ownership status in
either direction — it was never assigned by virtue of explicit request transport, and it is not
assigned or foreclosed by virtue of result omission either.

### Final result shape

```text
EvaluationResult
- target_ref: str
- consequence: str
- status: EvaluationStatus
- utility_judgment: str | None
```

Exactly these four fields, in exactly this order. No fifth field.

### Result name

The result type is named `EvaluationResult`, not `EvaluationOutcome` or `EvaluationDecision`.
`EvaluationResult` is the neutral semantic result container, consistent with
`PredictionCounterfactualResult` — the closest repository precedent, itself a result type with an
explicit multi-state status and no concrete execution engine. Domain naming does not depend on
application/execution readiness; `EvaluationOutcome` is not adopted merely because `ReasoningOutcome`
also carries an explicit status, since Evaluation's naming is not required to track Reasoning's.
`EvaluationDecision` is rejected because Evaluation produces a judgment, not a decision/selection
between alternatives (unlike `AttentionDecision` or `CognitiveModeDecision`).

### Dataclass structure

The future production `EvaluationResult` should be frozen, slotted, and keyword-only:

```text
@dataclass(frozen=True, slots=True, kw_only=True)
```

matching every existing domain contract in this repository (`ReasoningOutcome`,
`PredictionCounterfactualResult`, `PlanningRequest`, `Plan`, `EvaluationRequest`). This ADR records
this structural convention conceptually. No code is created by this ADR.

### String invariants

`target_ref`: string; non-empty after strip validation; exact value preserved; no normalization; no
coercion.

`consequence`: same invariant family.

`utility_judgment`, when present: same invariant family.

### Status type invariant

The future production result must require `status` to be an `EvaluationStatus`, validated
consistently with how every existing status/enum field in this domain is validated. This ADR does
not prescribe implementation details beyond this conceptual runtime type requirement.

### Cross-validation matrix

| status | utility_judgment | Valid |
| --- | --- | --- |
| `JUDGED` | valid non-blank textual value | Yes |
| `JUDGED` | `None` | No |
| `NO_JUDGMENT` | `None` | Yes |
| `NO_JUDGMENT` | textual value | No |

No other combination is valid.

### Optionality

The future field type is `utility_judgment: str | None`. `None` is not an implicit status by itself
— it is valid only because `status` explicitly discriminates the two states and the two fields are
cross-validated against each other, mirroring the existing precedent of
`ReasoningOutcome.conclusion: str | None` cross-validated against `ReasoningStatus`.

### No sentinels

Blank strings, magic strings, or sentinel objects are not used to represent `NO_JUDGMENT`. Absence
is represented only by `None`, discriminated by `status`.

### Result domain error

The future dedicated invariant error is `InvalidEvaluationResultError`, inheriting directly from
`DomainError`:

```text
InvalidEvaluationResultError(DomainError)
```

It represents invalid `EvaluationResult` construction/invariant violations only. It is neither a
technical execution failure nor the semantic `NO_JUDGMENT` state — both remain entirely separate
concerns.

### Future package surface

Once implementation is authorized, the `evaluation` domain package may conceptually expose exactly:

```text
EvaluationRequest
EvaluationResult
EvaluationStatus
```

No port or engine is authorized by this ADR. `InvalidEvaluationResultError` belongs with the
domain's centralized errors package, consistent with repository convention (mirroring
`InvalidEvaluationRequestError`'s existing placement).

### Technical failure remains outside result semantics

Technical Evaluation execution failure remains outside `EvaluationResult`'s semantic states. No
technical execution error is created by this ADR, because no Evaluation execution port or
application boundary currently exists.

### Port / engine boundary preserved

Evaluation port: **BLOCKED**. Evaluation engine/application: **BLOCKED**. No concrete production
application consumer or execution boundary currently exists to justify execution dependency
inversion. This ADR does not unblock execution topology.

### Rank, priority, and score remain future concerns

Consistent with ADR-0012, `rank`, `priority`, and `score` remain future Evaluation Engine concerns.
None of them is added to `EvaluationResult` by this ADR.

### Confidence and verification remain out of scope

`confidence`, `probability`, `verified`, and `verification_status` are not added. Confidence remains
an Epistemic Model / Confidence Engine concern; verification remains a Verification Engine concern,
per ADR-0012.

### Provider independence

Every decision in this ADR is independent of any LLM, Ollama, `ModelRouter`, provider, prompt, JSON
mode, structured output, or tool-calling mechanism, consistent with ADR-0002 (agent independent from
LLM).

### Prediction / Counterfactual boundary

Prediction / Counterfactual execution remains **PARKED**. This ADR does not unblock Prediction /
Counterfactual Implementation Gate item 4 (execution port).

### World Model boundary

World Model production remains **BLOCKED** by ADR-0006. This ADR does not alter that gate.

### Decision summary

| Concern | Decision |
| --- | --- |
| Result name | `EvaluationResult` |
| Status type | `EvaluationStatus` (Enum) |
| Status field | `status` |
| Status values | `JUDGED`, `NO_JUDGMENT` |
| Subject correlation | `target_ref` + `consequence`, both required |
| Normative statement retention | Required in request; not duplicated in result |
| Utility representation | One textual string value |
| Utility field | `utility_judgment` |
| Utility optionality | `str \| None`, cross-validated against `status` |
| Cross-validation | `JUDGED` ⇔ present; `NO_JUDGMENT` ⇔ absent |
| No-judgment payload | None beyond the status itself |
| Error | `InvalidEvaluationResultError(DomainError)` |
| Execution topology | Not addressed; port/engine remain blocked |

## Not Decided Here

- concrete Python implementation of `EvaluationResult`/`EvaluationStatus`/
  `InvalidEvaluationResultError`
- exact validation error message strings
- module/package placement mechanics beyond the conceptual surface listed above
- `EvaluationExecutor` / execution port
- `EvaluationEngine` / application service
- concrete application consumer
- cause taxonomy for `NO_JUDGMENT`
- rank, priority, or score contracts
- confidence or verification contracts
- normative-frame owner/source
- persistence, serialization, or API/network contracts
- future additional Evaluation subject types
- future migration/generalization of `EvaluationResult` if new subjects or states appear

## Non-Goals

This ADR explicitly does not: implement `EvaluationResult`, `EvaluationStatus`, or
`InvalidEvaluationResultError`; create an `EvaluationExecutor`; create an `EvaluationEngine` or
application service; introduce ranking, score, or priority; introduce confidence or verification;
introduce a cause taxonomy for `NO_JUDGMENT`; assign normative-frame ownership; introduce
persistence, serialization, or API contracts; change Prediction / Counterfactual execution; or
unblock World Model production.

## ADR Relationship

ADR-0012 remains valid and authoritative for Evaluation's semantic foundation. ADR-0013 remains
valid and authoritative for `EvaluationRequest`. ADR-0014 extends both only by freezing the minimum
V1 result contract that ADR-0012 explicitly deferred (utility representation, result structure, and
non-success semantics were left open questions there, not permanent prohibitions). ADR-0014
supersedes none of them and introduces no contradiction with either.

## Consequences

**Positive:**

- The exact minimum Evaluation result contract becomes implementable once this ADR is integrated.
- Semantic non-success (`NO_JUDGMENT`) remains explicitly distinct from technical execution failure
  and from request-representation errors.
- No speculative score, taxonomy, or ranking capability is introduced.
- The result remains provider-neutral, independent of any LLM or model infrastructure.
- Subject correlation is unambiguous: `target_ref` + `consequence` together, never `target_ref`
  alone.

**Tradeoff:**

- The normative basis (`normative_statement`) is not repeated in the result; interpreting a judgment
  in isolation from its originating request requires external association.
- No cause taxonomy exists yet for `NO_JUDGMENT`; a future decision may need to introduce one.
- Future ranking, priority, or score capabilities may require separate contracts or an evolution of
  this result shape.
- The execution boundary (port/engine) remains entirely unresolved; no Evaluation operation can be
  executed end to end yet.
