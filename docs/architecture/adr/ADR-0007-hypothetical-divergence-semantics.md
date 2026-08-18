# ADR-0007: Hypothetical Divergence Semantics

- Status: Accepted
- Date: 2026-08-17

## Context

ADR-0005 freezes a single nominal component: `Prediction / Counterfactual`.

ADR-0006 defines:

- **Situation Model** = current believed situation
- **World Model** = reusable dynamics knowledge
- **Prediction / Counterfactual** = scenario-specific consequence derivation
- **Epistemic Model** = epistemic qualification

ADR-0006 also determines:

- cross-component domain references remain opaque by default;
- no direct World Model dependency on situation, epistemology, planning, reasoning, or
  model_router;
- `SituationDelta` does not represent a hypothetical transition;
- a production `world_model` package remains blocked behind an Implementation Gate.

M0-13C (Prediction Consumer Contract Discovery) confirmed Prediction / Counterfactual as the
first probable World Model consumer with HIGH confidence, but found three gaps ahead of any
production contract:

1. representation of hypothetical divergence / intervention;
2. one request vs. two requests;
3. result cardinality / semantics.

The first gap is semantically prior to the other two: no `PredictionRequest` or
`CounterfactualRequest` field list can be written responsibly without first knowing how a
hypothetical divergence from a baseline is represented.

## Decision

### Baseline

Prediction / Counterfactual reasoning occurs relative to a **baseline** — the situation or
scenario taken as the reference point for the derivation being requested. The baseline is not
declared as a new component. It is not necessarily a `SituationModel` object. At the domain
boundary, a reference to the baseline must remain an opaque identity/reference.

### Baseline is not ownership

Prediction / Counterfactual must not own or mutate the current believed `SituationModel`
merely because a baseline references the current situation. A reference to a baseline does not
transfer ownership of the Situation Model, does not create a duplicated snapshot, and does not
authorize a direct import of `SituationModel`.

### Hypothetical divergence

A **hypothetical divergence** is an explicitly assumed difference from the baseline, for the
purpose of deriving possible consequences. It represents "assume something differs from the
baseline," not "update what the agent currently believes is true."

### Prediction semantics

Prediction derives possible consequences relative to a baseline **without** an explicit
hypothetical divergence. This does not mean prediction without context, prediction without
implicit assumptions, factual or verified prediction, or prediction with automatic confidence.
It means only that no explicit counterfactual divergence has been introduced by the requesting
boundary.

### Counterfactual semantics

Counterfactual derives possible consequences relative to a baseline **under one or more**
explicit hypothetical divergences. Counterfactual semantic intent therefore requires at least
one explicitly asserted divergence from the baseline. This is conceptual semantics only; this
ADR does not define a tuple, frozenset, list, field name, class, or request shape for it.

### Prediction / Counterfactual remains one component

This ADR does not split the frozen component `Prediction / Counterfactual` into
`PredictionEngine` / `CounterfactualEngine`, a prediction bounded context, a counterfactual
bounded context, or any other structural split. The distinction drawn here is **semantic
intent** (presence or absence of an explicit divergence), not a structural component split.

### Hypothetical divergence is not SituationDelta

Hypothetical divergence must not be represented canonically as `SituationDelta`.
`SituationDelta` has a `base_version`, has an `occurred_at`, operates on a concrete
`SituationModel`, and represents an observed/applicable change to the current believed
situation. A hypothetical divergence does not assert occurrence, does not alter current belief,
and exists only within the hypothetical scenario under consideration.

### Hypothetical divergence is not an EpistemicClaim

Hypothetical divergence must not be represented canonically as `EpistemicClaim`. It does not
automatically imply `EpistemicStatus.ASSUMPTION`, `EpistemicStatus.HYPOTHESIS`, or
`EpistemicStatus.PREDICTION`. Epistemology may in the future qualify a divergence or a derived
consequence through an explicit boundary, but the divergence itself does not take on
confidence, provenance, supporting evidence, counter evidence, or claim conflicts as its own
responsibility.

### Hypothetical divergence is not World Model dynamics

A hypothetical divergence belongs to the scenario being evaluated. World Model dynamics
knowledge describes how referenced things may relate or change. Divergence is therefore not a
dynamics rule: the divergence is semantic input to the scenario; dynamics is reusable knowledge
potentially consumed during derivation. This ADR does not create a precondition or effect
concept.

### Opaque reference rule

Baseline and hypothetical divergences must cross domain boundaries by opaque reference. This
ADR does not decide the concrete type (`str`, `UUID`, `TSID`, a value object, a `BaselineRef`,
a `ScenarioRef`, an `InterventionRef`, a `DivergenceRef`, or any other name). None of these
names is approved as a contract by this decision.

### Materialization

The Prediction / Counterfactual domain must not assume it can dereference baseline/divergence
references by itself. Resolution/materialization remains a separate, undefined
responsibility. This ADR does not create a `ContextResolver`, `SituationResolver`,
`ScenarioResolver`, or `Materializer`.

### Divergence cardinality

Only the semantics are fixed:

- Prediction: zero explicit hypothetical divergences.
- Counterfactual: one or more explicit hypothetical divergences.

This ADR does not decide the container type, ordering, duplicate semantics, or normalization.

### Multiple divergences

This ADR permits, semantically, more than one divergence within a counterfactual. It does not
decide whether divergences are ordered, whether they are independent, whether they can
conflict, how conflicts would be resolved, whether one overrides another, or any composition
semantics. These remain deferred until a concrete contract is designed.

### Divergence is not a condition

A hypothetical divergence must not automatically be treated as a World Model condition,
precondition, causal antecedent, or transition trigger. A divergence may in the future
participate in the selection or application of dynamics, but that is not decided here.

### Divergence is not an effect

A hypothetical divergence is not a predicted consequence, an effect, a result, or a future
state. It is part of the input scenario. Consequences belong to the future result semantics of
Prediction / Counterfactual.

### Reasoning strategy remains unrelated

`ReasoningStrategy.COUNTERFACTUAL` is a strategy identifier belonging to the Reasoning Engine.
It is not the representation of hypothetical divergence. This ADR does not change
`ReasoningRequest`, `ReasoningOutcome`, `ReasoningEngine`, or `ReasoningStrategy`.

### Planner remains unrelated

Planner does not create or own a hypothetical divergence as part of the planning domain. A
future Planner or application coordinator may request a counterfactual derivation through an
explicit boundary, but `Plan` and `PlanStep` do not change in this ADR.

### Result semantics remain deferred

This ADR does not decide the result of Prediction / Counterfactual. The following remain
undecided: single consequence, multiple consequences, empty consequence set, text statement,
opaque consequence references, structured consequences, hypothetical state, information need,
or insufficient knowledge.

### Empty result

The empty-`Plan` precedent is not transferred automatically. No result/empty-result semantics
are decided here. A future contract may adopt a structurally-valid empty result, but must
define explicitly what it does or does not mean.

### Probability, confidence, and utility

Transition probability, epistemic confidence, model log-probability, and evaluation utility
remain explicitly distinct concepts. This ADR introduces none of them. Prediction /
Counterfactual does not receive automatic ownership of confidence, utility, ranking, or
verification.

### Temporal semantics

The following remain undecided: prediction horizon, before/after, effective time, duration,
temporal ordering, and intervention timing. No temporal model is created.

### One request vs. two requests

This ADR does not decide whether a future contract will use one request type without a
discriminator, one request type with a mode/kind, or separate prediction/counterfactual request
types. It decides only the semantics necessary for any of those shapes: Prediction has no
explicit divergence; Counterfactual has one or more.

### No discriminator

This ADR does not approve any new enum, including `PredictionKind`, `ScenarioKind`,
`SimulationMode`, or `InferenceMode`.

### Ownership table

| Concern                                              | Owner                                 |
| ----------------------------------------------------- | -------------------------------------- |
| Current believed situation                            | Situation Model                        |
| Reusable dynamics knowledge                           | World Model                            |
| Baseline reference for a derivation                   | Prediction / Counterfactual boundary   |
| Explicit hypothetical divergence from baseline        | Prediction / Counterfactual boundary   |
| Scenario-specific consequence derivation              | Prediction / Counterfactual            |
| Epistemic qualification of claims/results             | Epistemic Model                        |
| Utility/ranking of consequences                       | future Evaluation Engine               |
| Verification of derived consequences                  | future Verification Engine             |

"Boundary" in this table names a semantic responsibility, not an approved domain class.

### Conceptual flow

```text
opaque baseline reference
          |
          +---------------------------+
          |                           |
          v                           v
   no explicit divergence      explicit divergence(s)
          |                           |
          v                           v
      Prediction                Counterfactual
          \                           /
           \                         /
            +---- future dynamics ---+
                  consumption
                       |
                       v
             possible consequence(s)
                  [not yet defined]
```

This diagram represents semantic flow, not approved classes or calls. "Future dynamics
consumption" is a probable direction, not code created by this ADR. No cross-domain import is
authorized by this ADR beyond what ADR-0006 already authorizes.

## Not Decided Here

- concrete baseline reference type
- concrete divergence reference type
- a `Scenario` class
- an `Intervention` class
- a `Divergence` class
- request class shape
- one request vs. separate requests
- any discriminator enum
- consequence representation
- result cardinality
- empty-result semantics
- insufficient-knowledge representation
- probability
- confidence
- utility
- ranking
- verification
- temporal semantics
- dynamics representation
- World Model contracts
- a Prediction execution port
- a Counterfactual execution port
- any application service / coordinator
- provider/model integration
- context/situation materialization
- persistence

Additionally, the following remain open within the divergence semantics themselves:

- container type for divergences (tuple / frozenset / list)
- ordering of divergences
- duplicate-divergence semantics
- normalization of divergences
- conflict resolution between divergences
- composition semantics across divergences
- whether divergences are independent of one another
- the distinction between a divergence and a World Model condition/precondition
- the distinction between a divergence and an effect/consequence

## Consequences

**Positive:**

1. Gives Counterfactual an explicit semantic difference from Prediction.
2. Avoids treating hypothetical state as current belief.
3. Avoids abusing `SituationDelta` for hypothetical transitions.
4. Preserves `EpistemicModel`'s ownership of confidence, provenance, and conflict handling.
5. Keeps baseline and divergence references opaque.
6. Enables later request-shape design without requiring a structural Prediction/Counterfactual
   split.
7. Narrows the World Model consumer requirement.

**Tradeoff:**

1. No executable Prediction/Counterfactual capability exists yet.
2. Consequence semantics remain undefined.
3. No dynamics representation exists yet.
4. Scenario references still require a future resolution/materialization design.
5. World Model production remains blocked.

## Prediction / Counterfactual Implementation Gate

No production Prediction / Counterfactual domain contracts should be introduced until a
subsequent reviewed step decides:

1. request shape: one request or separate requests;
2. result cardinality and minimum consequence representation;
3. empty-result and insufficient-knowledge semantics;
4. whether any execution port is actually required.

The concrete baseline/divergence reference type and the question of how a derivation consumes
World Model dynamics knowledge remain important, but they are not substitutes for the four
criteria above — they belong to the general set of pending decisions this ADR defers, and to
the World Model Implementation Gate established by ADR-0006.

## World Model Gate Status

This ADR resolves, for the purpose of unblocking further design: the identity of the first
World Model consumer (Prediction / Counterfactual), baseline semantics, hypothetical
divergence semantics, and the rule that baseline/divergence references cross domain
boundaries opaquely.

This ADR does not resolve: the minimum reusable World Model dynamics representation, the
concrete World Model domain shape, the concrete reference type for any of these references, or
Prediction / Counterfactual's result semantics/cardinality. The production `world_model`
package therefore remains blocked, per ADR-0006's Implementation Gate.
