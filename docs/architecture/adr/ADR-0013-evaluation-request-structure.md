# ADR-0013: Evaluation Request Structure

- Status: Accepted
- Date: 2026-08-20

## Context

ADR-0012 froze the semantic foundation of the future Evaluation Engine. Among the points already
frozen there:

- the first/minimum supported Evaluation subject is one individual Prediction / Counterfactual
  consequence;
- the subject's value-level correlation is `target_ref` + exact consequence statement;
- some normative semantic reference content is required for a utility/value judgment to be
  meaningful;
- the minimum normative frame is exactly one textual normative semantic value;
- the normative frame's identity/ref is not required;
- the normative frame's owner/source remains deferred;
- the utility/value output representation remains deferred.

ADR-0012 explicitly left two things undecided: whether the normative frame is delivered
explicitly or implicitly, and the concrete `EvaluationRequest` contract itself. M0-14R had already
established that the request track and the result track carry independent blockers. M0-14S
resolved the request transport question: all three semantic roles (target-scope correlation,
consequence text, normative text) are explicit, by-value operation data, with no approved implicit
carrier and no dependency this creates on any future normative-frame owner. M0-14T resolved the
concrete naming and structure question: one flat request class, `EvaluationRequest`, with three
`str` fields (`target_ref`, `consequence`, `normative_statement`), no wrapper, no nested subject or
frame object, following the same dataclass and validation conventions already established by
`ReasoningRequest`, `PlanningRequest`, `PredictionRequest`, and `CounterfactualRequest`.

This ADR consolidates M0-14S and M0-14T into a single accepted decision. It is documentation-only:
it does not create the request class, its package, its error, its tests, or any execution
contract.

## Decision

### Minimum V1 Evaluation request

The minimum V1 Evaluation request is **one explicit domain request contract**: `EvaluationRequest`.

### Request scope

`EvaluationRequest` represents one request to evaluate one individual Prediction / Counterfactual
consequence, within its target semantic scope, against one normative semantic statement.

This is the first/minimum supported request shape. It does not mean Evaluation only ever evaluates
Prediction / Counterfactual consequences. Any future subject (a `Plan`, a `ReasoningOutcome`, an
`EpistemicClaim`, or anything else) requires its own evidence and its own decision, and may require
its own request shape or an evolution of this one. This ADR does not foreclose or pre-design that.

### Request count

Minimum V1 requires **exactly one** request type. `PredictionEvaluationRequest` and
`CounterfactualEvaluationRequest` are not created. The consequence's Prediction-vs-Counterfactual
origin is not part of the minimum Evaluation subject semantics (ADR-0012), so it has no bearing on
request cardinality either.

### Explicit transport

All minimum semantic input the operation needs is delivered **explicitly** by the request. The
request contains:

1. a target-scope correlation value;
2. an exact consequence textual value;
3. a normative textual semantic value.

None of the three is obtained implicitly from an engine, a policy, or state in the minimum V1
contract.

### Owner vs. transport

`normative_statement` being request-explicit does **not** resolve or alter normative-frame
ownership. The source/owner of the normative content remains deferred by design, exactly as ADR-0012
left it. Explicit transport is a statement about how the operation receives a value; it is not a
statement about who produces or is accountable for that value.

### Concrete shape

```text
EvaluationRequest
- target_ref: str
- consequence: str
- normative_statement: str
```

Flat. No nested object.

### target_ref

`target_ref` keeps exactly the meaning already preserved by ADR-0008, ADR-0009, ADR-0010, and
ADR-0012: an opaque semantic-scope correlation anchor for the derivation target. It is not
consequence identity, not evaluation identity, not request identity, and not provenance.

### consequence

`consequence` represents the exact individual textual Prediction / Counterfactual consequence
being evaluated. The spelling is singular: `consequence`. `PredictionCounterfactualResult` already
establishes `consequences: tuple[str, ...]`, and the individual item is conceptually a consequence
throughout the existing ADR corpus and code. No `consequence_ref`, `consequence_id`,
`consequence_statement` wrapper, or dedicated `Consequence` value object is added.

### normative_statement

`normative_statement` is the exactly-one textual normative semantic value against which the
consequence is evaluated. The spelling is `normative_statement`: the representation is textual,
"statement" matches the established textual-semantic family already used elsewhere in this domain,
and it avoids three specific ambiguities — implying an opaque identity (`reference`), implying a
structured object (`frame`), and colliding with the utility/value output vocabulary (`value`).

### normative_statement precision

`normative_statement` does not mean `target_statement`, `goal_statement`, `criterion_statement`, a
utility/value result, or an opaque normative ref. It is its own concept: textual normative semantic
content, unrelated to the derivation target's own textual statement and unrelated to any other
`_statement` field elsewhere in this domain.

### No frame object

`NormativeFrame`, `EvaluationFrame`, `Criterion`, and `EvaluationCriterion` are not created. A plain
textual value is sufficient for the minimum V1 request.

### No Prediction / Counterfactual result dependency

`EvaluationRequest` does not accept `PredictionCounterfactualResult`. The minimum subject is one
individual consequence, not the whole result; passing the whole result would require consequence
selection/materialization semantics that are not approved. A direct dependency on a sibling
cognition domain-contract is not necessary when the frozen subject semantics are already fully
expressible by value. This is sibling-component/domain-contract coupling under consideration, not a
cross-bounded-context dependency, and this ADR declines it regardless of how it is labeled.

### No subject wrapper

`EvaluationSubject`, `ConsequenceSubject`, `EvaluatedConsequence`, or an equivalent wrapper are not
created. No independent identity, lifecycle, behavior, additional invariant, or reuse justifies
one.

### No subject ref

`subject_ref`, `evaluation_subject_ref`, and `consequence_ref` are not created. ADR-0012 already
found no need for consequence occurrence identity.

### Flat representation

Three flat fields. No inheritance, no discriminator, no nested subject/frame structure.

### Field types

All three fields are exactly `str`. None of `Optional`, `Sequence`, `tuple`, `Enum`, `Literal`,
`Any`, `object`, `dict`, or generic JSON is used.

### Dataclass structure

The future production `EvaluationRequest` should be frozen, slotted, and keyword-only — the same
structural convention already used by `ReasoningRequest`, `PlanningRequest`, `PredictionRequest`,
and `CounterfactualRequest`:

```text
@dataclass(frozen=True, slots=True, kw_only=True)
```

This ADR records this structural convention conceptually. No code is created by this ADR.

### String validation

Each field must be an exact `str` value, must be non-empty after strip validation, preserves the
exact caller-provided string, performs no trimming mutation, no normalization, and no coercion.

### target_ref validation

`target_ref` is opaque. No UUID, TSID, URI, provider-format, prefix, or external-existence
validation is performed — only string type and non-blank content.

### consequence validation

`consequence` requires string type and non-blank content, with the exact text preserved. No
semantic parsing, no propositional-atomicity validation, no source/provenance validation, no
verification that the consequence exists in a `PredictionCounterfactualResult`, and no
correspondence check against `target_ref`.

### normative_statement validation

`normative_statement` requires string type and non-blank content, with the exact text preserved. No
normalization, no coercion, no criterion parsing, no goal parsing, and no value-scale parsing.

### Cross-field validation

No approved cross-field invariant exists. `target_ref` ↔ `consequence` correspondence,
`consequence` ↔ `normative_statement` compatibility, and `target_ref` ↔ `normative_statement`
compatibility are not validated. Each field owns only its own independent minimum invariant.

### Validation error

`InvalidEvaluationRequestError` is the `DomainError` raised when `EvaluationRequest` violates its
domain representation:

```text
InvalidEvaluationRequestError(DomainError)
```

Exact human-facing error-message strings are not frozen by this ADR.

### Error topology

Future placement: `src/noema/cognition/domain/errors/evaluation_errors.py`, re-exported through
`src/noema/cognition/domain/errors/__init__.py`. No Evaluation-local `errors.py` and no generic
shared validation error are introduced.

### Domain package

Future production placement: `src/noema/cognition/domain/evaluation/`. This ADR structurally
identifies that placement. Creating the package remains blocked until this ADR is reviewed and
integrated.

### Request module

Future module: `src/noema/cognition/domain/evaluation/evaluation_request.py`. The package's public
surface, `evaluation/__init__.py`, exports `EvaluationRequest`. No future result or engine modules
are implied by this placement.

### Error public surface

`cognition/domain/errors/__init__.py` should eventually export `InvalidEvaluationRequestError`. The
exact mechanical ordering follows current repository conventions at implementation time; this ADR
does not freeze a line-number or order-specific implementation detail.

### No ContextPackage

`EvaluationRequest` does not include `ContextPackage`. No minimum evidence requires contextual
slices.

### No CognitiveBudget

`EvaluationRequest` does not include `CognitiveBudget`. No minimum Evaluation budget semantics are
approved.

### No target_statement

`target_statement` is not included. The Evaluation subject correlation uses `target_ref` +
`consequence`. `target_statement` belongs to the derivation request semantics (Prediction /
Counterfactual), not to the minimum Evaluation request.

### No baseline/divergence

`baseline_ref` and `divergence_refs` are not included. Evaluation does not reproduce scenario
provenance.

### No Prediction/Counterfactual discriminator

No Prediction-vs-Counterfactual mode, source kind, or discriminator is included. The minimum
evaluated subject semantics intentionally do not distinguish its Prediction / Counterfactual
source.

### No provenance

`request_ref`, `result_ref`, `scenario_ref`, `source_ref`, `origin`, and `provenance` are not
included.

### No utility output

`EvaluationRequest` contains no `utility`, `value`, `score`, `rank`, `priority`, or result status.
None of these are request inputs.

### Result remains blocked

The Evaluation result production contract remains **blocked**. The exact blocker: the utility/value
judgment already has semantic meaning (ADR-0012), but no approved concrete representation exists.
This ADR does not resolve that blocker.

### Not-evaluable remains deferred

`UNKNOWN`, `NOT_EVALUABLE`, `INSUFFICIENT_CONTEXT`, and `UNRESOLVED` remain deferred. None of them
is part of request structure.

### Execution port remains blocked

`EvaluationExecutor`, `EvaluationPort`, and an `Evaluator` port are not created. The execution port
remains blocked.

### Engine/application boundary remains blocked

No production `EvaluationEngine` or application service is created. ADR-0005's normative existence
of the Evaluation Engine component does not, by itself, authorize an implementation boundary yet.

### No concrete application consumer

No concrete production Evaluation application consumer currently exists. This does not invalidate
the domain request contract recorded here, but it continues to block execution topology.

### Prediction / Counterfactual boundary

Prediction / Counterfactual Implementation Gate item 4 (execution port) remains **PARKED**.
`EvaluationRequest` does not unblock `PredictionExecutor`, `CounterfactualExecutor`,
`PredictionEngine`, or `CounterfactualEngine`.

### World Model boundary

World Model production remains **BLOCKED** by ADR-0006. This ADR does not alter that gate.

### Provider independence

No `EvaluationRequest` field references an LLM, a provider, a model, a prompt, a token, a
temperature, a JSON schema, Ollama, or `ModelRouter`, consistent with ADR-0002 (agent independent
from LLM).

### Decision table

| Concern | Decision |
| --- | --- |
| Request class | `EvaluationRequest` |
| Request count | One minimum request type |
| Subject transport | Explicit, by value |
| Target field | `target_ref: str` |
| Consequence field | `consequence: str` |
| Normative field | `normative_statement: str` |
| Normative-frame owner | Deferred |
| Structure | Flat |
| Wrapper | None |
| P/C result dependency | None |
| Dataclass | frozen / slots / kw-only |
| Validation | exact `str`, nonblank, preserve exact value |
| Cross-field invariants | None |
| Validation error | `InvalidEvaluationRequestError` |
| Domain package | `cognition/domain/evaluation` |
| Result | Blocked / deferred |
| Execution port | Blocked |
| Engine/application service | Blocked |

## Not Decided Here

- Evaluation result class name
- utility/value representation
- utility field name
- numeric/categorical/textual output
- Evaluation status
- not-evaluable semantics
- rank
- priority
- score
- execution port
- execution error
- engine/application boundary
- concrete consumer
- provider/model adapter
- persistence
- normative-frame owner/source
- future additional Evaluation subject types
- future migration/generalization of `EvaluationRequest` if new subjects appear

## ADR Relationship

ADR-0013 complements ADR-0005, ADR-0008, ADR-0009, ADR-0010, ADR-0011, and ADR-0012. It supersedes
none of them. ADR-0012 remains authoritative for Evaluation's semantic foundation; ADR-0013 resolves
only the request transport/structure questions ADR-0012 explicitly deferred.

## Consequences

**Positive:**

- The minimum Evaluation input is now structurally complete: a single, flat, three-field request
  shape with resolved naming, types, validation topology, and package placement.
- No speculative wrapper, identity, or nested object is introduced.
- No dependency on the Prediction / Counterfactual result artifact is introduced.
- Normative-frame ownership remains independent of, and unresolved by, this transport decision.
- A future production request implementation becomes possible once this ADR is reviewed and
  integrated.

**Tradeoff:**

- The request remains consequence-specific in V1; supporting another Evaluation subject in the
  future may require a new structural decision or an evolution of this request shape.
- The Evaluation result still cannot be implemented; no executable Evaluation operation exists.
- Request completeness does not imply result, port, or engine readiness — all three remain
  independently blocked.
