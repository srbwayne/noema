# ADR-0021: Verification Minimum Polarity Requirement Semantics

- Status: Accepted
- Date: 2026-09-01

## Context

ADR-0015 froze Verification's minimum V1 semantic category — correctness/validity of derived
content — evaluated within the derivation context under which that content was produced, and
deferred all output semantics. ADR-0016 froze the first/minimum Verification subject as one
individual Prediction / Counterfactual consequence item. ADR-0017 preserved correctness/validity
as one undifferentiated semantic axis and froze the minimum explicit derivation-context axes.
ADR-0018 froze a partial, explicit-axis-scoped correlation semantics for that subject. ADR-0019
froze that a minimum Verification request transports exactly one instance of the minimum subject.
ADR-0020 froze what minimally exists when Verification succeeds in producing a correctness/
validity judgment — one determination concerning one minimum subject, within the subject's
applicable derivation-context scope — while explicitly leaving polarity unresolved:
`POLARITY_REMAINS_UNRESOLVED`. ADR-0020 did not claim the determination's semantic space is
binary, finite, or open/non-enumerated; it left all three shapes, and the prior question of
whether any orientation dimension is required at all, equally undecided. ADR-0020's successful-
judgment atom is itself independent of polarity and representation; it does not depend on polarity
being resolved in either direction.

A subsequent read-only discovery (M0-15ED) examined a narrower question than "what should
polarity be": whether the minimum successful judgment semantics positively require a polarity
dimension at all. That discovery found no accepted Verification authority (ADR-0015 through
ADR-0020) that positively establishes such a requirement, found that ADR-0015 itself declines to
infer any output shape from the words "correctness" or "validity," and found the adjacent
Evaluation architecture — not itself Verification authority — illustrative only that a fixed
polarity dimension is not universally necessary for every accepted judgment category in this
codebase, without treating that adjacent precedent as proof of anything about Verification's own
semantics. A subsequent decision review (M0-15EE) evaluated three candidates — polarity required,
polarity not required by the minimum, and necessity left unspecified — against that evidence and
approved the second: mandatory polarity was not sufficiently justified for the minimum semantic
contract, while future richer polarity semantics remain possible under their own, separately
evidenced decision. This ADR records the result of that approval. It does not reopen the
discovery or review, and it does not create any production contract.

## Decision

### Minimum polarity requirement

The minimum successful Verification judgment does **not** require a polarity dimension. A minimum
successful correctness/validity determination remains semantically valid without polarity being a
mandatory dimension of the minimum judgment contract.

Conceptually: `MINIMUM_SUCCESSFUL_VERIFICATION_JUDGMENT_DOES_NOT_REQUIRE_POLARITY`.

### Scope tokens

This decision carries the following boundaries, each a consequence of the same single decision
above, not a separate semantic decision:

- `POLARITY_NOT_PART_OF_MANDATORY_MINIMUM_JUDGMENT_SEMANTICS`;
- `FUTURE_RICHER_POLARITY_SEMANTICS_NOT_PROHIBITED`;
- `POLARITY_TOPOLOGY_NOT_REQUIRED_FOR_MINIMUM_CONTRACT`.

### "Not required" precision — critical boundary

This ADR freezes `NOT_REQUIRED`. It does not freeze, and explicitly distinguishes this from,
`ABSENT`, `FORBIDDEN`, `IMPOSSIBLE`, or `NON_POLAR`. This ADR does not state that Verification has
no polarity, that Verification judgments are non-polar, that polarity is forbidden, that
correctness/validity has no possible opposed semantic orientation, or that every future
Verification layer must omit polarity. `NOT_REQUIRED` means only that the minimum mandatory
judgment contract does not include a polarity dimension as one of its required elements. Whether
any particular future, richer judgment vocabulary happens to be polar or non-polar is left
entirely open by this ADR.

### ADR-0020 relationship — precise scope

ADR-0020 left polarity unresolved (`POLARITY_REMAINS_UNRESOLVED`); it did not itself decide
whether polarity is required by the minimum contract, and this ADR does not claim it did. ADR-0021
is a new increment, narrower than ADR-0020's open question: it resolves only whether polarity is
*mandatory* for the minimum successful judgment. The conceptual status after this ADR is
`MINIMUM_POLARITY_REQUIREMENT_RESOLVED_AS_NOT_REQUIRED`. Any future, richer polarity semantics —
whatever shape they might take — remain outside this minimum contract and remain a separate,
undecided question. ADR-0020's successful-judgment atom, and everything else ADR-0020 froze,
remains entirely unchanged and authoritative.

### Candidate A (mandatory polarity) — why not selected

A candidate requiring every minimum successful judgment to carry a polarity dimension is not
selected here, but not because it contradicts ADR-0020 or any other accepted authority — no
accepted authority declares mandatory polarity incompatible with the successful-judgment atom.
The reason is narrower: making polarity mandatory would add an invariant to the minimum semantic
contract without sufficient architectural evidence establishing that opposed orientation is
necessary. No accepted Verification ADR demonstrates that necessity; the only support available
for it is ordinary-language intuition about how correctness judgments commonly work, which this
decision does not treat as architectural evidence. Nothing in this ADR forecloses a future,
separately evidenced decision approving mandatory or optional polarity for a richer Verification
layer.

### Candidate C (necessity left unspecified) — why not selected

Leaving polarity necessity unspecified would have remained a safe choice, and this ADR does not
treat that option as wrong. It is not chosen because the evidence available is asymmetric enough
to resolve the narrower question responsibly: no evidence demonstrates that a mandatory opposed-
orientation dimension is semantically necessary for the minimum judgment contract, and the
minimum-contract rule governing this codebase's Verification decisions — do not add unsupported
mandatory dimensions to the minimum semantic contract, while future richer extensions remain
available under their own, separately evidenced decisions — permits resolving that narrower
question now, as `NOT_REQUIRED`, rather than leaving it open indefinitely.

### Relationship to ADR-0016 and ADR-0019 — precedent classification

ADR-0016 (rejecting a consequence collection as the minimum subject) and ADR-0019 (rejecting
multi-subject minimum request transport) are referenced here only as analogous architectural
decision pattern, not as identical evidence, the same semantic question, or direct authority for
polarity. ADR-0016 addressed its own evidence about subject granularity; ADR-0019 addressed its
own evidence about request cardinality; neither addressed polarity. The only thing reused from
them is the general pattern: unsupported mandatory dimensions are not added to the minimum
contract, while future richer extensions remain possible under separate evidence. This ADR does
not claim identical evidential conditions with either.

### Evaluation precedent — classification

Where the adjacent Evaluation architecture (`EvaluationStatus.JUDGED` / `NO_JUDGMENT` together with
a free-text `utility_judgment`) is relevant to this ADR's reasoning, it is classified strictly as
`ADJACENT_ARCHITECTURE_PRECEDENT`. It is not normative Verification authority, and it is not used
here as proof that Verification must be non-polar. It illustrates only that an accepted judgment
category elsewhere in this codebase does not universally require a fixed polarity dimension to
remain meaningful — nothing more.

### Semantic content preserved

This decision does not empty a successful determination of meaning. A successful minimum
Verification judgment remains, exactly as ADR-0020 froze it, a correctness/validity determination
concerning one minimum subject within its applicable derivation-context scope. This decision
removes only a mandatory opposed-orientation requirement from that minimum contract; it does not
remove, weaken, or redefine the judgment's underlying semantic content.

### Polarity topology

Because polarity is not required by the minimum contract,
`POLARITY_TOPOLOGY_NOT_REQUIRED_FOR_MINIMUM_CONTRACT`. This ADR does not select `binary`,
`finite`, or `open/non-enumerated` as a future topology, and it does not state that no future
topology may ever exist. Topology selection, if polarity is ever separately approved for a richer
layer, remains entirely for that future, separate decision.

### Output representation remains unresolved

`OUTPUT_REPRESENTATION_REMAINS_UNRESOLVED`. This ADR does not approve `bool`, `str`, an `Enum`, a
`status` field, a `judgment` field, a payload shape, a score, or a confidence value as the
representation of a successful determination.

### Non-success remains deferred

`NON_SUCCESS_SEMANTICS_REMAIN_DEFERRED` and `VERIFICATION_TOTALITY_NOT_ESTABLISHED`, exactly as
prior ADRs left them. This ADR does not decide whether a future unfavorable correctness/validity
determination constitutes success, non-success, or anything else; polarity necessity and
non-success semantics remain independent, separately undecided questions.

### Result envelope cardinality

`RESULT_ENVELOPE_CARDINALITY_REMAINS_DEFERRED`. This ADR does not infer any result container
topology or shape from the decision recorded here.

### Correlation preserved

`A1_PARTIAL_CARRIER_SEMANTICS_APPROVED`, `A1_COMPLETE_CORRELATION_SEMANTICS_NOT_APPROVED`, and
`COMPLETE_CORRELATION_REPRESENTATION_REMAINS_UNREADY` all remain exactly as ADR-0018 and
ADR-0020 left them. This ADR does not extend, narrow, or touch ADR-0018's carrier semantics.
`NO_CURRENT_POLARITY_CORRELATION_DEPENDENCY_ESTABLISHED`: no accepted authority establishes a
dependency between the minimum polarity requirement decided here and correlation completeness, and
this ADR does not claim that polarity and correlation are architecturally orthogonal — only that
no current dependency between them is established.

### Target boundary preserved

`TARGET_FUTURE_CORRELATION_ROLE_REMAINS_UNRESOLVED`. This ADR does not add target to the minimum
polarity requirement decision in any form.

### Judgment basis / materialization preserved

`ADDITIONAL_BASIS_REMAINS_UNRESOLVED` and `MATERIALIZATION_REMAINS_DEFERRED`, exactly as prior
ADRs left them. This ADR does not decide what sustains a correctness/validity determination, and
it does not approve any resolver.

### Structural contracts

Not approved: `VerificationRequest`, `VerificationResult`, `VerificationStatus`.
`REQUEST_STRUCTURAL_DISCOVERY` and `RESULT_STRUCTURAL_DISCOVERY` remain **BLOCKED**.
`STRUCTURAL_CONTRACTS_REMAIN_BLOCKED`. This ADR does not run a full structural-prerequisite
readiness review; it resolves only the minimum polarity requirement question.

### Execution

`VERIFICATION_EXECUTION_REMAINS_BLOCKED`. `OPERATION_JUDGMENT_CARDINALITY_REMAINS_DEFERRED`. This
ADR does not approve `VerificationExecutor`, `VerificationPort`, a `VerificationEngine`
implementation, `VerificationService`, `VerificationPolicy`, `VerificationAdapter`, or
`VerificationExecutionError`.

### World Model / Prediction-Counterfactual execution

World Model production remains **BLOCKED** by ADR-0006. Prediction / Counterfactual Implementation
Gate item 4 (execution port) remains **PARKED/BLOCKED**. Neither is altered by this ADR.

### Provider independence

This decision is independent of any LLM, `ModelRouter`, provider, prompt, temperature, tooling,
JSON schema, or model confidence, consistent with ADR-0002.

### Output prerequisite impact

Mandatory polarity is no longer a required unresolved dimension of the minimum successful judgment
contract. This does not mean output semantics are fully resolved, that structural discovery is
ready, or that a result shape is ready. Output representation, non-success semantics, Verification
totality, result-envelope cardinality, and complete correlation representation all remain
unresolved/deferred exactly as before this ADR.

### Minimum-novelty rationale

The minimum Verification semantic contract should contain only semantic dimensions demonstrated to
be necessary. ADR-0020 already provides a meaningful successful judgment atom — one
correctness/validity determination concerning one minimum subject, within its derivation-context
scope. No accepted Verification authority demonstrates that opposed orientation is required for
that minimum atom to remain meaningful. Making polarity mandatory would therefore add an
unsupported invariant to the minimum contract. Leaving future richer polarity semantics possible,
rather than foreclosing them, preserves reversibility toward whatever shape a future, separately
evidenced decision might approve.

### Reversibility

This decision is reversible toward richer future semantics because `NOT_REQUIRED` does not mean
`FORBIDDEN` everywhere. A future, separately evidenced Verification layer may add a polarity
dimension — binary, finite, or open — without contradicting this ADR. This ADR does not approve
any such future layer; it only records that none of them would need to contradict or retract the
decision made here.

### Decision summary

| Concern | Decision |
| --- | --- |
| Successful minimum judgment atom | One correctness/validity determination (unchanged, ADR-0020) |
| Mandatory polarity in minimum judgment | Not required |
| Polarity prohibited | No |
| Future richer polarity | Not prohibited; separate future decision |
| Minimum polarity topology | Not required |
| Concrete polarity vocabulary | Not approved |
| Output representation | Unresolved |
| Non-success | Deferred |
| Totality | Not established |
| Result envelope | Deferred |
| Complete correlation | Unready |
| Structural contracts | Blocked |
| Execution | Blocked |

## Not Decided Here

- any polarity vocabulary
- binary polarity
- finite polarity taxonomy
- open polarity/judgment topology
- richer future polarity semantics
- output field
- output type
- status vocabulary
- output representation
- non-success semantics
- totality
- result envelope
- complete correlation representation
- target future role
- judgment basis
- materialization
- structural contracts
- execution

## Consequences

**Positive:**

- The minimum Verification semantic contract no longer carries an unsupported mandatory polarity
  invariant.
- The decision preserves full reversibility toward any future richer polarity semantics.
- ADR-0020's successful judgment atom, and every other prior Verification decision, remains
  reused without modification or reinterpretation.
- No speculative structure, vocabulary, or topology is introduced.
- The narrow scope of this decision keeps it independent of representation, non-success, totality,
  result-envelope cardinality, and complete correlation representation.

**Tradeoff:**

- The output-semantic prerequisite ADR-0015 identified remains only partially resolved; structural
  contract discovery remains blocked.
- A future decision may still need to determine whether any particular richer Verification layer
  is polar, and if so, its topology and vocabulary — none of that work is done by this ADR.
- The relationship between a future unfavorable determination and non-success remains an open
  question for a separate future decision.

## ADR Relationship

ADR-0021 complements ADR-0015, ADR-0016, ADR-0017, ADR-0018, ADR-0019, and ADR-0020. It resolves
only the minimum polarity requirement question — whether polarity is mandatory for the minimum
successful judgment — and does not supersede any of their other decisions. ADR-0020 remains
authoritative for the successful judgment atom itself; the prior unresolved polarity state ADR-0020
recorded is narrowed by this ADR only for the mandatory minimum-requirement question, not
resolved in full.
