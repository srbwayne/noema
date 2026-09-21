# ADR-0037: Context Relevance Semantics

- Status: Accepted
- Date: 2026-09-20

## Context

`ContextCandidate.relevance` is a canonical Cognition domain field with a defined representation and
existing consumers, but the proposition asserted by a known numeric value had not been canonically
stated.

What already exists:

- `ContextCandidate.relevance` is `float | None`. A known value must be a finite float in
  `[0.0, 1.0]`.
- `None` already means that no relevance judgment exists for the candidate. ADR-0030 fixed this
  explicitly: `None` is never a numeric sentinel -- not `0.0`, `0.5`, or `1.0`.
- `ContextComposer` consumes a known relevance value for both eligibility and ranking. A known
  value below `ContextCompositionPolicy.minimum_relevance` is ineligible, a higher known value is
  preferred at the relevance ranking dimension, and unknown relevance may satisfy required
  coverage only and is never optional enrichment.
- `ContextCompositionPolicy.minimum_relevance` already consumes the numeric value as a threshold.
  Its representation is a finite float in `[0.0, 1.0]`.
- `PriorTaskContextProjector` currently emits `relevance=None` for every prior-`TASK` candidate,
  and no production relevance producer exists.
- ADR-0030 explicitly rejected recency, canonical position, and same-runtime membership as
  relevance substitutes.
- ADR-0031 made prior-`TASK` context production-reachable and integrated it into the DIRECT
  runtime, but deferred relevance scoring beyond ADR-0030's unknown-relevance eligibility policy.

The semantic problem is narrow and specific. The representation and the consumer behavior existed,
but the proposition asserted by a numeric relevance value was not canonically defined. The
repository stated what a value looks like and how the composer reads it, but not what a value
says. As a consequence, the numeric threshold `minimum_relevance` could not be interpreted beyond
a number, no endpoint had a meaning, and it was not stated where comparing two scores is valid.

ADR-0012 records a related and adjacent observation: the numeric scores in the repository --
including `ContextCandidate.relevance` -- each measure a different axis governed by their own
component-specific policy, and none is transferable to another axis by analogy alone. That
observation is a precedent for keeping axes separate. It does not define Context relevance.

This ADR records the decision that defines what `ContextCandidate.relevance` means, and nothing
beyond it. It does not decide who produces relevance, how it is computed, or what happens when
production fails.

## Decision

### Semantic quantity

```text
CONTEXT_RELEVANCE_SEMANTIC       = CURRENT_TASK_PERTINENCE
CONTEXT_RELEVANCE_SEMANTIC_SCOPE = PER_CONTEXT_COMPOSITION
CONTEXT_RELEVANCE_REFERENCE      = CURRENT_TASK_DESIGNATED_BY_CONTEXT_REQUEST_TASK_REF
CONTEXT_RELEVANCE_SUBJECT        = ONE_CONTEXT_CANDIDATE_CONTEXTUAL_INFORMATION
```

### Normative definition

For one `ContextCandidate`, when a relevance judgment exists, `relevance` is the normalized degree
in `[0.0, 1.0]` to which the contextual information represented by that candidate is judged
pertinent to the current task designated by `ContextRequest.task_ref` for the context composition
in which the candidate is being considered.

Within that same composition and under the same applicable relevance authority, a higher relevance
score means the candidate is judged more pertinent to the current task than a lower-scored
candidate.

### Current task

In this ADR, "current task" means the task designated by `ContextRequest.task_ref` belonging to
the context composition in which the candidate is considered. It is not a reference to any
`SituationModel` entry as such: it is the task that the request for this composition names.

`task_ref` is an opaque semantic reference. The definition does not require:

- resolution of a task payload;
- text comparison;
- embedding;
- LLM execution;
- semantic-search infrastructure.

The definition states what is judged -- pertinence to the designated task -- and not how the task
is understood or by what means the judgment is reached.

### Judgment subject

The score concerns the contextual information represented by one `ContextCandidate`. It is not
globally a property of:

- the provider;
- the source;
- the slice type;
- the historical `TASK` from which a candidate may originate;
- the runtime.

Two candidates carrying the same source information may be judged differently in different
compositions, because the reference belongs to the composition.

### Scope

```text
CONTEXT_RELEVANCE_SEMANTIC_SCOPE = PER_CONTEXT_COMPOSITION
```

A relevance judgment belongs to one candidate in one context composition. Candidates are
reconstructed on every preparation, and no retention authority for a judgment exists. This ADR does
not authorize a per-runtime retained score, a durable score, or a cross-process score.

### Scale

```text
RELEVANCE_SCALE = NORMALIZED_0_TO_1
```

The structural representation is unchanged:

```text
known relevance   = finite float in [0.0, 1.0]
unknown relevance = None
```

### Zero endpoint

```text
RELEVANCE_ZERO_SEMANTIC = JUDGED_NOT_PERTINENT_TO_CURRENT_TASK
```

`0.0` is a valid known judgment. It is not `None`, not a producer failure, not unknown content,
and not low confidence.

### One endpoint

```text
RELEVANCE_ONE_SEMANTIC = JUDGED_MAXIMALLY_PERTINENT_TO_CURRENT_TASK_ON_APPLICABLE_SCALE
```

`1.0` is maximal on the applicable relevance authority's normalized scale. It does not establish
global calibration, probability, truth, or necessity.

### Ordering

```text
RELEVANCE_ORDERING_SEMANTIC =
  HIGHER_SCORE_MEANS_GREATER_CURRENT_TASK_PERTINENCE_WITHIN_SAME_COMPOSITION_AND_AUTHORITY
```

Equal scores establish no pertinence ordering between the candidates. The numeric distance between
two scores has no separately defined semantic meaning: a difference of `0.2` is not asserted to be
twice a difference of `0.1`.

### Comparability

```text
RELEVANCE_SCORE_COMPARABILITY_SCOPE              = WITHIN_SAME_COMPOSITION_ONLY
CROSS_OPERATION_RELEVANCE_COMPARABILITY_REQUIRED = NO
```

Numeric comparison of scores is semantically valid only within one context composition. This is
exactly the extent to which `ContextComposer` compares candidates: inside one composition. This
ADR does not authorize cross-operation calibration, cross-runtime comparison, or a global relevance
ranking.

### Calibration

```text
RELEVANCE_ABSOLUTE_CALIBRATION_REQUIRED = NO
```

The semantic contract requires a normalized ordering under the applicable authorized relevance
policy. It does not require a globally calibrated numeric measurement system.

### `minimum_relevance` semantics

```text
MINIMUM_RELEVANCE_SEMANTIC =
  LOWEST_KNOWN_JUDGED_RELEVANCE_AT_WHICH_A_CANDIDATE_REMAINS_ELIGIBLE
```

`ContextCompositionPolicy.minimum_relevance` is the lowest known judged relevance, on the same
normalized scale, at which the candidate remains eligible with respect to relevance. It applies
only to known scores,
according to the existing `ContextComposer` semantics. It does not reject `relevance=None`.

The representation of `minimum_relevance` is unchanged, and no current composition rule is changed.
Under the existing rule a known score at or above the threshold satisfies the relevance condition
for eligibility, so a threshold of `0.0` is satisfied by a candidate judged `0.0`. The candidate
must still satisfy every independent non-relevance guardrail (forbidden slice type, sensitivity,
trust, age, authority). That is a consequence of the existing eligibility rule and of the chosen
threshold value, not of this ADR.

Because absolute calibration is not required, a threshold value is meaningful only relative to the
scale of the applicable relevance authority. This ADR does not decide which authority that is.

### `None` semantics

```text
NONE_RELEVANCE_SEMANTIC = NO_RELEVANCE_JUDGMENT_EXISTS
```

This ADR preserves ADR-0030's meaning of `None` exactly. `None` asserts only that no relevance
judgment exists. It does not mean:

- `0.0`;
- not relevant;
- producer failure;
- unknown content;
- low confidence.

### Independent axes

Relevance is distinct from the following axes, each of which remains independent:

```text
RELEVANCE_ASSERTS_TRUST              = NO
RELEVANCE_ASSERTS_SENSITIVITY        = NO
RECENCY_AS_RELEVANCE_AUTHORIZED      = NO
RELEVANCE_ASSERTS_ATTENTION_PRIORITY = NO
RELEVANCE_ASSERTS_CONFIDENCE         = NO
RELEVANCE_ASSERTS_TRUTH              = NO
RELEVANCE_ASSERTS_CORRECTNESS        = NO
RELEVANCE_ASSERTS_UTILITY            = NO
RELEVANCE_ASSERTS_NECESSITY          = NO
RELEVANCE_ASSERTS_SUFFICIENCY        = NO
```

- **Trust.** A candidate may be highly pertinent but untrusted. `ContextTrustLevel` remains its own
  axis.
- **Sensitivity.** `ContextSensitivity` remains its own axis.
- **Recency.** ADR-0030's rejection of recency as relevance is preserved. Age remains an
  independent `ContextComposer` ranking dimension.
- **Attention.** Relevance is not Attention priority or score. This ADR does not integrate
  Attention (see the non-decisions below).
- **Confidence.** Relevance is not epistemic confidence, and not any future model confidence.
- **Truth and correctness.** A relevant candidate may be false.
- **Utility.** Relevance is pertinence. It is not expected reasoning utility, answer quality, or
  expected outcome improvement.
- **Necessity and sufficiency.** A high score does not mean that the candidate is required, and
  does not mean that it alone is sufficient context.

### Provider and algorithm independence

```text
CONTEXT_RELEVANCE_SEMANTIC_PROVIDER_INDEPENDENT  = YES
CONTEXT_RELEVANCE_SEMANTIC_ALGORITHM_INDEPENDENT = YES
```

The meaning does not depend on Ollama, a particular LLM, an embedding model, a tokenizer, a vector
database, or cosine similarity.

The semantic may later be realized by a separately authorized deterministic, model-backed,
caller-supplied, or hybrid producer without changing the domain meaning. This is compatibility, not
authorization: this ADR authorizes no producer of any kind.

### Semantic similarity is not the definition

```text
SEMANTIC_SIMILARITY_IS_RELEVANCE_DEFINITION = NO
```

Similarity between candidate content and task content may potentially be a future scoring
technique. It is not the semantic meaning of the field. Similar content is not thereby pertinent,
and pertinent content is not necessarily similar.

### Goal relevance is not the definition

```text
GOAL_RELEVANCE_IS_CONTEXT_RELEVANCE_DEFINITION = NO
```

This ADR does not require a goal. `ContextRequest.goal_ref` remains optional, and goal payload
authority remains unresolved.

### The full request is not the reference

```text
FULL_CONTEXT_REQUEST_IS_RELEVANCE_REFERENCE = NO
```

The reference is the task designated by `task_ref`, and not the request as a whole. The independent
request guardrails -- trust, sensitivity, age, authorities, slice-type constraints, and the size
budget -- do not become implicit inputs to the meaning of relevance merely because they belong to
`ContextRequest`. Each remains an independent constraint applied by `ContextComposer` on its own
axis.

## Current runtime compatibility

```text
CURRENT_PRIOR_TASK_RUNTIME_COMPATIBLE_WITH_ADR_0037 = YES
```

Every current prior-`TASK` candidate carries `relevance=None`, and the semantic defined here
explicitly permits no relevance judgment to exist. The current runtime behavior is unchanged:
`None` may satisfy required coverage, is never optional enrichment, and is not rejected by
`minimum_relevance`.

## Source consequence

```text
CONTEXT_RELEVANCE_SEMANTIC_DECISION_REQUIRES_SOURCE_CHANGE = NO
SOURCE_DOC_ALIGNMENT_REQUIRED                              = NO
```

The existing field shape and its "no relevance judgment exists" contract already permit this
definition. No implementation follows merely from defining the domain meaning.

## Existing consequence, not decided here

```text
KNOWN_LOW_REQUIRED_TASK_FAILURE_POLICY = UNRESOLVED
```

Under current behavior, known relevance must satisfy `minimum_relevance` in both the required and
the optional phase, and a known below-threshold value is never overridden by the consumer's
required-type requirement. Therefore, if every required `TASK` candidate has a known relevance
below `minimum_relevance`, current `ContextComposer` behavior may leave required coverage
unsatisfied and raise `ContextCompositionUnsatisfiedError`.

This ADR describes that existing consequence only. It does not decide whether that behavior should
remain.

## What this ADR does not decide

```text
CONTEXT_RELEVANCE_OWNER_IDENTIFIED                 = NO
RUNTIME_RELEVANCE_PRODUCER_OWNER                   = UNRESOLVED
RELEVANCE_PRODUCER_TIMING                          = UNRESOLVED
RELEVANCE_JUDGMENT_CORRELATION_AUTHORITY           = UNRESOLVED
RELEVANCE_PRODUCTION_FAILURE_SEMANTICS             = UNRESOLVED
KNOWN_LOW_REQUIRED_TASK_FAILURE_POLICY             = UNRESOLVED
RELEVANCE_RETENTION_AUTHORITY                      = NONE
MODEL_BASED_RELEVANCE_ARCHITECTURALLY_POSSIBLE     = UNRESOLVED
MODEL_ROUTER_CAN_OWN_RELEVANCE_SEMANTICS           = NO
WORKSPACE_TO_CONTEXT_RELEVANCE_MAPPING_AUTHORIZED  = NO
ATTENTION_TO_CONTEXT_RELEVANCE_MAPPING_AUTHORIZED  = NO
ATTENTION_PRIORITY_SEMANTICALLY_EQUIVALENT_TO_CONTEXT_RELEVANCE = UNRESOLVED
```

This ADR defines the Cognition semantic contract of `ContextCandidate.relevance`. It does not
identify a runtime producer. Specifically, it does not decide:

- **Ownership.** Which Cognition authority may produce a relevance judgment.
- **Producer timing.** Whether production occurs during projection, after projection, before
  composition, or during canonical ingestion.
- **Correlation.** How a judgment is correlated to one candidate -- whether by `content_ref`,
  `provenance_ref`, `SituationEntry.entry_id`, or position.
- **Failure semantics.** Fallback to `None`, operation failure, candidate exclusion, retry, or
  partial judgment.
- **Required-`TASK` interaction.** Whether the existing consequence above should remain.
- **Retention.** Persistence, memory, or any lifetime of a judgment beyond one composition.
- **Model scoring.** Whether a model-backed producer is architecturally possible, and whether an
  additional model call is permitted. `model_router` does not own relevance semantics.
- **Attention.** Attention is not wired, and this ADR defines no mapping from Attention priority or
  score to relevance.
- **Workspace.** `CognitiveItem.relevance` remains a separate existing field with no authorized
  mapping to `ContextCandidate.relevance`.
- **Calibration and thresholds.** No scoring scale or threshold value is chosen.
- **Implementation.** No source, test, or docstring change is authorized.

Now that the quantity is defined, the next unresolved question is which Cognition authority may
produce such a judgment:

```text
NEXT_CONTEXT_RELEVANCE_BLOCKER = OWNERSHIP
```

This ADR does not answer that question.

## Consequences

Positive:

- `ContextCandidate.relevance` has a precise, minimal meaning: pertinence to the current task, per
  context composition;
- `minimum_relevance`, the endpoints, and the ordering that `ContextComposer` already applies now
  have a defined proposition;
- the current all-`None` prior-`TASK` runtime is valid without any code change;
- readers are prevented from over-reading a score as trust, sensitivity, recency, priority,
  confidence, truth, utility, necessity, sufficiency, or a probability;
- the meaning is independent of any provider and of any scoring technique, so deterministic,
  model-backed, caller-supplied, and hybrid producers remain possible;
- no producer, owner, transport, or identifier is introduced.

Tradeoffs:

- because absolute calibration is not required, a `minimum_relevance` value is meaningful only
  relative to the scale of the applicable relevance authority;
- scores are comparable only within one composition, so no cross-operation or global relevance
  ranking is available;
- the numeric distance between scores has no defined meaning;
- no producer exists, so the definition remains unexercised by the production runtime;
- the existing consequence for required `TASK` coverage when every candidate is known-low remains
  undecided.

## ADR relationship

- **ADR-0030** established that `None` means no relevance judgment exists, rejected recency,
  canonical position, and same-runtime membership as relevance substitutes, and fixed the
  unknown-relevance composition semantics. It did not define the proposition that a numeric
  relevance value asserts. This ADR supplements it and preserves all of those statements.
- **ADR-0031** made the prior-`TASK` context pipeline production-reachable and explicitly deferred
  relevance scoring. This ADR defines the meaning of a score without scoring anything, and does not
  alter the integration.
- **ADR-0012** is adjacent precedent only: it observes that numeric cognition fields, including
  `ContextCandidate.relevance`, each measure a different axis and are not transferable by analogy.
  It does not define Context relevance.
- **ADR-0035** defines the operational role of `CognitiveMode`. Its Mode semantics are unrelated to
  this ADR and remain unchanged, and the Mode axis stays parked.
- **ADR-0036** defines DIRECT reasoning completion semantics. Those semantics are unrelated to this
  ADR and remain unchanged.

None of these ADRs previously decided `CURRENT_TASK_PERTINENCE`, and this ADR supersedes none of
them.

```text
ADR_0037_SUPERSEDES_EXISTING_ADR = NO
```

The structured-outcome, Mode, usage, general-operation, and strategy-demand frontiers are not
touched by this ADR:

```text
STRUCTURED_REASONING_OUTCOME_FRONTIER                                = PARKED_PENDING_NEW_EVIDENCE
RICHER_REASONING_OUTCOME_PRODUCTION_READY                            = NO
MODE_AXIS_DISPOSITION                                                = PARKED_PENDING_NEW_EVIDENCE
MODE_SEMANTIC_ORDER                                                  = UNRESOLVED
USAGE_FRONTIER_DISPOSITION                                           = REMAIN_PARKED
GENERAL_COGNITIVE_OPERATION_CONTRACT                                 = UNRESOLVED
REASONING_OUTCOME_SUFFICIENT_AS_GENERAL_COGNITIVE_OPERATION_RESULT   = UNRESOLVED
PRODUCTION_REASONING_STRATEGY_DEMAND_PRODUCER                        = NONE
PRODUCTION_STRATEGY_AWARE_OPERATION_REACHABLE                        = NO
```
