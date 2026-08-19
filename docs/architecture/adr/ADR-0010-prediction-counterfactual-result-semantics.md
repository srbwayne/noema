# ADR-0010: Prediction and Counterfactual Result Semantics

- Status: Accepted
- Date: 2026-08-18

## Context

ADR-0006 defines Prediction / Counterfactual as the component that applies world-model
knowledge to a particular situation or hypothetical scenario in order to derive scenario-specific
possible consequences.

ADR-0007 established that Prediction and Counterfactual differ by the presence of explicit
hypothetical divergences in the scenario: Prediction has zero; Counterfactual has one or more.

ADR-0008 established that every minimal derivation is scoped by exactly one derivation target —
an opaque reference plus a textual semantic statement.

ADR-0009 froze `PredictionRequest` and `CounterfactualRequest` as separate request types inside
the same frozen `Prediction / Counterfactual` structural component, and resolved item 1 of the
Prediction / Counterfactual Implementation Gate (request shape).

M0-13K (Result Contract Discovery) and M0-13L (Successful Result Cardinality Decision) resolved
item 2 of the same gate: result cardinality and minimum consequence representation. This ADR
records that resolution.

## Decision

### Shared result semantics

Prediction and Counterfactual share one and the same result contract, conceptually. This ADR
does not freeze two separate result types.

Rationale: no intrinsic property of a derived consequence indicates whether it was produced by a
Prediction derivation or a Counterfactual derivation. That distinction belongs entirely to the
request/scenario that produced the result, not to the result itself. Two separate request types
do not imply two separate result types — the reason `PredictionRequest` and `CounterfactualRequest`
were kept separate (ADR-0009: preventing an added divergence from silently reclassifying the
operation) is an input-side concern that has no output-side equivalent.

### No result discriminator

The result does not carry `mode`, `kind`, a prediction/counterfactual flag, `scenario_kind`, or
`derivation_kind`. The result does not need to re-carry the semantic operation type; the caller
already knows which request produced it.

### Result correlation

The minimal correlation information carried by the result is `target_ref`.

Rationale: `ReasoningRequest.problem_ref` correlates with `ReasoningOutcome.problem_ref`;
`PlanningRequest.goal_ref` correlates with `Plan.goal_ref`. In both precedents, exactly one field
— the operation's semantic-focus identifier — is mirrored from request to output; no other
request field is duplicated. `target_ref` is the functionally equivalent semantic correlation
anchor for Prediction / Counterfactual.

### target_ref semantics

`target_ref`, as carried by the result:

- correlates the result to the derivation target that produced it;
- remains opaque, exactly as it is on the request;
- is not runtime request identity;
- is not scenario identity;
- is not result identity.

This ADR does not create `result_id`, `request_id`, `derivation_id`, or `correlation_id`.

### No baseline duplication

`baseline_ref` does not belong to the minimal result. The caller that executed the operation
already holds the original request. The result is not turned into a self-sufficient copy of the
request.

### No divergence duplication

`divergence_refs` does not belong to the minimal result. Counterfactual scenario configuration
remains solely on the request.

### Minimum consequence representation

A minimal consequence is represented by a textual consequence statement.

It does not have: an opaque consequence identity; its own `target_ref`; its own `baseline_ref`;
its own `divergence_refs`; confidence; probability; utility; verification; or a causal rule.

### No consequence identity

No per-consequence identity is created. This ADR does not introduce `consequence_id`,
`consequence_ref`, a `UUID`, or a `TSID` for an individual consequence. No approved consumer
needs to reference one consequence individually.

### No Consequence value object

This ADR does not approve a dedicated `Consequence`, `PossibleConsequence`, or
`DerivedConsequence` class merely to wrap a string. The minimal contract does not carry
sufficient evidence — no invariant, reuse, or cardinality of its own beyond a bare textual
statement — to justify that wrapper. This does not forbid reconsidering the question in the
future if a new invariant or reuse need emerges.

### Consequence item semantics

Each returned consequence statement represents one consequence item. This is contract semantics,
not a linguistic guarantee: the domain does not claim it can prove, from the text alone, that a
statement contains exactly one atomic proposition. With opaque natural-language text, the minimal
runtime can validate string type and non-empty content; it cannot semantically decompose or
verify propositional atomicity without an additional, unapproved representation layer. This ADR
does not create a proposition parser, a semantic parser, or a structured-consequence AST.

### Successful cardinality

A successful, non-empty derivation over exactly one target may produce one or more consequence
statements. Conceptually: successful cardinality is `>= 1`.

### Exactly one target does not imply exactly one consequence

Exactly one derivation target does not imply exactly one consequence. The target delimits the
semantic subject, focus, or scope of the derivation; it does not delimit the number of effects
that may be derived over that scope.

### Multiple consequences

Multiple consequence statements may be returned for the same target when multiple effects are
representable. This does not require a new target, a new request, or a new scenario.

### Losslessness rationale

An exactly-one output shape would pressure the system to concatenate independent consequences
into one compound statement, to discard one of several real consequences, or to introduce
additional structure later as a breaking change. A one-or-more shape represents both a single
consequence and multiple consequences without structural loss in either case.

### Non-exhaustiveness

Multiple returned consequence statements do not constitute an exhaustive list of everything that
could happen. This ADR does not introduce "all consequences," a "complete consequence set," an
"exhaustive forecast," or a closed-world assumption. One-or-more means only: the consequences
that were derived by this operation.

### No relationship semantics

A collection of consequence statements does not imply any relationship between its items. It
does not mean AND, OR, alternative, simultaneous, mutually exclusive, branch, dependency, or
causal relation. Relationship semantics among consequences remain deferred.

### No ordering semantics

No rank, priority, importance, causal precedence, or temporal precedence is assigned to the
future position of a consequence item. M0-13K already found an absence of ordering semantics in
this domain; this ADR does not reopen it.

### Representation duplicate finding

Exactly identical textual representations may, in the future, be treated as representation
duplicates. This ADR does not attempt to detect semantic equivalence or paraphrase equivalence.
The concrete validation mechanics are not frozen here, because they may depend on the concrete
container decided under Gate 3.

### Concrete container deferred

This ADR does not freeze `tuple[str, ...]`, `frozenset[str]`, `list[str]`, or any other concrete
container as the result's consequence field. The decision frozen here is semantic: successful
cardinality is one-or-more. The concrete field shape awaits Gate 3, because empty-result
semantics may influence which concrete representation is chosen.

### Empty result remains undecided

This ADR does not decide whether zero consequences can exist within the same result type, nor
whether an empty collection, `None`, an optional field, or a separate result state represents
that case. This belongs entirely to Gate 3.

### Insufficient knowledge remains undecided

This ADR does not decide `InsufficientKnowledge`, `Unknown`, `UnableToPredict`, `NeedsInformation`,
`NoEffect`, `Impossible`, or any corresponding status or error.

### No result status

This ADR does not create or approve `PredictionStatus`, `CounterfactualStatus`,
`DerivationStatus`, or `ResultStatus`. Status depends on Gate 3.

### Probability

Probability, likelihood, chance, and log-probability are not included in the minimal result.
This ADR leaves probability deferred; it does not definitively classify it as belonging to
Epistemology, because no existing ADR has done so either. Confidence, distinct from probability,
continues to clearly belong to the Epistemic Model.

### Confidence

Confidence is not included. Epistemic qualification belongs to the Epistemic Model.

### Utility / ranking

Utility, rank, priority, and score are not included. Their ownership belongs to the future
Evaluation Engine.

### Verification

`verified` and `verification_status` are not included. Their ownership belongs to the future
Verification Engine.

### Temporal semantics

Horizon, timestamp, `expected_at`, `valid_until`, and time offset are not automatically included.
Temporal semantics remain deferred.

### Causal explanation

Cause, mechanism, causal path, rule references, and transition references are not included. The
result does not leak World Model internals.

### World Model boundary

World Model remains reusable dynamics knowledge. A Prediction / Counterfactual result remains
scenario-specific derived consequences. The result does not expose any future internal
representation of the World Model.

### Epistemic boundary

A result is not automatically an `EpistemicClaim`. A future coordination boundary may translate a
derived consequence into an `EpistemicClaim`. This ADR does not directly include
`EpistemicStatus`, `EpistemicSource`, evidence references, or `conflicting_claim_ids`.

### Reasoning boundary

A result is not a `ReasoningOutcome`. This ADR does not include `ReasoningStatus`,
`reason_summary`, or `information_needs` by symmetry with Reasoning.

### Result name

This ADR freezes the semantics of a single shared result contract. It does not need to freeze the
concrete future class name, because spelling evidence is not yet sufficient. Candidate names such
as `PredictionCounterfactualResult`, `DerivationResult`, or `PredictionResult` are not approved by
aesthetic preference. Naming remains deferred.

### Result type count

Despite naming remaining deferred, this ADR freezes that the future minimal design has one shared
result type — not separate `PredictionResult` and `CounterfactualResult` classes.

### Dependency impact

No new cross-domain dependency is necessary for the minimal semantics of the result. The current
architecture guard (`test_prediction_counterfactual_has_only_allowed_noema_dependencies`) does not
need to be expanded by this ADR.

### Item 2 gate

Prediction / Counterfactual Implementation Gate item 2 — result cardinality and minimum
consequence representation — is **RESOLVED** by this ADR. Its constituent decisions: one shared
result; `target_ref` correlation; textual consequence representation; no consequence identity;
successful cardinality one-or-more; no exhaustiveness; no relationship semantics.

### Remaining gates

Item 3 — empty-result and insufficient-knowledge semantics — remains **NOT RESOLVED**.

Item 4 — execution-port requirement — remains **NOT RESOLVED**.

### World Model gate

World Model production remains blocked by ADR-0006. This ADR does not create a dynamics
representation.

## Not Decided Here

- concrete result class name
- concrete consequence container
- empty-result validity
- insufficient-knowledge representation
- result status
- result validation errors
- execution port
- application boundary
- provider/model adapter
- probability semantics
- temporal semantics
- relationship semantics among consequences
- semantic equivalence of textual consequences
- scenario identity
- runtime tracing identity
- persistence
- World Model representation

## Consequences

**Positive:**

- The request is not duplicated inside the result.
- The same result semantics serve both Prediction and Counterfactual.
- Multiple legitimate, independent effects can be represented without loss.
- No compound consequence statement is forced by the contract's shape.
- No consequence identity is invented without an evidenced consumer.
- Epistemic, Evaluation, and Verification ownership boundaries are preserved.
- The result remains provider-independent.
- Gate 2 closes independently from Gate 3 and Gate 4.

**Tradeoff:**

- The result does not yet have a concrete class shape.
- Zero-result semantics remain unknown.
- Natural-language semantic atomicity is not machine-verifiable by this contract.
- The relationship among multiple consequences remains undefined.
- Probability and temporal semantics remain deferred.
- No executable Prediction/Counterfactual exists yet.

## ADR Relationship

ADR-0010 complements ADR-0005, ADR-0006, ADR-0007, ADR-0008, and ADR-0009. It supersedes none of
them.
