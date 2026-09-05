# ADR-0024: Verification Minimum Result-Envelope Cardinality Requirement Semantics

- Status: Accepted
- Date: 2026-09-05

> Status `Accepted` records that the semantic decision this ADR carries has already been approved by
> its decision review (M0-15GS). While this ADR remains only on its local topic branch, it is an
> **approved decision / local ADR draft**, not yet **accepted `main` authority**. It does not become
> accepted `main` authority until merged into `main`.

## Context

ADR-0015 froze Verification's minimum V1 semantic category — correctness/validity of derived
content, evaluated within the derivation context under which that content was produced — and
deferred all output semantics. ADR-0016 froze the first/minimum Verification subject as one
individual Prediction / Counterfactual consequence item. ADR-0018 froze a partial, explicit-axis-
scoped correlation semantics for that subject, while leaving complete correlation representation
unready. ADR-0019 froze that a minimum Verification request transports exactly one instance of the
minimum subject, keeping request transport cardinality distinct from operation cardinality and
result cardinality.

ADR-0020 froze what minimally exists when Verification succeeds in producing a correctness/validity
judgment: one correctness/validity determination concerning one minimum subject, within the
subject's applicable derivation-context scope. ADR-0020 explicitly distinguished semantic judgment
cardinality from result-envelope cardinality — "one" determination does not mean "one result
envelope, one result object, one field, one enum member, one string, one boolean" — and recorded,
unresolved, `RESULT_ENVELOPE_CARDINALITY_REMAINS_DEFERRED`. ADR-0021 resolved that minimum mandatory
polarity is `NOT_REQUIRED`. ADR-0022 resolved that minimum mandatory totality is `NOT_REQUIRED`.
ADR-0023 resolved that no specific output content topology is required by the minimum. None of
ADR-0021, ADR-0022, or ADR-0023 addressed result-envelope cardinality; each preserved
`RESULT_ENVELOPE_CARDINALITY_REMAINS_DEFERRED` exactly where ADR-0020 had left it, and ADR-0023
explicitly recorded that content topology and result-envelope topology remain independent,
separately deferred questions.

A sequence of read-only process gates (M0-15GQ through M0-15GS) identified and narrowed result-
envelope cardinality as the next legitimate Verification semantic frontier. That work established,
without deciding representation: that the question is genuinely semantic, requirement-level only,
and isolable from non-success existence, totality, operation cardinality, request transport
cardinality, and content topology; that no accepted authority demonstrates a specific result-
envelope cardinality is necessary for the successful minimum judgment atom's semantic legitimacy;
and that the successful judgment atom (ADR-0020) is itself directly and repeatedly described, across
six independently-authored accepted ADRs (ADR-0018 through ADR-0023), as not implying any result
container topology, one-to-one request/result relationship, or result shape. A subsequent decision
review (M0-15GS) evaluated three positions — a specific result-envelope cardinality required by the
minimum (R1), no specific result-envelope cardinality required by the minimum (R0), and the
requirement left unresolved (RU) — against that evidence and against the accepted minimum-contract
decision methodology, and approved R0. This ADR records the result of that approval. It does not
reopen the discovery or the review, and it does not create any production contract.

Process gate reports (M0-15GQ–GS) are cited here only as process history establishing how this
question was narrowed. They are not architectural authority. This ADR's decision rests on accepted
architecture (ADR-0015 through ADR-0023) and on the approved M0-15GS review, not on the gate reports
themselves.

## Decision

### Minimum result-envelope cardinality requirement

The minimum successful Verification semantic contract does **not** require commitment to any one
particular result-envelope cardinality invariant for carrying its one successful correctness/
validity judgment.

Conceptually: `NO_SPECIFIC_RESULT_ENVELOPE_CARDINALITY_REQUIRED_BY_MINIMUM`.

This is a **requirement-level** decision. It concerns only whether committing to one specific
result-envelope cardinality is one of the mandatory semantic invariants of the minimum successful
Verification contract. It says nothing about which cardinality, if any, a future concrete or richer
representation will actually use — every future concrete representation will naturally carry some
definite cardinality; this ADR freezes only that the minimum contract does not mandate one such
cardinality as an invariant.

### "Not required" precision — critical boundary

This ADR freezes `NOT_REQUIRED`. It does **not** freeze, and explicitly distinguishes this decision
from, every one of the following: `NO_RESULT_ENVELOPE`, `NO_RESULT`, `NO_OUTPUT`, `NO_CONTAINER`,
`ARBITRARY_CARDINALITY`, `ANY_CARDINALITY_IS_VALID`, `ZERO_OR_ONE`, `EXACTLY_ONE`, `ONE_OR_MORE`,
`ZERO_OR_MORE`, `MULTIPLE`, `COLLECTION`. Accordingly, this ADR does **not** state or imply any of:

- "a successful Verification judgment has no result envelope";
- "no result exists";
- "no output exists";
- "any cardinality whatsoever satisfies the minimum contract";
- "the result envelope may be arbitrary";
- "the envelope is exactly one, zero-or-one, one-or-more, zero-or-more, or a collection".

The precise and only meaning frozen here: **committing to one specific result-envelope cardinality
is not one of the mandatory semantic invariants of the minimum successful Verification contract.**
A future concrete or richer representation may still use a definite cardinality; this decision does
not forbid one, it only declines to make one mandatory now (see "Future richer result-envelope
cardinality" below).

### Exact result-envelope cardinality remains open

No exact result-envelope cardinality is selected by this ADR. None of `EXACTLY_ONE`, `ZERO_OR_ONE`,
`ONE_OR_MORE`, `ZERO_OR_MORE`, `MULTIPLE`, or any other candidate cardinality is approved, named, or
implied as the eventual value. This ADR does not invent or imply a structural container. Whether,
and which, exact cardinality a future concrete representation adopts remains entirely for a
separate, future, evidenced decision — one this ADR does not attempt and does not foreclose.

### Future richer result-envelope cardinality

`FUTURE_RICHER_RESULT_ENVELOPE_CARDINALITY_NOT_PROHIBITED`.

A future, separately evidenced Verification capability may adopt a particular result-envelope
cardinality without contradicting this ADR. `NOT_REQUIRED` at the minimum level does not forbid a
stricter commitment at a higher, separately decided level.
`NO_SPECIFIC_RESULT_ENVELOPE_CARDINALITY_REQUIRED_BY_MINIMUM` does **not** mean
`NO_RESULT_ENVELOPE`: a concrete Verification capability will
necessarily produce some definite result-envelope shape when it is eventually built; this ADR
freezes only that no particular shape is a mandatory invariant of the minimum semantic contract
today. This ADR does not identify which cardinality should eventually be adopted.

### ADR-0020 relationship — semantic judgment atom preserved

`ONE_SUCCESSFUL_CORRECTNESS_VALIDITY_DETERMINATION_PER_MINIMUM_VERIFICATION_JUDGMENT` remains the
authoritative, unchanged description of the minimum successful Verification judgment (ADR-0020).
This ADR does not redefine the successful judgment, the minimum subject, the undifferentiated
correctness/validity axis, the derivation-context scope, or semantic judgment cardinality.

`ONE_DETERMINATION != ONE_RESULT_ENVELOPE`, exactly as ADR-0020 already established: "one"
determination freezes semantic judgment cardinality only; it does not mean one result envelope, one
result object, one field, one string, or one enum member. This ADR does not convert one
determination into one result. The semantic judgment atom remains fully meaningful and coherent
independently of any mandatory result-envelope-cardinality commitment — ADR-0020's own text records
that the atom "does not imply... any result container topology, one-to-one request/result
relationship, or result shape."

### ADR-0019 relationship — request cardinality distinct

`ONE_SUBJECT_PER_MINIMUM_VERIFICATION_REQUEST` (ADR-0019) is preserved, unchanged, and not reopened.
Request transport cardinality != result-envelope cardinality: ADR-0019 itself explicitly declines to
infer any request-to-result one-to-one relationship from its own decision. This ADR does not infer
one request = one result. ADR-0019's disciplined decision pattern — resolving a cardinality question
only on positively demonstrated necessity, without inferring it from an adjacent, already-decided
cardinality dimension — is reused here only as `METHODOLOGICAL_OR_ADJACENT_PRECEDENT`, not as
substantive result-envelope authority.

### ADR-0021 / ADR-0022 methodology — precedent classification

ADR-0021 (minimum polarity requirement) and ADR-0022 (minimum totality requirement) are classified
here as `ACCEPTED_MINIMUM_REQUIREMENT_DECISION_METHODOLOGY`. Neither is substantive result-envelope-
cardinality authority, and this ADR does not state that polarity `NOT_REQUIRED` or totality
`NOT_REQUIRED` themselves imply result-envelope cardinality `NOT_REQUIRED`. Only their accepted
decision discipline is reused:

- the already-approved successful judgment atom (ADR-0020) remains meaningful without a mandatory
  result-envelope-cardinality invariant;
- no accepted authority demonstrates that committing to a specific result-envelope cardinality is
  necessary for that atom's semantic legitimacy;
- the minimum semantic contract therefore does not add that unsupported mandatory invariant;
- richer future decisions, adopting a specific cardinality under their own evidence, remain possible.

This ADR's decision does not rest on "no evidence for a mandatory cardinality was found, therefore
none is required." It rests positively on the independent, result-envelope-specific textual finding,
reaffirmed across six accepted ADRs (ADR-0018 through ADR-0023), that the semantic judgment atom does
not imply or require any result container topology, combined with the absence of any accepted
authority demonstrating necessity for one.

### ADR-0023 relationship — content topology distinct

`NO_SPECIFIC_OUTPUT_CONTENT_TOPOLOGY_REQUIRED_BY_MINIMUM` (ADR-0023) is preserved, unchanged, and not
reopened. `CONTENT_TOPOLOGY != RESULT_ENVELOPE_CARDINALITY`: ADR-0023 itself explicitly records that
"content topology and result-envelope topology remain independent, separately deferred questions."
This ADR is not presented as a direct consequence of ADR-0023's semantic conclusion, and its decision
is not copied from ADR-0023. The relationship between the two is that both are independently scoped,
independently evidenced, requirement-level decisions addressing different dimensions of the same
output-semantic prerequisite set ADR-0015 originally identified.

### Prior deferred-status precision

Accepted ADRs (ADR-0018 through ADR-0023) currently record
`RESULT_ENVELOPE_CARDINALITY_REMAINS_DEFERRED`. This ADR narrows that prior open status **only** for
the single question: *is commitment to some specific result-envelope cardinality a mandatory
invariant of the minimum successful Verification semantic contract?* The answer to that question is
now `NOT_REQUIRED`. This ADR does not resolve which concrete result-envelope cardinality is
eventually used, and it does not claim that every future result-cardinality question is closed.

### Totality boundary

`TOTALITY_NOT_REQUIRED_BY_MINIMUM` (ADR-0022) is preserved and not reopened. Totality and result-
envelope cardinality are separate semantic axes. This ADR does not infer from totality, and does not
infer from its own decision toward totality, any of: `Optional`, `None`, zero-or-one results, result
absence, or one result carrying a status.

### Non-success boundary

`NON_SUCCESS_SEMANTICS_REMAIN_DEFERRED`, exactly as ADR-0015 through ADR-0023 left it. Process state
`NON_SUCCESS_EXISTENCE = PARKED_UNTIL_NEW_EVIDENCE` is preserved and not reopened by this ADR. This
ADR introduces no `NO_JUDGMENT`, `UNKNOWN`, `UNVERIFIED`, `FAILED`, `INDETERMINATE`, `Optional`,
`None`, or equivalent non-success vocabulary.

### Operation boundary

`OPERATION_JUDGMENT_CARDINALITY_REMAINS_DEFERRED`, exactly as prior ADRs left it. This ADR does not
infer one operation = one result, one operation = one judgment, or one request = one operation.

### Output / carrier boundary

`OUTPUT_REPRESENTATION_REMAINS_UNRESOLVED`, exactly as prior ADRs left it.
`SEMANTIC_CONTENT_TOPOLOGY != CONCRETE_CARRIER_FORM` (ADR-0023) is preserved. This ADR does not
select `str`, `bool`, `Enum`, an object, a value object, a structured payload, a reference/token, or
a tuple/list as any carrier, and it does not introduce a result carrier field.

### Result-structure boundary

This ADR does not create or approve `VerificationResult`, `VerificationStatus`, `ResultEnvelope`,
`VerificationOutput`, a result field, a status field, a payload field, or a collection field. The
semantic result-envelope-cardinality requirement resolved here is not the same question as, and does
not decide, concrete result structure.

### Materialization boundary

`MATERIALIZATION_REMAINS_DEFERRED`, exactly as prior ADRs left it.
`MATERIALIZATION_DEFERRED != OPAQUE_CARRIER_FORBIDDEN` (ADR-0023) is preserved. This ADR does not
choose between a self-contained or a reference/materialized output.

### Target / basis / correlation boundary

Unchanged and not reopened by this ADR: `ADDITIONAL_BASIS_REMAINS_UNRESOLVED`,
`TARGET_ASSOCIATION_REMAINS_UNRESOLVED`, `TARGET_FUTURE_CORRELATION_ROLE_REMAINS_UNRESOLVED`,
`DERIVATION_CONTEXT_NOT_EXHAUSTIVELY_DEFINED`, `A1_PARTIAL_CARRIER_SEMANTICS_APPROVED`,
`A1_COMPLETE_CORRELATION_SEMANTICS_NOT_APPROVED`,
`COMPLETE_CORRELATION_REPRESENTATION_REMAINS_UNREADY`. This ADR introduces no new correlation
semantics.

### Structural contracts

Not approved: `VerificationRequest`, `VerificationResult`, `VerificationStatus`, `VerificationBasis`,
`VerificationContext`, `VerificationTarget`. `REQUEST_STRUCTURAL_DISCOVERY` and
`RESULT_STRUCTURAL_DISCOVERY` remain **BLOCKED**. `STRUCTURAL_CONTRACTS_REMAIN_BLOCKED`. This ADR
alone does not run a structural-readiness review and does not unblock structural work.

### Execution

`VERIFICATION_EXECUTION_REMAINS_BLOCKED`. This ADR does not approve `VerificationExecutor`,
`VerificationPort`, a `VerificationEngine` implementation, `VerificationService`,
`VerificationPolicy`, or a `VerificationAdapter`.

### Parked threads

Process state preserved, not reopened, and not treated as evidence by this ADR: judgment basis —
`PARKED_UNTIL_NEW_EVIDENCE`; non-success existence — `PARKED_UNTIL_NEW_EVIDENCE`; target correlation
— `PARKED_UNTIL_NEW_EVIDENCE`; target scoping — `PARKED_UNTIL_NEW_EVIDENCE`. This ADR's decision does
not constitute new evidence reopening any of them.

### Provider independence

This decision is independent of any LLM, `ModelRouter`, provider, prompt, temperature, tooling, JSON
schema, or model confidence, consistent with ADR-0002.

### Single semantic increment

`ONE_NEW_VERIFICATION_RESULT_ENVELOPE_CARDINALITY_REQUIREMENT_INCREMENT_FAMILY`. This ADR contains
exactly one new semantic increment family: the minimum mandatory result-envelope-cardinality
requirement is `NOT_REQUIRED`. Everything else in this ADR is a scope boundary, preserved prior
authority, rationale, or future-compatibility statement. No exact cardinality, result structure,
concrete carrier, non-success semantics, status vocabulary, operation cardinality, request/result
mapping, materialization, target role, or complete correlation is introduced or decided.

### Minimum-novelty rationale

The minimum Verification semantic contract should carry only invariants demonstrated to be
necessary. ADR-0020 already supplies a meaningful successful judgment atom. Accepted authority
explicitly separates that atom from result-envelope cardinality — "one" determination does not mean
one result envelope (ADR-0020), and semantic cardinality is distinct from structural cardinality
(ADR-0023). The semantic legitimacy of that atom does not depend on resolving a specific result-
envelope cardinality: ADR-0020's atom is directly described as not implying any result container
topology, one-to-one request/result relationship, or result shape, and this independence is
reaffirmed, in the authors' own words, across ADR-0018 through ADR-0023. No accepted Verification
authority demonstrates that committing to a specific result-envelope cardinality is necessary for
that atom to remain meaningful. Freezing a mandatory result-envelope-cardinality invariant would
therefore add an unsupported invariant to the minimum contract. Therefore the minimum does not
require one. Future richer cardinality remains possible under its own, separately evidenced
decision.

### Reversibility

`NOT_REQUIRED` does not mean `FORBIDDEN`. A future, separately evidenced representation may use a
definite result-envelope cardinality without retracting this ADR, provided it is not claimed to be a
mandatory invariant of this same minimum contract absent a new architectural decision. This ADR does
not approve any such future representation; it records only that none of them would need to
contradict or retract the decision made here.

### Decision summary

| Concern | Decision |
| --- | --- |
| Successful judgment atom | Unchanged (ADR-0020) |
| Minimum result-envelope cardinality requirement | Not required |
| Exact result-envelope cardinality | Not selected / unresolved |
| Future richer result-envelope cardinality | Not prohibited |
| Request cardinality | Unchanged (ADR-0019) |
| Operation cardinality | Deferred |
| Totality | Not required, unchanged (ADR-0022) |
| Content topology | Not required, unchanged (ADR-0023) |
| Non-success | Deferred |
| Concrete result structure | Not approved |
| Output representation | Unresolved |
| Materialization | Deferred |
| Complete correlation | Unready |
| Structural contracts | Blocked |
| Execution | Blocked |

## Not Decided Here

- exact result-envelope cardinality
- result object shape
- `VerificationResult`
- `VerificationStatus`
- result fields
- output carrier
- output content topology (see ADR-0023)
- non-success semantics
- non-success existence
- request/result mapping
- operation/result mapping
- operation cardinality
- materialization / resolution
- target's future Verification role
- judgment basis
- complete correlation representation
- structural contracts
- execution topology
- persistence
- API / serialization

## Consequences

**Positive:**

1. One unnecessary mandatory design axis — a specific result-envelope cardinality — is removed from
   the minimum Verification semantic contract.
2. The successful judgment atom (ADR-0020) and every other prior Verification decision are reused
   without modification or reinterpretation.
3. Future result-envelope cardinality and structural flexibility are preserved: no premature
   container, field, or shape is introduced.
4. No speculative structure is introduced by this ADR.
5. The narrow scope of this decision keeps it independent of non-success, content topology,
   judgment basis, target role, complete correlation, and operation cardinality.

**Tradeoff:**

1. Concrete result structure remains entirely unresolved; no `VerificationResult` shape can yet be
   written from this ADR alone.
2. Structural contracts and execution remain entirely blocked; this ADR does not narrow that
   blocker.
3. A future richer or specialized Verification layer, if it needs a specific result-envelope
   cardinality, will require its own separate, evidenced decision.
4. Non-success semantics and output representation remain unresolved, so a complete Verification
   output cannot yet be specified end to end.

## ADR Relationship

ADR-0024 complements ADR-0015 through ADR-0023. It narrows only the result-envelope-cardinality
**requirement** question — whether the minimum successful Verification semantic contract mandates
one specific result-envelope cardinality — and answers it `NOT_REQUIRED`. It supersedes none of
them. ADR-0020 remains authoritative for the successful judgment atom itself; ADR-0019 remains
authoritative for request transport cardinality; ADR-0021 remains authoritative for the minimum
polarity requirement; ADR-0022 remains authoritative for the minimum totality requirement; ADR-0023
remains authoritative for the minimum output content topology requirement. This ADR does not reopen,
narrow, or extend any of those decisions — it resolves only the additional, narrower result-
envelope-cardinality-requirement question that ADR-0020 left open and that ADR-0021/0022/0023 did
not address.
