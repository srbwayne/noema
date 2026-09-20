# ADR-0035: CognitiveMode Operational Semantic Role

- Status: Accepted
- Date: 2026-09-19

## Context

ADR-0005 freezes the Cognitive Mode Arbiter and `REFLEX`, `FAST`, `DELIBERATE`, and `DEEP` as
COGNITION V1 components, structurally only: it explicitly does not specify their semantics.
`CognitiveMode` exists as a plain four-member `Enum`, and today it is transported end to end
without ever being read behaviorally:

- `direct.policy.mode` (process configuration) is parsed into a `CognitiveMode` and forwarded as
  the per-operation `mode` argument;
- `ContextRequest.mode` validates the type and is otherwise transport-only;
- no `ReasoningStrategy`, `CognitiveBudget`, context, model-selection, or planning decision reads
  it;
- all four values currently reach the same DIRECT reasoning execution path.

Separately, `CognitiveModeArbiter` and `CognitiveModeDecision` exist as fully tested domain
contracts that no production component constructs, and `CognitiveDemand` has no runtime producer.
Source-level docstrings describe `CognitiveMode` as "Authorized cognitive processing depths" and
"Depth and strategy authorized for a cognitive operation", but no accepted ADR gives those phrases
cross-component authority, and the Arbiter's ordering of the four modes is a private
arbitration-internal detail.

Without an accepted meaning for one `CognitiveMode` value, any later relation from mode to another
component would have to invent its own premise. This ADR records only the approved, smallest
operational semantic role of one value with respect to one cognitive operation.

## Decision

### Role: effective processing depth

```text
COGNITIVE_MODE_OPERATIONAL_SEMANTIC_ROLE = EFFECTIVE_PROCESSING_DEPTH
```

One `CognitiveMode` value designates the effective cognitive-processing depth assigned to one
cognitive operation. "Effective" means the operation's assigned mode value for that operation --
the single assigned mode designation, as distinct from the Arbiter's intermediate `minimum_mode`
and `soft_mode`. It does **not** imply that the runtime realizes distinct mode-specific behavior.
The value is an assignment made by a source, not an observation of what execution did.

The semantic identity of a mode is therefore allowed to exist before any mode-specific downstream
behavior is defined or implemented.

### Operation scope

```text
COGNITIVE_MODE_SCOPE = PER_COGNITIVE_OPERATION
```

The value belongs semantically to one cognitive operation. A process may currently reuse the same
configured value across every operation of a session; that reuse is a process-level policy and
does not make `CognitiveMode` session-owned.

### Source independence

```text
COGNITIVE_MODE_VALUE_SEMANTICS_SOURCE_INDEPENDENT = YES
```

The meaning of a `CognitiveMode` value does not depend on who supplied it. Its current source is
`direct.policy.mode`; a future possible source is `CognitiveModeArbiter.selected_mode`. Both can
supply the same operation-mode semantic value. The semantic owner is cognition domain
architecture; a producer supplies the value and does not thereby own its meaning.

### Current configured mode

```text
CURRENT_CONFIGURED_MODE_ROLE = DIRECTLY_ASSIGNED_OPERATION_MODE
```

The current process configuration (`direct.policy.mode`, realized by `_process.py`) directly
supplies the operation's effective `CognitiveMode`. This is current process policy. It does not
mean configuration permanently owns mode selection, and it decides no `CognitiveMode` bootstrap
source beyond what already exists.

### Future Arbiter compatibility

```text
FUTURE_ARBITER_SELECTED_MODE_ROLE = SAME_OPERATION_MODE_SEMANTICS
```

If a future runtime legitimately wires `CognitiveModeArbiter`,
`CognitiveModeDecision.selected_mode` may supply the same semantic value that `direct.policy.mode`
supplies today. `minimum_mode` and `soft_mode` keep their arbitration-scoped meanings; they share
the `CognitiveMode` type but are not operation modes. This ADR does not authorize that wiring, and
it does not decide how `CognitiveDemand` is produced.

### Behavioral degeneracy is currently allowed

```text
MODE_BEHAVIORAL_DEGENERACY_ALLOWED = YES
```

Multiple `CognitiveMode` values may temporarily produce identical observable runtime behavior when
downstream mode-specific behavior has not yet been defined or implemented. The current first-DIRECT
runtime is therefore not inconsistent merely because `REFLEX`, `FAST`, `DELIBERATE`, and `DEEP`
all currently reach the same DIRECT reasoning execution path. This is a current-runtime
compatibility statement, not a permanent architectural rule.

Strategy-demand fallback and mode behavioral degeneracy are different phenomena, and this
allowance does not weaken ADR-0034's prohibition (`SPECIALIZED_TO_DIRECT_FALLBACK_ALLOWED = NO`):
a `ReasoningStrategyDemand` that resolves to a specialized strategy is denied rather than executed
as DIRECT, whereas `CognitiveMode` currently has no approved downstream behavior mapping. A
`CognitiveMode` designation, by itself under the semantics decided here, currently imposes no
separately approved downstream execution behavior. This does not mean that `CognitiveMode` can
never constrain execution, that future mode-specific behavior may be ignored, or that
`CognitiveMode` has no normative future role. The allowance holds only while no relation from mode
to behavior has been decided; any future relation must decide separately whether collapsing to a
single behavior remains acceptable, and this allowance is not authority for any future mapping.

### No immediate runtime enforcement

```text
MODE_ROLE_REQUIRES_IMMEDIATE_RUNTIME_ENFORCEMENT = NO
```

Defining the operation's effective mode does not by itself require a new runtime enforcement
component. No production implementation follows from this ADR alone.

### Semantic ordering boundary

This ADR does not freeze a general semantic ordering.

```text
MODE_ORDERING_SCOPE = ARBITRATION_ORDER_ONLY
MODE_SEMANTIC_ORDER = UNRESOLVED
```

The ordering `REFLEX` → `FAST` → `DELIBERATE` → `DEEP` exists inside `CognitiveModeArbiter`'s
arbitration algorithm, while `CognitiveMode` itself is currently represented as a plain `Enum` with
no general ordering contract. This ADR does not generalize that private arbitration ordering into
a runtime capability order, a strategy power order, a resource-intensity order, a budget order, or
a general semantic depth order. The role above needs four distinct named depth designations and no
ordinal relation. "Depth" names the category and does not by itself approve an ordinal scale.

### Relations firewalled

Selecting this role introduces no mapping from any `CognitiveMode` value to any other component.

```text
COGNITIVE_MODE_TO_REASONING_STRATEGY_DEMAND = UNRESOLVED
COGNITIVE_MODE_TO_REASONING_STRATEGY        = SUGGESTED_NOT_AUTHORIZED
MODE_BUDGET_RELATION                        = NONE_AUTHORIZED
MODE_CONTEXT_RELATION                       = NONE_AUTHORIZED
MODE_MODEL_SELECTION_RELATION               = NONE_AUTHORIZED
MODE_PLANNING_RELATION                      = NONE_AUTHORIZED
MODE_AUTHORIZES_TOOL_USE                    = UNRESOLVED
MODE_AUTHORIZES_EXTERNAL_SEARCH             = UNRESOLVED
```

**Strategy.** The source-level `CognitiveMode` docstring mentioning strategy authorization is not
sufficient authority for a cross-component strategy mapping. This ADR defines no mode → strategy
matrix, no allowed strategy set, no strategy floor or ceiling, and no `ReasoningStrategyDemand`
derivation. ADR-0034 remains unchanged.

**Budget.** No authorized relation exists between `CognitiveMode` and `max_time`, `max_steps`,
`max_llm_calls`, `max_tool_calls`, `max_cost`, `max_tokens`, or `max_search_depth`. This ADR does
not make `CognitiveMode` a budget preset or a budget constraint. ADR-0032 and ADR-0033 remain
unchanged.

**Context.** `CognitiveMode` does not currently determine required context types, forbidden
context types, relevance, slice count, sensitivity, trust, instruction authority, age, the
context-size limit, or candidate ordering. `ContextRequest.mode` remains transport-only in the
current runtime.

**Model selection.** Mode does not select a provider, a model, a model capability, a model count,
structured output, or tool-calling capability. Provider independence is preserved.

**Planning.** No current rule states that any `CognitiveMode` requires planning, forbids planning,
permits planning, or changes planning depth.

**Tools and search directionality.** The current Arbiter-local implications run in one direction
only: `requires_tools` → minimum arbitration mode `DELIBERATE`, and `requires_external_information`
→ minimum arbitration mode `DELIBERATE`. These are demand-to-minimum-arbitration-mode facts inside
the Arbiter. They are not reversed by this ADR: no rule says `DELIBERATE` authorizes tool use or
external search.

### Arbiter boundary

```text
COGNITIVE_DEMAND_RUNTIME_PRODUCER   = NONE
ARBITER_OUTPUT_REAL_CONSUMER        = NONE
COGNITIVE_MODE_ARBITER_RUNTIME_READY = NO
```

This ADR defines what a `CognitiveMode` value means. It does not define how runtime demand is
produced or how the Arbiter becomes reachable, and it creates neither a producer nor a consumer.

### Authorization versus selection vocabulary

The source-level phrase "Depth and strategy authorized for a cognitive operation" is not
interpreted by this ADR as a frozen capability or permission envelope. The accepted role is the
effective processing depth assigned to the operation. Any stronger meaning of "authorized"
requires a separate decision. The Python docstring is not modified by this ADR.

### Current runtime truthfulness

```text
CURRENT_DIRECT_RUNTIME_COMPATIBLE_WITH_MODE_ROLE = YES
```

The semantic mode value identifies the operation's assigned cognitive depth, while downstream
differentiation remains separately unresolved. Equal observable execution behavior across all four
modes is permitted by the behavioral-degeneracy allowance above, so all four currently valid
configurations remain valid.

## What this ADR does not decide

- general semantic ordering among `REFLEX` / `FAST` / `DELIBERATE` / `DEEP`;
- mode → reasoning strategy;
- mode → `ReasoningStrategyDemand`;
- mode → budget;
- mode → context;
- mode → model selection;
- mode → planning;
- mode → tools;
- mode → external search;
- `CognitiveDemand` production;
- `CognitiveModeArbiter` runtime wiring;
- mode-specific executor topology;
- mode-specific provider or model choice;
- mode-specific resource consumption;
- mode-specific output or result form.

## Preserved frontiers

This ADR preserves the following existing boundaries and does not reopen or decide them:

- `GENERAL_COGNITIVE_OPERATION_CONTRACT = UNRESOLVED` and
  `REASONING_OUTCOME_SUFFICIENT_AS_GENERAL_COGNITIVE_OPERATION_RESULT = UNRESOLVED` remain open and
  unrelated to this decision;
- `USAGE_FRONTIER_DISPOSITION = REMAIN_PARKED`;
- `COGNITIVE_BUDGET_ENFORCED_DIMENSIONS = max_llm_calls, max_time`, and full `CognitiveBudget`
  runtime enforcement remains unimplemented;
- `STRATEGY_DEMAND_ADMISSION_STATUS = MERGED_CANONICAL` (ADR-0034);
- `VERIFICATION_SOURCE_IMPLEMENTATION = NO`.

## Next frontier and parking criterion

```text
NEXT_MODE_DESIGN_FRONTIER = MODE_SEMANTIC_DEPTH_ORDER
```

The next design investigation may ask whether `REFLEX`, `FAST`, `DELIBERATE`, and `DEEP` have a
canonical semantic ordering outside the Arbiter's internal selection algorithm. This ADR does not
answer that question.

As future process guidance only, not an architectural prohibition: after
`MODE_SEMANTIC_DEPTH_ORDER` is investigated, the Mode axis should be eligible to return to a parked
state unless a real runtime consumer or new authority justifies another relation. Parking is not a
pre-decision that `CognitiveMode` has no future relation to strategy, budget, context, tools,
model selection, planning, or any other component, and new evidence or a real consumer may reopen
the axis. No relation, including strategy integration, is preselected.

## Consequences

Positive:

- `CognitiveMode` now has a precise operation-level semantic role;
- current process configuration and future Arbiter output can share the same semantic value;
- mode semantics no longer depend on the current lack of differentiated execution behavior;
- no speculative strategy, budget, or context mapping is introduced;
- the current runtime remains valid.

Tradeoffs:

- mode still has no behavioral consumer;
- the semantic depth order remains unresolved outside arbitration;
- Arbiter wiring remains unauthorized and not implementation-ready;
- the four modes still collapse to identical observable execution today.

## ADR relationship

- **ADR-0005** freezes the Cognitive Mode Arbiter and the four modes structurally only and
  specifies no semantics. This ADR adds the operation-level role of one value and does not amend
  the frozen structure.
- **ADR-0026** records that no `CognitiveMode` bootstrap source is decided. This ADR keeps source
  and meaning separate and decides no new source.
- **ADR-0030 / ADR-0031** defer mode-arbitration integration around context work. That deferral
  stands.
- **ADR-0034** deferred `CognitiveMode`/`CognitiveDemand` integration, and separately left the
  `CognitiveDemand` → `ReasoningStrategyDemand` relation undecided. Neither is changed by this ADR,
  which decides no `CognitiveMode` → `ReasoningStrategy` or `CognitiveMode` →
  `ReasoningStrategyDemand` relation. ADR-0034 is unchanged.

This ADR supersedes none of them.
