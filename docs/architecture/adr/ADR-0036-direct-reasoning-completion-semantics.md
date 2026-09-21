# ADR-0036: DIRECT Reasoning Completion Semantics

- Status: Accepted
- Date: 2026-09-20

## Context

`ReasoningOutcome` and `ReasoningStatus` are canonical Cognition domain contracts.
`ReasoningStatus` has four members -- `COMPLETED`, `PARTIAL`, `NEEDS_INFORMATION`, and
`UNRESOLVED` -- and its docstring describes "the semantic completeness of a reasoning outcome".
The structural matrix relating each status to the presence of `conclusion` and
`information_needs` is complete, and `ReasoningOutcome` validates it itself:

```text
COMPLETED          -> conclusion present, information_needs empty
PARTIAL            -> conclusion present, information_needs non-empty
NEEDS_INFORMATION  -> conclusion absent,  information_needs non-empty
UNRESOLVED         -> conclusion absent,  information_needs empty
```

No previously accepted ADR defines which semantic event selects any of these rows. Earlier ADRs
mention `ReasoningOutcome` only as precedent or as a boundary statement -- for example ADR-0011,
ADR-0014, ADR-0022, and ADR-0032.

`ModelExecutionResult` is the success-only result of executing a model resource. It carries a
`ModelResource` and a non-empty `output_text`, and its own contract states that it carries no
status, error, retry, or provider metadata. It has no `ReasoningStatus` and no
reasoning-completeness authority.

`ModelReasoningExecutor`, the first concrete `ReasoningExecutor`, currently maps every
successful DIRECT model result to:

```text
status            = ReasoningStatus.COMPLETED
conclusion        = result.output_text
reason_summary    = "direct reasoning"
information_needs = ()
```

That mapping was introduced together with the executor and has no accompanying architectural
decision. It is minimal and, until this ADR, semantically underdefined: nothing stated what
`COMPLETED` asserts for a DIRECT outcome, so nothing could state whether the mapping is
legitimate.

This ADR records the narrow decision that defines `COMPLETED` for DIRECT and nothing beyond it.

## Decision

### Completion semantics: recorded conclusion, DIRECT only

```text
DIRECT_REASONING_COMPLETION_SEMANTICS = RECORDED_CONCLUSION
DIRECT_COMPLETION_SEMANTICS_SCOPE     = DIRECT_ONLY
DIRECT_COMPLETION_TARGET              = DIRECT_REASONING_OUTCOME_PAYLOAD
```

For a `ReasoningStrategy.DIRECT` outcome, `ReasoningStatus.COMPLETED` means that the concrete
DIRECT reasoning executor recorded a valid non-blank conclusion for the operation and recorded
no `InformationNeed` values in that outcome. It is completeness of the DIRECT `ReasoningOutcome`
payload under the status/payload matrix above.

`COMPLETED` for DIRECT is not a provider-execution status, not proof that the problem was
resolved, not a truth assessment, not verification, not a confidence statement, not a claim of
epistemic sufficiency or exhaustiveness, and not a statement about task or general
cognitive-operation success.

### What "recorded" means

"Recorded" means that the executor placed the payload into the `conclusion` field as its
produced conclusion. It does not mean that the payload was independently validated, endorsed as
true, verified, confidence-scored, or accepted by an Evaluation or Verification component.

### Conclusion semantics

```text
REASONING_CONCLUSION_SEMANTIC = DIRECT_EXECUTOR_RECORDED_CONCLUSION
```

For DIRECT, `ReasoningOutcome.conclusion` is the conclusion recorded by the DIRECT executor. A
non-empty `ModelExecutionResult.output_text` is structurally sufficient for the current DIRECT
executor to place that exact value into the `conclusion` field.

This does not establish, as a generic `model_router` rule, that a successful model execution
implies a completed reasoning outcome. The mapping from a model-execution result to a
`ReasoningOutcome` is a Cognition-owned mapping performed by the Reasoning executor.

### Technical and semantic boundary

```text
MODEL_ROUTER_OWNS_REASONING_COMPLETENESS = NO
PROVIDER_OWNS_REASONING_COMPLETENESS     = NO
```

`model_router` reports model-execution facts. Cognition owns reasoning semantics. Technical
provider success is not itself reasoning completion.

### What COMPLETED does not assert

```text
COMPLETED_ASSERTS_TRUTH                 = NO
COMPLETED_ASSERTS_VERIFIED              = NO
COMPLETED_ASSERTS_CONFIDENCE            = NO
COMPLETED_ASSERTS_EXHAUSTIVENESS        = NO
COMPLETED_ASSERTS_EPISTEMIC_SUFFICIENCY = NO
```

- **Truth.** A recorded conclusion may be false. This ADR does not evaluate correctness.
- **Verification.** Verification remains separately owned. This ADR adds no `verified`,
  `verification_status`, judgment, or polarity to `ReasoningOutcome`.
- **Confidence.** This ADR introduces no confidence value or threshold.
- **Exhaustiveness.** A DIRECT conclusion need not represent exhaustive reasoning.
- **Epistemic sufficiency.** Epistemic sufficiency is not inferred from the absence of
  `InformationNeed` values.

### Empty information needs

```text
COMPLETED_EMPTY_NEEDS_MEANING = NO_NEEDS_PRODUCED
```

An empty `information_needs` tuple on a `COMPLETED` DIRECT outcome means that the outcome
records no information needs. It does not mean that the system established that no missing
information exists. A producer that has no means of expressing information needs makes no claim
about their absence.

This ADR does not define an `InformationNeed.subject_ref` namespace, information-need discovery,
or information-need completeness.

### Refusal and uncertainty content

Under this narrow DIRECT contract, a non-blank conclusion expressing uncertainty, inability, or
refusal may still be a valid `COMPLETED` outcome if the executor records it as the DIRECT
conclusion and records no information needs. `COMPLETED` asserts nothing about the usefulness of
the recorded conclusion.

This ADR does not require every future executor to classify such content as `COMPLETED`. A
future producer with separately approved semantic authority may produce another valid status.
This ADR introduces no text parsing and requires none.

### Relation to the other statuses

`ReasoningStatus.UNRESOLVED` is a legitimate semantic `ReasoningOutcome` status, not a technical
failure. ADR-0032 states that it is reserved for genuine semantic reasoning incompleteness after
an attempt. This ADR preserves that meaning and does not redefine it; it defines only DIRECT
`COMPLETED`. The two remain distinguishable: `COMPLETED` requires a recorded conclusion, and
`UNRESOLVED` requires that there be none.

```text
PARTIAL_SELECTION_SEMANTICS           = UNRESOLVED
NEEDS_INFORMATION_SELECTION_SEMANTICS = UNRESOLVED
```

`PARTIAL` remains "conclusion present, information_needs non-empty", and `NEEDS_INFORMATION`
remains "conclusion absent, information_needs non-empty". This ADR does not define what event
selects either, and nothing in the `COMPLETED` definition makes either status impossible.

### Scope: DIRECT only

```text
SPECIALIZED_STRATEGY_COMPLETION_SEMANTICS = UNRESOLVED
```

These semantics are not generalized to `DECOMPOSITION`, `HYPOTHESIS_TESTING`, `CAUSAL`,
`COMPARATIVE`, `SEARCH`, `COUNTERFACTUAL`, `CRITIQUE`, `TOOL_ASSISTED`, or `MULTI_MODEL`.

### Outcome-production responsibility

```text
REASONING_OUTCOME_PRODUCTION_OWNER = REASONING_EXECUTOR
CURRENT_DIRECT_OUTCOME_PRODUCER    = ModelReasoningExecutor
```

A concrete `ReasoningExecutor` produces the `ReasoningOutcome` for the strategy it executes;
`ReasoningEngine` validates type and request correlation and returns a valid outcome unchanged.
This does not mean that an executor owns the semantic definition of `ReasoningStatus`. That
definition remains Cognition-owned, and an executor's outcomes are expected to conform to the
semantics Cognition has decided -- currently, for DIRECT `COMPLETED`, this ADR.

`ModelReasoningExecutor` is the current DIRECT producer in the current runtime topology. That is
not permanent ownership of DIRECT, and this ADR does not prohibit another DIRECT executor.

### Related mapping fields

```text
REASON_SUMMARY_SEMANTICS                                = UNRESOLVED
MODEL_SELF_REPORT_COMPLETENESS_AUTHORITY                = UNRESOLVED
PROVIDER_NEUTRAL_STRUCTURED_REASONING_RESULT_CONTRACT   = NONE
STRUCTURED_MODEL_OUTPUT_REQUIRED_FOR_DIRECT_COMPLETION  = NO
HEURISTIC_TEXT_TO_REASONING_STATUS_AUTHORIZED           = NO
HEURISTIC_TEXT_TO_INFORMATION_NEEDS_AUTHORIZED          = NO
```

- **`reason_summary`.** The existing value `"direct reasoning"` may remain the current
  structurally valid value. This ADR does not define `reason_summary` semantics.
- **Model self-report.** This ADR requires no model self-report and decides no authority for one.
- **Structured output.** This ADR creates no schema and requires no structured model output.
  `ModelCapability.STRUCTURED_OUTPUT` remains whatever capability authority already exists.
- **Text parsing.** This ADR does not authorize deriving a status or information needs by
  heuristically parsing model output text. Recorded-conclusion semantics requires no regular
  expression, keyword classifier, hidden parser, or content heuristic.

### Technical failure boundary

Under the current accepted `ReasoningExecutor` architecture, a technical execution failure is
reported through the exception boundary and is not a `ReasoningStatus` emitted by that failed
execution. Provider and model technical failures remain `ReasoningExecutionError`, and budget
admission and deadline failures remain their existing domain errors. This ADR states the current
boundary and does not impose a universal prohibition on any future architecture.

### Current mapping compatibility and consequences

```text
CURRENT_DIRECT_MAPPING_COMPATIBLE                 = YES
CURRENT_DIRECT_MAPPING_DISPOSITION                = SEMANTICALLY_VALID
CURRENT_DIRECT_RUNTIME_COMPATIBLE_WITH_ADR_0036   = YES
DIRECT_COMPLETION_DECISION_REQUIRES_SOURCE_CHANGE = NO
SOURCE_DOC_ALIGNMENT_REQUIRED                     = NO
```

The current DIRECT executor already produces exactly the minimal shape this decision permits:
a recorded conclusion, no recorded information needs, and a structurally valid summary. No
additional source, test, or existing-document alignment change is required beyond recording
this ADR, and no behavioral implementation follows from it.

### Preserved boundaries

```text
GENERAL_COGNITIVE_OPERATION_CONTRACT                                 = UNRESOLVED
REASONING_OUTCOME_SUFFICIENT_AS_GENERAL_COGNITIVE_OPERATION_RESULT   = UNRESOLVED
OUTCOME_RETENTION_TARGET_AUTHORITY                                   = NONE
OUTCOME_RETENTION_READY                                              = NO
EPISTEMIC_RUNTIME_OWNER                                              = NONE
MODE_AXIS_DISPOSITION                                                = PARKED_PENDING_NEW_EVIDENCE
MODE_SEMANTIC_ORDER                                                  = UNRESOLVED
USAGE_FRONTIER_DISPOSITION                                           = REMAIN_PARKED
COGNITIVE_BUDGET_ENFORCED_DIMENSIONS                                 = max_llm_calls, max_time
FULL_COGNITIVE_BUDGET_RUNTIME_ENFORCEMENT_IMPLEMENTED                = NO
```

This ADR defines only DIRECT `ReasoningOutcome` completion semantics. It does not decide that
`ReasoningOutcome` is or is not a general cognitive-operation result, adds no retention or
persistence mapping, adds no `ReasoningOutcome` to `EpistemicClaim` mapping and no confidence
production, introduces no Mode relation, and does no usage, token, or cost work.

### Richer outcome production and frontier disposition

```text
RICHER_REASONING_OUTCOME_PRODUCTION_READY               = NO
STRUCTURED_REASONING_OUTCOME_FRONTIER_DISPOSITION       = PARK_AFTER_ADR_0036_LIFECYCLE
```

Richer outcome production still lacks a provider-neutral structured reasoning-result authority,
an `InformationNeed.subject_ref` target authority, and a model self-report or alternative
semantic-interpretation authority. This ADR resolves none of them.

As process guidance only, and not an architectural prohibition: once this ADR has completed its
review, publication, and synchronization, the structured `ReasoningOutcome` production frontier
should return to a parked state unless new evidence or a real consumer justifies reopening it.
It is not thereby declared permanently complete.

## What this ADR does not decide

- `PARTIAL` selection semantics;
- `NEEDS_INFORMATION` selection semantics;
- completion semantics for any specialized strategy;
- richer DIRECT semantic classification;
- `InformationNeed` production;
- the `InformationNeed.subject_ref` namespace;
- `reason_summary` semantics;
- model self-report authority;
- a structured reasoning-result schema;
- an output parser;
- correctness or truth of a conclusion;
- confidence;
- Verification;
- retention of outcomes;
- any Epistemic mapping;
- a general cognitive-operation result;
- outcome semantics for specialized strategies.

## Consequences

Positive:

- `ReasoningStatus.COMPLETED` has a precise, minimal meaning for DIRECT;
- the current DIRECT mapping is valid without any code change;
- readers are prevented from over-reading `COMPLETED` as truth, verification, confidence,
  exhaustiveness, or epistemic sufficiency;
- Cognition, not `model_router` or a provider, owns reasoning-completion semantics;
- richer outcomes -- `PARTIAL`, `NEEDS_INFORMATION`, `UNRESOLVED`, structured production,
  cognition-owned interpretation, and other strategy executors -- remain possible;
- no speculative parser, schema, or `subject_ref` namespace is introduced.

Tradeoffs:

- `COMPLETED` for DIRECT is a modest assertion -- a recorded conclusion -- and must not be read
  as a quality signal;
- an empty `information_needs` tuple does not mean that no information is missing;
- selection semantics for `PARTIAL` and `NEEDS_INFORMATION` remain undefined;
- `reason_summary` remains a semantically weak label;
- richer outcome production remains not ready.

## ADR relationship

- **ADR-0032** establishes that `ReasoningStatus.UNRESOLVED` is reserved for genuine semantic
  reasoning incompleteness after an attempt, and that a budget admission failure is not
  `UNRESOLVED`. This ADR preserves both statements and does not redefine `UNRESOLVED`.
- **ADR-0033** preserves the boundary between a cognitive deadline failure and a technical
  `ReasoningExecutionError`. This ADR leaves that boundary unchanged.
- **ADR-0031** concerns the integration of prior-TASK context into the current DIRECT runtime,
  including model-input materialization. It is context only and does not define completion
  semantics.
- **ADR-0035** defines the operational role of `CognitiveMode`. Its Mode semantics are unrelated
  to this ADR and remain unchanged, and the Mode axis stays parked.
- **ADR-0011** is referenced only as adjacent precedent for keeping an explicit semantic state
  alongside payload consistency. It does not define `ReasoningStatus`.
- **ADR-0022** is referenced only as an adjacent discussion in the Verification context, where
  `ReasoningOutcome` appears as precedent. It does not own Reasoning semantics.

None of these ADRs previously defined DIRECT `COMPLETED`, and this ADR supersedes none of them.
