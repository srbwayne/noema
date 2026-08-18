# ADR-0008: Derivation Target Semantics

- Status: Accepted
- Date: 2026-08-17

## Context

ADR-0005 freezes `Prediction / Counterfactual` as a single nominal component.

ADR-0006 defines `Prediction / Counterfactual` as scenario-specific consequence derivation.

ADR-0007 defined baseline and explicit hypothetical divergences as the semantic axes of the
scenario: Prediction has zero explicit divergences; Counterfactual has one or more.

M0-13E discovered that baseline plus divergences are not sufficient to distinguish two
different derivations over the same scenario. Conceptually, given the same baseline and the
same divergence:

- "What happens to X?"
- "What happens to Y?"

are two semantically distinct operations. M0-13F confirmed OPTION 1: an explicit derivation
target semantics is necessary.

## Decision

### Derivation target

A **derivation target** identifies and describes the semantic focus whose possible
consequences are being derived. It answers, conceptually, "what is this derivation about?" or
"what consequence scope is being investigated?" No single grammatical form is fixed: a
derivation target may be expressed as a question-like framing or as a descriptive consequence
scope, provided it clearly expresses the semantic focus.

### A target is required

Every minimal Prediction / Counterfactual derivation must be scoped by exactly one derivation
target. The minimal contract therefore does not include a fully unscoped operation equivalent
to "derive any or all possible consequences of this scenario." This does not declare that open
exploration can never exist; it declares only that open-ended, unrestricted derivation is
outside the minimal Prediction / Counterfactual V1 contract.

### Exactly one target

The minimal semantic contract has exactly one derivation target. This ADR does not define
multi-target derivation. If multiple targets are needed in the future, that cardinality will
require evidence and explicit review. This ADR does not decide whether multiple targets, if
ever introduced, would be independent or composed.

### Two semantic aspects

Conceptually:

```text
Derivation Target = opaque reference + textual semantic statement
```

This does not approve a `DerivationTarget` class or any field names. It is semantics, not a
type declaration.

### Opaque target reference

The target has an opaque reference used for identity/semantic correlation. The reference:

- must be opaque to the Prediction / Counterfactual domain;
- must not require dereferencing by the domain itself;
- must be represented conceptually as a non-empty identity;
- must not be interpreted as request-instance identity.

Existing repository precedent for this shape includes `problem_ref`, `goal_ref`, and
`subject_ref`.

### Concrete reference type

M0-13E and M0-13F found strong evidence that this repository represents opaque external
references as a non-empty string. This ADR records that the current repository precedent
strongly supports a non-empty `str` for opaque target references. This ADR does not approve a
`TargetRef` value object, `UUID`, `TSID`, `URI`, a workspace item, or a task identifier as the
semantic owner of this reference.

### Textual statement

The target also has a textual semantic statement describing the focus/question/scope of the
requested derivation. It is not a provider prompt, a system message, a reasoning strategy, an
execution instruction, an expected result, or a verified proposition.

### Statement grammar is not fixed

The statement is not required to be literally phrased as a question. Semantically equivalent
forms such as "What happens to latency?" and "effect on completion latency" must both remain
possible, provided they clearly express the semantic focus. This ADR does not create a query
language or a DSL.

### String invariants

For both the opaque reference and the textual statement, the minimal semantics are: a string;
non-empty after a strip validation; the exact value preserved; no coercion; no normalization.
This ADR does not introduce a maximum length, a language restriction, case normalization, trim
mutation, a template, JSON, or prompt syntax.

### Reference and statement are not accidental redundancy

Reference and statement serve distinct functions: the reference is a stable, opaque semantic
identity/correlation anchor; the statement is a locally available semantic description needed
without dereferencing. The domain does not need to resolve the reference to understand the
target semantically.

### Reference-statement correspondence is not verified

The Prediction / Counterfactual domain cannot verify that the opaque reference and the textual
statement point to externally equivalent content. A future request contract may validate type
and non-emptiness, but not external semantic correspondence, without an explicitly approved
external boundary. This ADR does not create that resolver.

### Target is not request identity

A target reference is not a request id. Executing the same baseline, the same divergences, and
the same target again represents the same semantic operation requested again. Tracing or
execution identity, if ever needed, belongs to a separate concern. This ADR does not create a
`request_id`.

### Target is not baseline

Baseline answers "relative to what scenario?" Target answers "what are we trying to derive
about that scenario?" Target does not transfer ownership of `SituationModel`.

### Target is not divergence

Divergence answers "what is explicitly assumed to differ from the baseline?" Target answers
"what semantic focus is being investigated?" A target is not a hypothetical divergence.

### Target is not result

Target is request semantics; a result/consequence is derived output semantics. A target is not
a predicted consequence. This ADR does not create `Consequence`, `PredictionResult`, or
`PredictionOutcome`.

### Target is not goal

Planning's goal expresses an intended/desired state. A derivation target expresses the focus of
a derivation. Prediction / Counterfactual does not gain desirability, utility, or an
optimization objective by having a target. This ADR does not approve reusing `goal_ref` or
`goal_statement` as names for this concept.

### Target is not a reasoning problem

Reasoning's problem describes something to be reasoned about/resolved. A derivation target
describes the semantic focus of a consequence derivation. This ADR does not turn Prediction /
Counterfactual into a mode of the Reasoning Engine, and does not approve reusing
`ReasoningRequest`, `problem_ref`, or `problem_statement` as this concept's contract.

### Target is not an epistemic proposition

A derivation target is not automatically a hypothesis, a claim, a proposition to verify, or an
`EpistemicClaim`. A target does not have confidence, status, provenance, evidence, or
verification state.

### QUESTION enums are unrelated

`SituationEntryKind.QUESTION` and `CognitiveItemKind.QUESTION` classify content belonging to
their own respective models. Neither is the derivation-target contract. This ADR does not
authorize importing `situation` or `workspace` to represent a target.

### InformationNeed precedent, not reuse

`InformationNeed` demonstrates an existing precedent for a smaller-granularity pairing —
`subject_ref` plus `description` — without prescribing a method of execution. This ADR does not
reuse `InformationNeed` as the target; `InformationNeed` belongs to the Reasoning domain.

### Correlation precedent

Reasoning's `Request.problem_ref` correlates with `Outcome.problem_ref`; Planning's
`PlanningRequest.goal_ref` correlates with `Plan.goal_ref`. These existing semantic-operation
boundaries preserve correlation with the semantic subject/goal of the operation, supporting the
presence of an opaque target reference. This ADR does not define future Prediction result
fields.

### Provider independence

Target semantics are entirely provider-independent. They do not depend on an LLM, the model
router, `ModelExecutionEngine`, Ollama, a prompt, tokenization, `STRUCTURED_OUTPUT`, or a JSON
schema.

### Materialization

The target statement does not resolve materialization of the baseline, divergences, or World
Model knowledge. Those references remain opaque. No materializer/resolver is created.

### ContextPackage excluded

This ADR does not introduce `ContextPackage` into a future Prediction / Counterfactual request.
M0-13E and M0-13F found no evidence for that coupling.

### CognitiveBudget excluded

This ADR does not introduce `CognitiveBudget` as semantic content of the target or the request.
Budget remains an execution/orchestration concern until future evidence indicates otherwise.

### Target value object deferred

This ADR does not freeze a `DerivationTarget` class. Although reference plus statement form a
coherent concept, the repository has precedent for both flattened fields and nested item
contracts. The choice between an embedded pair and a dedicated value object remains deferred
until the request-shape decision.

### Field names deferred

This ADR does not freeze `target_ref`, `target_statement`, `derivation_ref`,
`derivation_statement`, `question_ref`, `question_statement`, or any other API name.

### Terminology

"Derivation target" may be used as the conceptual name of this architectural decision. This
does not mean a future class or field must be named `DerivationTarget`, `target_ref`, or
`target_statement`.

### Same semantics for Prediction and Counterfactual

Prediction and Counterfactual use the same derivation-target semantics. No evidence supports a
different rule for a Prediction target versus a Counterfactual target. The distinction between
the two continues to be explicit divergence cardinality.

### One request vs. two remains deferred

This ADR does not decide between a single request whose intent is inferred by divergence
cardinality and separate `PredictionRequest` / `CounterfactualRequest` classes. A derivation
target works under either shape.

### Divergence container remains deferred

This ADR does not decide container type, ordering, duplicate semantics, normalization,
conflicts, composition, or independence for hypothetical divergences.

### Result semantics remain deferred

This ADR does not decide a single result, multiple consequences, an empty result, insufficient
knowledge, a structured consequence, a text result, or a hypothetical state.

### Execution port remains deferred

This ADR does not create or approve `PredictionExecutor`, `CounterfactualExecutor`,
`PredictionEngine`, `CounterfactualEngine`, or any execution port.

### World Model remains blocked

This ADR does not resolve the minimum reusable dynamics representation, the World Model domain
shape, dynamics rules, conditions/effects, or materialization. The production `world_model`
package remains blocked by ADR-0006.

### Ownership table

| Concern                                              | Owner                                 |
| ----------------------------------------------------- | -------------------------------------- |
| Current believed situation                            | Situation Model                        |
| Reusable dynamics knowledge                           | World Model                            |
| Baseline reference                                    | Prediction / Counterfactual boundary   |
| Explicit hypothetical divergences                     | Prediction / Counterfactual boundary   |
| Derivation target semantics                           | Prediction / Counterfactual boundary   |
| Scenario-specific consequence derivation              | Prediction / Counterfactual            |
| Epistemic qualification                               | Epistemic Model                        |
| Utility/ranking                                       | future Evaluation Engine               |
| Verification                                          | future Verification Engine             |

"Boundary" in this table names a semantic responsibility, not an approved domain class.

### Conceptual flow

```text
             derivation request semantics

           scenario                    semantic focus
              |                             |
       baseline reference            derivation target
              |                     /                  \
       divergence(s)        opaque reference      textual statement
              \                     /
               \                   /
                +-----------------+
                        |
                        v
           Prediction / Counterfactual
                        |
                        v
              possible consequence(s)
                 [not yet defined]
```

This diagram is conceptual only. No class, package, or call graph is frozen. The result
remains undefined. World Model dynamics consumption remains separately gated.

### Effect on the request gate

This ADR resolves the primary gap M0-13E discovered: baseline plus divergences alone did not
suffice to express a complete derivation. It is now semantically defined as scenario plus
exactly one derivation target. Request shape is still not fully frozen, because one request vs.
separate requests, embedded pair vs. a target object, divergence container semantics, and final
field spelling all remain open. Production Prediction / Counterfactual request contracts
therefore remain blocked.

## Not Decided Here

- exact target field names
- a dedicated `DerivationTarget` class
- embedded vs. nested target representation
- one request vs. separate requests
- divergence container
- divergence ordering
- divergence duplicate semantics
- divergence conflict/composition semantics
- a `PredictionRequest` class
- a `CounterfactualRequest` class
- result representation
- result cardinality
- empty-result semantics
- insufficient-knowledge semantics
- execution port
- application boundary
- World Model dynamics
- context/situation materialization
- provider/model adapter
- persistence
- request/execution tracing identity

## Consequences

**Positive:**

- Distinguishes derivations that share the same scenario.
- Avoids unbounded "derive everything" semantics in the minimal V1 contract.
- Provides a locally readable semantic focus without dereferencing.
- Preserves an opaque correlation identity.
- Remains provider-independent.
- Does not import situation/workspace/reasoning/planning objects.
- Allows the request-shape decision to resume with the missing semantic axis resolved.

**Tradeoff:**

- Exact API spelling remains undecided.
- One-vs-two request remains undecided.
- Target representation (flatten vs. object) remains undecided.
- No result contract exists.
- No executable Prediction/Counterfactual exists.
- World Model remains blocked.

## ADR Relationship

ADR-0008 complements ADR-0005, ADR-0006, and ADR-0007. It supersedes none of them.
