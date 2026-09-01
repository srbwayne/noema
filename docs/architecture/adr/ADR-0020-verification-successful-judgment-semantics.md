# ADR-0020: Verification Successful Judgment Semantics

- Status: Accepted
- Date: 2026-08-28

## Context

ADR-0015 froze Verification's minimum V1 semantic category — correctness/validity of derived
content — and established that this correctness/validity is evaluated within the derivation
context under which the content was produced. ADR-0015 explicitly deferred output semantics: it
approved no concrete output representation and inferred none from "correctness," "validity,"
"verified," or "verification_status."

ADR-0016 froze the first/minimum Verification subject as one individual Prediction /
Counterfactual consequence item, keeping derivation context distinct from that subject. ADR-0017
preserved correctness/validity as one undifferentiated semantic axis and froze the minimum
explicit derivation-context axes without exhausting derivation context. ADR-0018 froze a partial,
explicit-axis-scoped correlation semantics for that subject. ADR-0019 froze that a minimum
Verification request transports exactly one instance of the minimum subject, a request-transport
concern distinct from subject cardinality, judgment cardinality, and result-envelope cardinality.

None of ADR-0015 through ADR-0019 addressed what minimally exists when Verification succeeds in
producing a correctness/validity judgment. A sequence of read-only architectural discoveries
examined exactly this gap. That work found that the judgment category itself — "Verification
concerns correctness/validity" — does not by itself define what a successful judgment
semantically yields, distinguished the semantic question ("what does a successful judgment mean")
from the representational question ("how is that meaning encoded"), and found that a minimum
semantic decision — one correctness/validity determination concerning one minimum subject, within
its applicable derivation-context scope — is positively supported, minimally novel, and
independent of polarity and representation, while polarity itself remains unsupported by any
current authority. A subsequent review evaluated that candidate against alternatives requiring
binary polarity, a finite taxonomy, an open-ended judgment space, or no semantic payload at all,
and approved only the minimal candidate. This ADR records the result of that approval. It does not
reopen that discovery or review, and it does not create any production contract.

## Decision

### Successful minimum Verification judgment atom

A successful minimum Verification judgment semantically consists of **one correctness/validity
determination concerning one minimum Verification subject, within the applicable
derivation-context scope**.

Conceptually: `ONE_SUCCESSFUL_CORRECTNESS_VALIDITY_DETERMINATION_PER_MINIMUM_VERIFICATION_JUDGMENT`.

### "Successful" precision

"Successful" means only that a correctness/validity judgment was **semantically** produced. It
does not mean technical execution success, provider success, transport success, persistence
success, proof success, or ground-truth confirmation. No Verification technical execution
operation exists yet; this ADR does not create one.

### "Determination" precision

"Determination" means only the produced correctness/validity judgment itself. It does not imply
formal proof, theorem proving, entailment, certainty, confidence, probability, ground truth,
actuality correspondence, binary truth, factual occurrence, or technical success. This ADR does
not introduce any of those concepts into Verification semantics.

### Subject boundary

The determination concerns exactly the subject ADR-0016 already froze: one individual Prediction /
Counterfactual consequence item. This ADR does not add `target_ref`, `baseline_ref`,
`divergence_refs`, a context object, subject identity, or consequence identity to the subject
itself. The subject remains exactly what ADR-0016 defined; it is not redefined, widened, or
wrapped here.

### Context scope

The judgment remains scoped within the derivation context under which the subject was produced,
exactly as ADR-0015 established. This ADR does not redefine derivation context, does not claim
complete correlation, and does not make context part of the subject. "Within the applicable
derivation-context scope" restates ADR-0015's existing scope boundary; it is not a new claim about
context composition or completeness.

### Undifferentiated axis preserved

`CORRECTNESS_VALIDITY_REMAINS_UNDIFFERENTIATED`, exactly as ADR-0017 established. This ADR does
not introduce a correctness mode, a validity mode, a separate correctness judgment, a separate
validity judgment, two fields, or two outputs. One determination covers the one undifferentiated
axis.

### "One" determination precision

The word "one" freezes semantic judgment cardinality at the minimum judgment-atom level only. It
does not mean one result envelope, one result object, one field, one enum member, one string, one
boolean, one request per operation, one operation per request, or one operation per subject. Each
of those remains a separate, independently deferred dimension, addressed below.

### Polarity remains unresolved

`POLARITY_REMAINS_UNRESOLVED`. This ADR does not approve `correct`/`incorrect`,
`valid`/`invalid`, `verified`/`unverified`, `true`/`false`, `pass`/`fail`,
`positive`/`negative`, or any equivalent pairing. It does not claim the determination's semantic
space is binary, finite, or open/non-enumerated. All three shapes remain equally undecided by this
ADR.

### Output representation remains unresolved

`OUTPUT_REPRESENTATION_REMAINS_UNRESOLVED`. This ADR does not approve `bool`, `str`, an `Enum`, a
`status` field, a `judgment` field, a payload field, a `tuple`, a `list`, an object, a value
object, an evidence set, or a score as the concrete representation of the determination.

### Negative judgment not frozen

Prior discovery found strong repository precedent, elsewhere in this domain, that an
unfavorable-sounding semantic conclusion need not by itself mean the absence of a valid result.
That finding was precedent informing the review; it is not adopted as Verification authority here.
This ADR does not freeze `NEGATIVE_JUDGMENT_DISTINCT_FROM_NO_JUDGMENT` or any comparable statement
as Verification semantics. It records only, as rationale, that whether a future unfavorable
correctness/validity determination would constitute non-success remains an open question for a
separate, future decision.

### Non-success remains deferred

`NON_SUCCESS_SEMANTICS_REMAIN_DEFERRED` and `VERIFICATION_TOTALITY_NOT_ESTABLISHED`, exactly as
prior ADRs left them. This ADR does not introduce `NO_JUDGMENT`, `UNKNOWN`, `UNVERIFIED`,
`INDETERMINATE`, `INSUFFICIENT_EVIDENCE`, `NOT_VERIFIABLE`, or any equivalent. Whether every
structurally valid future Verification request must yield a determination remains undecided.

### Result envelope cardinality

`RESULT_ENVELOPE_CARDINALITY_REMAINS_DEFERRED`. The semantic judgment atom frozen here does not
imply, and this ADR does not decide, any result container topology, one-to-one request/result
relationship, or result shape.

### Request transport preserved

ADR-0019 remains authoritative: `ONE_SUBJECT_PER_MINIMUM_VERIFICATION_REQUEST`. This ADR does not
infer from it, or from the decision recorded here, one judgment per operation, one result per
request, or one operation per request. Request transport cardinality, judgment cardinality, and
result-envelope cardinality remain three independent dimensions.

### Correlation preserved

`A1_PARTIAL_CARRIER_SEMANTICS_APPROVED`, `A1_COMPLETE_CORRELATION_SEMANTICS_NOT_APPROVED`,
`COMPLETE_CORRELATION_REPRESENTATION_REMAINS_UNREADY`, and
`COMPLETE_CORRELATION_THREAD_PARKED_FOR_LACK_OF_CONCRETE_ADDITIONAL_COVERAGE_EVIDENCE` all remain
exactly as ADR-0018 and subsequent discovery left them. This ADR does not solve correlation and
does not extend, narrow, or touch ADR-0018's carrier semantics.

### Target boundary preserved

`TARGET_NOT_CONFIRMED_AS_DERIVATION_CONTEXT_MEMBER`, `TARGET_DISTINCT_SEMANTIC_ROLE`, and
`TARGET_FUTURE_CORRELATION_ROLE_REMAINS_UNRESOLVED` all remain unchanged. This ADR does not add
target to successful judgment semantics in any form.

### Judgment basis preserved

`ADDITIONAL_BASIS_REMAINS_UNRESOLVED`, exactly as ADR-0017 left it. The existence of a
determination, frozen here, does not establish what evidence, knowledge, rules, proof, or basis
sustains it. This ADR answers only what exists when a judgment succeeds, not what makes that
judgment sound.

### Materialization preserved

`MATERIALIZATION_REMAINS_DEFERRED`. No resolver or materializer of any kind is approved by this
ADR.

### Provenance / Epistemic boundary preserved

Existing ownership is preserved without modification. This ADR does not make confidence,
`EpistemicStatus`, supporting evidence, counter evidence, or provenance validation part of the
minimum determination.

### Score / confidence excluded

Confidence, probability, score, utility, ranking, and certainty are explicitly excluded from this
decision. None is part of the successful judgment atom frozen here.

### Output prerequisite status — critical

This ADR narrows the output-semantic prerequisite ADR-0015 identified. It does not complete it.
After this ADR:

- successful judgment atom: **DECIDED**;
- polarity / semantic topology: **UNRESOLVED**;
- concrete output representation: **UNRESOLVED**;
- non-success semantics: **DEFERRED**;
- Verification totality: **NOT ESTABLISHED**;
- result-envelope cardinality: **DEFERRED**.

Structural contract discovery therefore remains **BLOCKED**. This ADR does not claim the output
prerequisite is fully closed.

### Structural contracts

Not approved: `VerificationRequest`, `VerificationResult`, `VerificationStatus`.
`REQUEST_STRUCTURAL_DISCOVERY` and `RESULT_STRUCTURAL_DISCOVERY` remain **BLOCKED**. Structural
contracts generally remain **BLOCKED**.

### Execution

Verification execution remains **BLOCKED**. This ADR does not approve `VerificationExecutor`,
`VerificationPort`, a `VerificationEngine` implementation, `VerificationService`,
`VerificationPolicy`, `VerificationAdapter`, or `VerificationExecutionError`.
`OPERATION_JUDGMENT_CARDINALITY_REMAINS_DEFERRED` is preserved.

### World Model / Prediction-Counterfactual execution

World Model production remains **BLOCKED** by ADR-0006. Prediction / Counterfactual Implementation
Gate item 4 (execution port) remains **PARKED/BLOCKED**. Neither is altered by this ADR.

### Provider independence

This decision is independent of any LLM, `ModelRouter`, provider, prompt, temperature, tooling,
JSON schema, or model confidence, consistent with ADR-0002.

### Minimum-novelty rationale

ADR-0015 answered what semantic category Verification owns: correctness/validity of derived
content. This ADR answers what minimally exists when a successful judgment of that category is
produced: exactly one determination, concerning exactly one subject, within the subject's
applicable derivation-context scope. It does not answer what polarity that determination has, what
representation encodes it, what result structure carries it, what status discriminates it, or what
non-success state might apply instead of it. Each of those remains a separate, future decision.

### Reversibility

One semantic determination, as frozen here, remains fully compatible with a future decision
approving binary polarity, a finite categorical topology, or open/non-enumerated judgment content,
and with any future concrete representation or future non-success state built on top of it. This
ADR does not approve any of those; it only records that none of them would need to contradict or
retract the decision made here.

### Decision summary

| Concern | Decision |
| --- | --- |
| Verification judgment category | Correctness/validity of derived content (unchanged, ADR-0015) |
| Minimum subject | One individual P/C consequence item (unchanged, ADR-0016) |
| Successful minimum judgment atom | One correctness/validity determination concerning one minimum subject, within its derivation-context scope |
| Successful semantic judgment cardinality | Exactly one determination per minimum judgment |
| Correctness/validity differentiation | Undifferentiated (unchanged, ADR-0017) |
| Polarity | Unresolved |
| Output representation | Unresolved |
| Non-success semantics | Deferred |
| Verification totality | Not established |
| Result envelope cardinality | Deferred |
| Complete correlation | Partial explicit-axis correlation approved; complete semantics not approved; representation remains unready (ADR-0018) |
| Judgment basis | Unresolved (unchanged, ADR-0017) |
| Structural contracts | Blocked |
| Execution | Blocked |

## Not Decided Here

- polarity
- binary vs. finite vs. open semantic topology
- concrete output representation
- output field name
- output type
- status vocabulary
- non-success semantics
- totality
- result cardinality
- result structure
- complete correlation representation
- target correlation role
- judgment basis
- evidence/proof representation
- provenance
- materialization
- execution topology
- persistence
- API/serialization

## Consequences

**Positive:**

- Verification's successful output now has a positive minimum semantic existence instead of being
  entirely undefined.
- The decision is independent of polarity and representation, so it does not foreclose any future
  shape for the determination's value space.
- Subject, context-scope, and undifferentiated-axis boundaries from ADR-0015/0016/0017 are reused
  without modification or reinterpretation.
- No speculative structure, field, or type is introduced.
- The decision composes cleanly with ADR-0018's partial correlation and ADR-0019's request
  transport cardinality without touching either.

**Tradeoff:**

- The output-semantic prerequisite ADR-0015 identified remains only partially resolved; structural
  contract discovery remains blocked.
- Polarity and representation remain fully open, so no concrete `VerificationResult` shape can yet
  be written from this ADR alone.
- Non-success semantics and totality remain unresolved, so a complete Verification operation cannot
  yet be specified end to end.
- The relationship between a future unfavorable determination and non-success remains an open
  question for a separate future decision.

## ADR Relationship

ADR-0020 complements ADR-0015, ADR-0016, ADR-0017, ADR-0018, and ADR-0019. ADR-0015 remains
authoritative for the correctness/validity judgment category and the derivation-context scope
within which it is evaluated. ADR-0016 remains authoritative for the minimum subject. ADR-0017
remains authoritative for the undifferentiated semantic axis and the non-exhaustiveness of
derivation context. ADR-0018 remains authoritative for the partial explicit-axis correlation
semantics. ADR-0019 remains authoritative for minimum request transport cardinality. ADR-0020
resolves only the successful minimum judgment atom — what minimally exists when Verification
produces a correctness/validity determination — and supersedes none of the ADRs listed above.
