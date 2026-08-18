# ADR-0009: Prediction and Counterfactual Request Structure

- Status: Accepted
- Date: 2026-08-17

## Context

ADR-0005 freezes `Prediction / Counterfactual` as one structural component.

ADR-0006 assigns that component scenario-specific consequence derivation.

ADR-0007 froze:

- Prediction: baseline + zero explicit hypothetical divergences.
- Counterfactual: baseline + one or more explicit hypothetical divergences.

ADR-0008 froze: every minimal derivation is scenario plus exactly one derivation target. A
derivation target is an opaque reference plus a textual semantic statement.

ADR-0008 explicitly left deferred: one request vs. separate requests; flat vs. nested target;
the divergence container; and final field spelling. M0-13H resolved these points through
read-only audit. This ADR records that resolution.

## Decision

### Primary decision

Prediction and Counterfactual use **separate request types** inside the **same** frozen
Prediction / Counterfactual structural component: `PredictionRequest` and
`CounterfactualRequest`. This does not create a prediction bounded context, a counterfactual
bounded context, separate engines, separate ports, or separate application services. Two
request types are not a structural component split.

### Why separate request types

Prediction and Counterfactual have distinct semantic intents. In a single request whose intent
were inferred by divergence cardinality, adding one explicit divergence would silently change
Prediction into Counterfactual. With separate types, that change requires explicitly moving
from a `PredictionRequest` to a `CounterfactualRequest`. The caller chooses the semantic
operation.

### No cardinality-inferred request type

The minimal contract does not use a single request whose semantic intent is inferred solely by
`len(divergence_refs)`. Cardinality continues to define the divergence semantics of each
operation, but it does not implicitly select the operation's class.

### No discriminator

This ADR does not create `mode`, `kind`, `type`, `PredictionMode`, `DerivationKind`,
`ScenarioKind`, or `InferenceMode`. The request class itself already carries the distinction; a
discriminator would be redundant information.

### PredictionRequest

The future contract is conceptually frozen as:

```text
PredictionRequest:
    baseline_ref: str
    target_ref: str
    target_statement: str
```

`PredictionRequest` does not have `divergence_refs`, or any other explicit-hypothetical-
divergence field. This makes "Prediction with an explicit hypothetical divergence" impossible
by the shape of the type.

### CounterfactualRequest

```text
CounterfactualRequest:
    baseline_ref: str
    target_ref: str
    target_statement: str
    divergence_refs: tuple[str, ...]
```

`divergence_refs` is required, has no empty default, and must contain at least one item.

### Flattened target

The derivation target is flattened into the request as `target_ref` and `target_statement`.
This ADR does not create `target: DerivationTarget` in this structure. Rationale: target
cardinality is exactly one; it has no lifecycle of its own; no reuse of it is approved; its
invariants are only two non-empty strings; and `ReasoningRequest` and `PlanningRequest` already
use this same flattened pattern for their own cardinality-one semantic focus.

### No DerivationTarget value object

This ADR does not approve a `DerivationTarget` class. This does not declare that such a value
object can never exist — it declares that the current minimal request contract does not have
sufficient evidence to introduce the wrapper.

### Field spelling

The following names are frozen:

- `baseline_ref`
- `target_ref`
- `target_statement`
- `divergence_refs`

Rationale: `baseline_ref` uses the normative terminology ADR-0007 already established.
`target_ref`/`target_statement` use the conceptual name ADR-0008 already established.
`divergence_refs` uses the normative terminology of explicit hypothetical divergence without
introducing a new concept. This ADR does not use `situation_ref`, `scenario_ref`, `goal_ref`,
`problem_ref`, `derivation_ref`, or `request_ref`.

### baseline_ref

`baseline_ref: str`. Invariants: exact type `str`; non-empty after a strip validation; original
value preserved; no trim mutation; no normalization; no coercion. `baseline_ref` remains
opaque and does not imply `SituationModel`.

### target_ref

`target_ref: str`. Invariants: exact type `str`; non-empty after a strip validation; exact
value preserved; no normalization/coercion. `target_ref` remains an opaque semantic
correlation anchor; it is not request identity.

### target_statement

`target_statement: str`. Invariants: exact type `str`; non-empty after a strip validation;
exact value preserved; no normalization/coercion. It has no fixed grammar and is not a prompt.

### Divergence reference type

Each divergence reference is `str`. Invariants: exact type `str`; non-empty after a strip
validation; exact value preserved; no normalization/coercion. This ADR does not create
`DivergenceRef`, `InterventionRef`, `UUID`, or `TSID`.

### Divergence container

`CounterfactualRequest.divergence_refs` is represented as `tuple[str, ...]`. Rationale: the
request is immutable; the repository has precedent for immutable repeated references using
tuple; a tuple preserves the input supplied; it does not silently collapse duplicates; it does
not canonicalize; it does not auto-order; and it does not require deciding conflict/composition
semantics.

### Critical ordering clarification

The tuple preserves caller-provided order as representation. The current request contract
assigns **no** semantic precedence, priority, causal ordering, override ordering, or
composition meaning to tuple position. This ADR does not assert permutation equivalence, and it
does not assert order-independent equality. Python/dataclass structural equality remains
naturally sensitive to tuple order — this is representation equality, not a claim of semantic
equivalence between permutations. Future composition semantics may require an explicit new
decision.

### Duplicate rejection

`divergence_refs` must not contain duplicate references. Rationale: the same opaque identity
repeated does not represent a new explicit hypothetical divergence. Validate explicitly with
`len(divergence_refs) == len(set(divergence_refs))` or semantically equivalent behavior. This
ADR does not use `frozenset` for silent collapse.

### At least one divergence

For `CounterfactualRequest`, `len(divergence_refs) >= 1` is a required invariant; an empty
tuple is invalid. `PredictionRequest` has no divergence field at all.

### Conflicts and composition remain deferred

This ADR does not decide whether one divergence conflicts with another, overrides another,
precedes another, causes another, how multiple divergences compose, their independence, or
their compatibility. No resolver or checker is created.

### Dataclass shape

Both request types are expected to follow `@dataclass(frozen=True, slots=True, kw_only=True)`,
matching `ReasoningRequest`, `PlanningRequest`, and the existing domain contracts.

### Immutability

Requests are immutable value contracts. No `list`, `set`, or mutable mapping is used.

### No coercion

No conversion of `int → str`, `UUID → str`, `list → tuple`, `set → tuple`, or
whitespace-only-to-normalized-text. An invalid type is rejected. The exact input contract must
be respected.

### Validation errors

Two minimal `DomainError`s are frozen: `InvalidPredictionRequestError` and
`InvalidCounterfactualRequestError`. Both belong to the cognition domain error boundary. This
ADR does not create an error per field.

### Error file ownership

Following the existing organization, a future implementation may place both errors in a
concern-specific error module equivalent to `prediction_counterfactual_errors.py`, exported
through `noema.cognition.domain.errors`. This ADR freezes the ownership and names of the
errors; it does not need to freeze internal module details beyond the single-concern rule.

### DomainError vs. TypeError

A request-construction invariant violation raises the dedicated `DomainError`. A future
application boundary receiving the wrong request object may use `TypeError`, following existing
patterns. This ADR does not create an application boundary.

### Single component

`PredictionRequest` and `CounterfactualRequest` belong to the same Prediction / Counterfactual
component. This ADR does not introduce `prediction/` and `counterfactual/` as separate
packages.

### Future package ownership

The recommended and approved name for the future single domain package is
`prediction_counterfactual` — i.e., `src/noema/cognition/domain/prediction_counterfactual/`.
This is the direct mechanical mapping of the nominal component `Prediction / Counterfactual`
and avoids an artificial hierarchy. No package is created at this step.

### Future public domain API

The minimal future public API of this package is `PredictionRequest` and
`CounterfactualRequest`. No other public type is approved by this ADR. This excludes
`DerivationTarget`, `Scenario`, `Baseline`, `Divergence`, `Intervention`, `PredictionResult`,
`CounterfactualResult`, `Executor`, and `Engine`.

### Target reference/statement correspondence

ADR-0008 is preserved: the domain does not validate external correspondence between
`target_ref` and `target_statement`. No resolver or materializer is introduced.

### No request identity

This ADR does not create `request_id`, `prediction_id`, `counterfactual_id`, `derivation_id`,
or `correlation_id`. `target_ref` is the semantic correlation anchor. Runtime tracing remains a
separate concern.

### ContextPackage excluded

`ContextPackage` is not introduced into the requests.

### CognitiveBudget excluded

`CognitiveBudget` is not introduced into the requests. It remains an execution/orchestration
concern.

### Strategy/mode excluded

`ReasoningStrategy`, `PredictionStrategy`, `CounterfactualStrategy`, `mode`, `kind`, and any
discriminator are not introduced.

### Situation excluded

`SituationModel`, `SituationEntry`, and `SituationDelta` are not introduced. `baseline_ref` is
an opaque reference.

### Epistemology excluded

`EpistemicClaim`, confidence, status, provenance, and evidence are not introduced.

### World Model excluded

`WorldModel`, transition rules, dynamics rules, causal rules, conditions, and effects are not
introduced.

### Provider independence

The requests are entirely independent of an LLM, the model router, `ModelExecutionEngine`,
Ollama, prompts, JSON, `STRUCTURED_OUTPUT`, and tokenization.

### Invalid-state elimination

| State                       | PredictionRequest         | CounterfactualRequest |
| ---------------------------- | -------------------------- | ----------------------- |
| zero divergences              | structurally valid         | invalid                 |
| one divergence                 | impossible by type         | valid                    |
| multiple divergences           | impossible by type         | valid                    |
| blank baseline                 | invalid                    | invalid                  |
| blank target ref               | invalid                    | invalid                  |
| blank target statement         | invalid                    | invalid                  |
| duplicate divergence refs      | N/A                        | invalid                  |

### Semantic operation table

| Request type          | Scenario                                     | Semantic intent |
| ----------------------- | --------------------------------------------- | ---------------- |
| `PredictionRequest`      | baseline + target                             | Prediction        |
| `CounterfactualRequest`  | baseline + target + ≥1 explicit divergences    | Counterfactual     |

The request class itself makes intent explicit.

### No inheritance

This ADR does not create `BaseDerivationRequest`, `ScenarioRequest`,
`PredictionBaseRequest`, or inheritance between the two requests. The duplication of
`baseline_ref`, `target_ref`, and `target_statement` is intentional and small. DRY does not
justify a domain abstraction.

### No shared target object for DRY

A `DerivationTarget` is not created merely to reduce duplication between the two requests.

### Request gate

This ADR resolves item 1 — request shape — of the Prediction / Counterfactual Implementation
Gate. Item 1 is **RESOLVED**. Production request contracts may be implemented after this ADR
is reviewed/merged.

### Remaining Prediction gates

Still blocked, and not decided here:

2. result cardinality and minimum consequence representation;
3. empty-result and insufficient-knowledge semantics;
4. whether any execution port is actually required.

### World Model gate

Production World Model remains blocked by ADR-0006. This ADR does not resolve dynamics
representation, the World Model domain shape, conditions/effects, materialization, or
prediction result semantics.

### No result contract

This ADR does not create or approve `PredictionResult`, `CounterfactualResult`,
`PredictionOutcome`, `CounterfactualOutcome`, `Consequence`, or `PossibleConsequence`.

### No execution port

This ADR does not create or approve `PredictionExecutor`, `CounterfactualExecutor`,
`DerivationExecutor`, `PredictionEngine`, or `CounterfactualEngine`.

### Ownership table

| Concern                                              | Owner                                                                     |
| ----------------------------------------------------- | --------------------------------------------------------------------------- |
| Current believed situation                            | Situation Model                                                             |
| Reusable dynamics knowledge                           | World Model                                                                 |
| Baseline reference                                    | Prediction / Counterfactual                                                 |
| Derivation target                                     | Prediction / Counterfactual                                                 |
| Explicit hypothetical divergences                     | Counterfactual request semantics within Prediction / Counterfactual         |
| Prediction request identity by type                   | `PredictionRequest`                                                          |
| Counterfactual request identity by type               | `CounterfactualRequest`                                                      |
| Epistemic qualification                               | Epistemic Model                                                             |
| Utility/ranking                                       | future Evaluation Engine                                                    |
| Verification                                          | future Verification Engine                                                  |

"Request identity by type" means semantic operation type, not a runtime `request_id`.

## Not Decided Here

- result representation
- result cardinality
- empty-result semantics
- insufficient-knowledge semantics
- result correlation fields
- execution port
- application boundary
- model/provider adapter
- World Model dynamics representation
- World Model domain shape
- scenario/materialization resolver
- divergence conflict semantics
- divergence composition semantics
- divergence causal/override semantics
- persistence
- runtime tracing identity
- retries/fallback/cache
- budget enforcement

## Consequences

**Positive:**

- Caller chooses Prediction vs. Counterfactual explicitly.
- Prediction-with-divergence is an impossible state by type.
- No redundant discriminator.
- Target stays minimal and flat.
- Opaque references remain provider/domain independent.
- Tuple preserves caller representation without silently collapsing information.
- Duplicates produce an explicit validation failure.
- The request gate can be closed before result/port design.
- The single structural component remains intact.

**Tradeoff:**

- Three fields are duplicated between two request classes.
- A future boundary may need to accept both request types.
- Tuple structural equality is order-sensitive even though tuple position currently has no
  semantic precedence.
- Conflict/composition semantics remain undefined.
- No result contract exists yet.
- No executable Prediction/Counterfactual exists yet.
- World Model remains blocked.

## ADR Relationship

ADR-0009 complements ADR-0005, ADR-0006, ADR-0007, and ADR-0008. It supersedes none of them.
ADR-0009 resolves decisions ADR-0008 explicitly left deferred.
