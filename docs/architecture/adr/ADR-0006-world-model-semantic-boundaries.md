# ADR-0006: World Model Semantic Boundaries

- Status: Accepted
- Date: 2026-08-16

## Context

ADR-0005 freezes, separately, among other components:

- Situation Model
- Planner
- World Model
- Prediction / Counterfactual
- Epistemic Model

ADR-0005 freezes the structure only; it does not specify or implement these components.

The M0-13A read-only audit (World Model Contract Discovery) found:

- `SituationModel` already represents the agent's current believed situation, as a versioned,
  delta-applied snapshot.
- `SituationDelta` alters a specific, concrete, versioned `SituationModel` snapshot; its
  `base_version`, `occurred_at`, and entry-identity checks are entangled with that concrete
  snapshot.
- `EpistemicModel` already owns confidence, provenance, conflict handling, and an
  `EpistemicStatus.PREDICTION` classification for claims.
- `SituationEntry` and `ContextSlice` reference external content only through opaque string
  references (`content_ref`); no context- or situation-materialization boundary exists.
- No production `WorldModel` representation exists anywhere in the codebase.
- No provider-neutral structured domain decoding exists; `ModelExecutionRequest` and
  `ModelExecutionResult` carry plain text only, and `ModelCapability.STRUCTURED_OUTPUT` is a
  declared capability label with no execution mechanism behind it.

Creating a World Model contract without first fixing these boundaries would risk duplicating
`SituationModel` or `EpistemicModel`, or pre-empting the not-yet-designed
Prediction / Counterfactual capability, with speculative code.

## Decision

### Core distinction

Situation Model, World Model, and Prediction / Counterfactual are distinct responsibilities:

- **Situation Model** represents what the agent currently believes is the situation.
- **World Model** represents reusable knowledge about how referenced entities, states, events,
  constraints, or conditions may relate or change.
- **Prediction / Counterfactual** applies world-model knowledge to a particular situation or
  hypothetical scenario in order to derive possible consequences.

### World Model is not current state

World Model must not own or duplicate the agent's current believed situation. It must not
replace or duplicate `SituationModel`, `SituationEntry`, `SituationDelta`, situation
versioning, current entries, or current-snapshot mutation. Current state continues to belong
to the Situation Model.

### World Model is not Prediction

World Model must not itself represent a concrete prediction or counterfactual outcome. World
Model describes reusable knowledge about possible relations and changes; Prediction /
Counterfactual uses that knowledge in a specific scenario. Consequently, World Model must not
have, as its fundamental contract, a predicted state, predicted outcome, counterfactual
result, scenario result, or forecast status.

### World Model is not Epistemic Model

World Model must not duplicate epistemic qualification. Confidence, provenance, epistemic
status, contradiction/conflict tracking, and prediction classification remain epistemic
responsibilities. A future component may relate World Model knowledge to epistemic claims, but
World Model must not incorporate `EpistemicClaim` as internal state merely to copy those
responsibilities.

### Opaque reference boundary

Cross-component references between World Model and other cognition components must use opaque
identifiers/references at the domain boundary, unless a future ADR explicitly authorizes a
stronger dependency. Consequently, future world-model domain contracts must not directly own
`SituationModel`, `SituationEntry`, `EpistemicClaim`, `Plan`, `PlanStep`, `ReasoningRequest`,
or `ReasoningOutcome` as a form of structural coupling. They may, in the future, carry opaque
references to external concepts, with the concrete semantics defined by the corresponding
contract.

This ADR does not decide the concrete reference type (`str`, `UUID`, `TSID`, a value object, an
`EntityRef`, a `StateRef`, or otherwise). It decides only that World Model references external
concepts **by opaque identity**, rather than by direct cross-domain object ownership. The
concrete reference type is deferred until a real consumer exists.

### Cross-domain dependency

The World Model domain must initially remain independent from `situation`, `epistemology`,
`planning`, `reasoning`, and `model_router`. A future application/integration layer may
coordinate these components. Direct domain-to-domain dependency between them requires concrete
evidence and explicit architectural review.

### SituationEntryKind.CAUSAL_RELATION

`SituationEntryKind.CAUSAL_RELATION` currently classifies an opaque `content_ref` present in
the current situation. It does not define causal-rule structure, antecedent, consequence,
direction, probability, transition semantics, rule execution, or prediction.
`CAUSAL_RELATION` must not be treated as the World Model itself. This ADR does not remove or
redefine it.

### SituationDelta

`SituationDelta` models an observed/applicable change against a specific versioned
`SituationModel`. Its `base_version`, `occurred_at`, and entry-identity validation bind it to a
concrete situation. `SituationDelta` must not be reused as the canonical representation of a
hypothetical World Model transition. This does not preclude a future Prediction component from
producing something that is later translated into a `SituationDelta` after observation or
acceptance — but that translation is outside this ADR.

### World Model responsibility

The World Model owns reusable dynamics knowledge — knowledge about possible relations or
change behavior that is independent from any one concrete current snapshot. This ADR does not
decide whether that knowledge is represented as transition rules, a causal graph, constraints,
state patterns, or a hybrid representation.

### World Model is not a simulator

Simulation of a concrete scenario belongs with the future Prediction / Counterfactual
capability, not the minimal World Model domain foundation. A Simulator is not part of the
normative World Model.

### Planner relationship

Planner may eventually consume prediction/world-model capabilities through explicit
boundaries. Planner must not directly own World Model state. World Model must not generate
`Plan` as its fundamental result. `Plan` and `PlanStep` continue to belong to the planning
domain.

### Reasoning relationship

Reasoning strategies such as `CAUSAL` and `COUNTERFACTUAL` do not make `ReasoningEngine` the
owner of World Model knowledge. Reasoning may eventually consume these capabilities through
explicit application/integration boundaries. World Model must not return `ReasoningOutcome` as
its fundamental domain representation.

### Model Router relationship

World Model is provider-independent. No model/provider technology belongs in its domain. The
existence of `ModelCapability.STRUCTURED_OUTPUT` does not imply that World Model must be
model-generated. Current model execution transports text only at its public execution
contract. Any future model-backed World Model adapter requires its own approved translation
boundary.

### Context materialization

World Model must not assume it can dereference `ContextSlice.content_ref` or
`SituationEntry.content_ref` by itself. Materialization/resolution is a separate capability
that does not currently exist as an approved contract.

### Ownership table

| Concern                                            | Owner                          |
| --------------------------------------------------- | ------------------------------- |
| Current believed situation                          | Situation Model                 |
| Current situation mutation                           | Situation Model                 |
| Reusable dynamics knowledge                          | World Model                     |
| Scenario-specific consequence derivation             | Prediction / Counterfactual     |
| Confidence / provenance / epistemic status           | Epistemic Model                 |
| Goal decomposition into steps                        | Planner                         |
| Reasoning strategy execution                         | Reasoning Engine                |
| Model/provider selection and execution               | Model Router                    |

### Dependency direction

```text
               application / integration
                 /      |       \
                v       v        v
          Situation  World    Epistemic
            Model    Model      Model
                         |
                         v
               future Prediction /
                 Counterfactual
```

This diagram represents ownership and boundaries. It does not freeze classes or calls.
Prediction consuming World Model is a probable future direction, not code created by this ADR.
No cross-domain import is authorized by this ADR beyond what already exists.

## Not Decided Here

- `WorldModel` class shape
- package contents
- state representation
- `EntityRef` / `StateRef`
- transition-rule representation
- causal-graph representation
- preconditions
- effects
- probability
- utility
- temporal model
- simulation request/result
- Prediction contracts
- Counterfactual contracts
- persistence
- ports
- application services
- model-backed adapters
- context materialization
- structured-output decoding
- World Model learning/update behavior

## Consequences

**Positive:**

- Avoids duplicating `SituationModel`.
- Preserves `EpistemicModel` ownership of confidence, provenance, and conflict handling.
- Prevents Prediction from leaking into World Model.
- Preserves domain isolation.
- Permits multiple future World Model representations.
- Remains provider-independent.

**Tradeoff:**

- No usable World Model runtime exists yet.
- Concrete contracts remain deferred.
- Future Prediction design will be required before simulation can exist.
- Cross-component coordination belongs outside isolated domain packages until explicitly
  approved.

## Implementation Gate

No production `world_model` package should be introduced until a subsequent reviewed step
identifies a concrete first consumer and can justify:

1. the minimum reusable dynamics representation;
2. the reference type required by that consumer;
3. whether any cross-domain dependency is actually necessary;
4. which invariants belong to World Model rather than Prediction or Epistemology.
