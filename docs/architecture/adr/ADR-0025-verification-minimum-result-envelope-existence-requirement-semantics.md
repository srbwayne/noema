# ADR-0025: Verification Minimum Result-Envelope Existence Requirement Semantics

- Status: Accepted
- Date: 2026-09-06

> Status `Accepted` records approval of the semantic decision by its decision review. Repository
> `main` authority is established by repository history and merge state, independently of this
> status label.

## Context

ADR-0015 froze the minimum V1 Verification semantic axis — correctness/validity of derived
content, evaluated within the derivation context under which that content was produced. ADR-0016
froze the first/minimum Verification subject as one individual Prediction / Counterfactual
consequence item. ADR-0019 froze that a minimum Verification request transports exactly one
instance of the minimum subject. ADR-0020 froze what minimally exists when Verification succeeds
in producing a correctness/validity judgment: one correctness/validity determination concerning
one minimum subject, within the subject's applicable derivation-context scope. ADR-0021 resolved
that minimum mandatory polarity is `NOT_REQUIRED`. ADR-0022 resolved that minimum mandatory
totality is `NOT_REQUIRED`. ADR-0023 resolved that no specific output content topology is required
by the minimum. ADR-0024 resolved that no specific result-envelope cardinality is required by the
minimum, while explicitly stating that it "neither requires nor forbids a future concrete
result-envelope construct" — leaving the narrower question of result-envelope *existence*
unaddressed by name.

A sequence of read-only process gates (M0-15HN through M0-15HP) identified and narrowed exactly
this residual question. M0-15HN selected result-envelope existence as the next legitimate
Verification semantic frontier. M0-15HO established, without deciding representation, that the
question is genuinely semantic, isolable from carrier form, materialization, non-success
existence, judgment basis, target correlation/scoping, and operation cardinality, and that the
evidence base was sufficient for decision review. A subsequent decision review (M0-15HP)
evaluated three positions — a distinguishable result-envelope existence required by the minimum
(E1), not required by the minimum (E0), and the requirement left unresolved (EU) — against that
evidence, against ADR-0020's own affirmative definition of the successful judgment atom, and
against the accepted minimum-contract decision methodology, and approved E0. This ADR records the
result of that approval. It does not reopen the discovery or the review, and it does not create
any production contract.

Process gate reports (M0-15HN–HP) are cited here only as process history establishing how this
question was narrowed. They are not architectural authority. This ADR's decision rests on accepted
architecture (ADR-0015 through ADR-0024) and on the approved M0-15HP review, not on the gate
reports themselves.

## Decision

### Minimum result-envelope existence requirement

The minimum successful Verification semantic contract does **not** require the existence of a
distinguishable result-level envelope/container concept as one of its mandatory invariants.

Conceptually: `DISTINGUISHABLE_RESULT_ENVELOPE_EXISTENCE_NOT_REQUIRED_BY_MINIMUM`.

This is a **requirement-level** decision, and it applies only to `MINIMUM_SUCCESSFUL_VERIFICATION`.
It concerns only whether the existence of some enveloping/carrying construct, distinct from the
correctness/validity determination itself, is mandatory for the minimum contract. It says nothing
about which construct, if any, a future concrete or richer representation will actually use.

### "Not required" precision — critical boundary

This ADR freezes `NOT_REQUIRED`. It does **not** freeze, and explicitly distinguishes this decision
from, every one of the following: `NO_RESULT_ENVELOPE`, `RESULT_ENVELOPE_FORBIDDEN`, `NO_RESULT`,
`NO_OUTPUT`, `NO_CARRIER`, `BARE_RETURN_REQUIRED`. Precisely:

`NOT_REQUIRED != NO_RESULT_ENVELOPE`
`NOT_REQUIRED != RESULT_ENVELOPE_FORBIDDEN`
`NOT_REQUIRED != NO_RESULT`
`NOT_REQUIRED != NO_OUTPUT`
`NOT_REQUIRED != NO_CARRIER`
`NOT_REQUIRED != BARE_RETURN_REQUIRED`

Accordingly, this ADR does **not** state or imply any of:

- "Verification has no result";
- "Verification has no envelope";
- "Verification must return a bare value";
- "`VerificationResult` should not exist";
- "no object should be created";
- "there can never be a result envelope";
- "result cardinality no longer matters";
- "one request has no result".

The precise and only meaning frozen here: **mandatory result-envelope existence is not part of the
minimum successful Verification semantic contract.** A future concrete or richer representation may
still introduce a distinguishable result envelope; this decision does not forbid one, it only
declines to make one mandatory now.

### Semantic-vs-structural boundary — critical

`SEMANTIC_ENVELOPE_EXISTENCE_REQUIREMENT != STRUCTURAL_RESULT_OBJECT_EXISTENCE`. This ADR decides
only whether an enveloping *concept* is semantically mandatory. It does not approve, and does not
imply approval of, `VerificationResult`, `VerificationStatus`, `ResultEnvelope`,
`VerificationOutput`, a result field, a status field, a payload field, or a container field. No
class, object, schema, or type is created or implied by this ADR.
`DISTINGUISHABLE_RESULT_ENVELOPE_EXISTENCE_NOT_REQUIRED_BY_MINIMUM != VerificationResult_NOT_NEEDED`:
a structural contract may still later prove useful or necessary for implementation reasons; this
ADR does not decide that question in either direction.

### ADR-0020 relationship — atom completeness

`ONE_SUCCESSFUL_CORRECTNESS_VALIDITY_DETERMINATION_PER_MINIMUM_VERIFICATION_JUDGMENT` remains the
authoritative, unchanged description of the minimum successful Verification judgment (ADR-0020).
ADR-0020 defines the successful minimum judgment as consisting semantically of exactly three
elements: one correctness/validity determination; concerning one minimum subject; within its
applicable derivation-context scope. This ADR records that no fourth mandatory semantic
constituent — a distinguishable result envelope — is necessary for that atom's minimum semantic
completeness. ADR-0020 did not itself decide envelope existence; it left the question open. This
ADR is the new authority that resolves the requirement question — it does not retroactively
reinterpret ADR-0020 as having already decided it.

### Positive-evidence rationale — not an argument from silence

This ADR's decision does not rest on "no evidence for mandatory existence was found, therefore not
required." It rests positively on ADR-0020's own affirmative semantic definition of the atom, which
already provides a complete minimum successful judgment without naming envelope existence as a
constituent, despite ADR-0020's own precision language elsewhere explicitly engaging with
envelope-adjacent vocabulary ("does not mean one result envelope, one result object, one field...").
The absence of any accepted necessity witness for mandatory existence is secondary, corroborating
support only. `E0_RATIONALE = POSITIVE_DEFINITIONAL_COMPLETENESS`, not
`ARGUMENT_FROM_SILENCE`.

### Properties-vs-existence distinction — critical boundary

`INDEPENDENT_OF_ENVELOPE_PROPERTIES != INDEPENDENT_OF_ENVELOPE_EXISTENCE`. This ADR does not claim
that ADR-0023's or ADR-0024's independence statements — which address envelope *topology*,
*shape*, and *cardinality-value* — automatically imply this decision. `NO_SPECIFIC_RESULT_ENVELOPE_
CARDINALITY_REQUIRED_BY_MINIMUM` (ADR-0024) does not, by itself, logically imply
`DISTINGUISHABLE_RESULT_ENVELOPE_EXISTENCE_NOT_REQUIRED_BY_MINIMUM`. This ADR resolves the
existence requirement as a separate semantic increment, grounded independently in ADR-0020's atom
definition (see above), not derived from ADR-0023 or ADR-0024's properties-level conclusions.

### ADR-0024 relationship — existence distinct from cardinality

`NO_SPECIFIC_RESULT_ENVELOPE_CARDINALITY_REQUIRED_BY_MINIMUM` (ADR-0024) is preserved, unchanged,
and not reopened. `EXACT_RESULT_ENVELOPE_CARDINALITY = UNRESOLVED` remains exactly as ADR-0024 left
it. This ADR explicitly distinguishes `EXISTENCE_REQUIREMENT != EXACT_CARDINALITY`: ADR-0024 did
not already answer existence, and this ADR does not rewrite exact cardinality as resolved. Exact
cardinality remains a separate, still-open question, whose future relevance (if any) to the minimum
mandatory contract is left entirely to a later, separate determination.

### Future richer result envelope

`FUTURE_RICHER_RESULT_ENVELOPE_NOT_PROHIBITED`. A future, separately evidenced Verification design
may introduce a concrete result object, an envelope, a definite cardinality, or a richer
status/result structure. None is approved now. Such a future choice need not contradict this ADR,
because `NOT_REQUIRED` does not mean `FORBIDDEN`.

### Request boundary preserved

`ONE_SUBJECT_PER_MINIMUM_VERIFICATION_REQUEST` (ADR-0019) is preserved, unchanged, and not
reopened. `REQUEST_TRANSPORT_CARDINALITY != RESULT_ENVELOPE_EXISTENCE_REQUIREMENT`. This ADR does
not infer one request = one result, or one request = one envelope.

### Output representation boundary preserved

`OUTPUT_REPRESENTATION_REMAINS_UNRESOLVED`, exactly as prior ADRs left it. This ADR does not select
`str`, `bool`, `Enum`, an object, a value object, a structured payload, a reference/token, or a
tuple/list as any carrier. Envelope-existence non-requirement does not decide concrete carrier
form.

### Materialization boundary preserved

`MATERIALIZATION_REMAINS_DEFERRED`, exactly as prior ADRs left it.
`CARRIER_SELF_CONTAINMENT_FRONTIER_NOT_REOPENED`. This ADR does not choose self-contained,
materialized, opaque, reference-based, by-value, by-reference, or resolver-backed carrier
semantics. Envelope existence and materialization remain separate axes.

### Non-success boundary preserved

`NON_SUCCESS_SEMANTICS_REMAIN_DEFERRED`, exactly as ADR-0015 through ADR-0024 left it. Process
state `NON_SUCCESS_EXISTENCE = PARKED_UNTIL_NEW_EVIDENCE` is preserved and not reopened by this
ADR. This decision applies only to the successful minimum; it introduces no `NO_JUDGMENT`,
`UNKNOWN`, `UNVERIFIED`, `FAILED`, `INDETERMINATE`, `NOT_VERIFIABLE`, `Optional`, or `None`, and it
states nothing about whether any envelope would exist under a non-success condition.

### Operation boundary preserved

`OPERATION_JUDGMENT_CARDINALITY_REMAINS_DEFERRED`, exactly as prior ADRs left it. This ADR does not
infer one operation = one judgment, one operation = one result, one operation = one envelope, or
one request = one operation.

### Correlation / target boundary preserved

Unchanged and not reopened by this ADR: `TARGET_ASSOCIATION_REMAINS_UNRESOLVED`,
`TARGET_FUTURE_CORRELATION_ROLE_REMAINS_UNRESOLVED`, `A1_PARTIAL_CARRIER_SEMANTICS_APPROVED`,
`A1_COMPLETE_CORRELATION_SEMANTICS_NOT_APPROVED`, `COMPLETE_CORRELATION_REPRESENTATION_REMAINS_
UNREADY`, `DERIVATION_CONTEXT_NOT_EXHAUSTIVELY_DEFINED`. Target correlation and target scoping
remain parked; this ADR does not reopen them.

### Judgment-basis boundary preserved

`ADDITIONAL_BASIS_REMAINS_UNRESOLVED`, exactly as ADR-0017 through ADR-0024 left it. Process state
`JUDGMENT_BASIS = PARKED_UNTIL_NEW_EVIDENCE` is preserved. This ADR does not justify any future
envelope by reference to hypothetical future evidence, proof, rationale, provenance, or supporting
knowledge — those remain unresolved.

### Structural contracts

Not approved: `VerificationRequest`, `VerificationResult`, `VerificationStatus`,
`VerificationBasis`, `VerificationContext`, `VerificationTarget`, `ResultEnvelope`,
`VerificationOutput`. `REQUEST_STRUCTURAL_DISCOVERY` and `RESULT_STRUCTURAL_DISCOVERY` remain
**BLOCKED**. `STRUCTURAL_CONTRACTS_REMAIN_BLOCKED`. This ADR alone does not run a
structural-readiness review and does not unblock structural work.

### Execution

`VERIFICATION_EXECUTION_REMAINS_BLOCKED`. This ADR does not approve `VerificationExecutor`,
`VerificationPort`, a `VerificationEngine` implementation, `VerificationService`,
`VerificationPolicy`, `VerificationAdapter`, or `VerificationExecutionError`.

### Parked threads

Process state preserved, not reopened, and not treated as evidence by this ADR: judgment basis —
`PARKED_UNTIL_NEW_EVIDENCE`; non-success existence — `PARKED_UNTIL_NEW_EVIDENCE`; target
correlation — `PARKED_UNTIL_NEW_EVIDENCE`; target scoping — `PARKED_UNTIL_NEW_EVIDENCE`. This ADR's
decision does not constitute new evidence reopening any of them.

### Provider independence

This decision is independent of any LLM, `ModelRouter`, provider, prompt, temperature, tooling,
JSON schema, or model confidence, consistent with ADR-0002.

### Single semantic increment

`ONE_NEW_VERIFICATION_RESULT_ENVELOPE_EXISTENCE_REQUIREMENT_INCREMENT_FAMILY`. This ADR contains
exactly one new semantic increment family: distinguishable result-envelope existence is not a
mandatory invariant of the minimum successful Verification semantic contract. Everything else in
this ADR is a scope boundary, preserved prior authority, rationale, or future-compatibility
statement. No exact cardinality, concrete result structure, carrier form, materialization strategy,
non-success semantics, operation cardinality, or new target/correlation semantics is introduced or
decided.

### Reversibility

`NOT_REQUIRED` does not mean `FORBIDDEN`. A future, separately evidenced representation may
introduce a distinguishable result envelope without retracting this ADR, provided it is not claimed
to be a mandatory invariant of this same minimum contract absent a new architectural decision. This
ADR does not approve any such future representation; it records only that none of them would need
to contradict or retract the decision made here.

### Decision summary

| Concern | Decision |
| --- | --- |
| Successful judgment atom | Unchanged (ADR-0020) |
| Minimum result-envelope existence requirement | Not required |
| Exact result-envelope cardinality | Unresolved (unchanged, ADR-0024) |
| Future richer result envelope | Not prohibited |
| Concrete result structure | Not approved |
| Output representation | Unresolved |
| Materialization | Deferred |
| Non-success | Deferred; existence parked |
| Operation cardinality | Deferred |
| Correlation | Partial explicit-axis carrier approved; complete correlation not approved, unready |
| Judgment basis | Unresolved, parked |
| Structural contracts | Blocked |
| Execution | Blocked |

## Not Decided Here

- exact result-envelope cardinality
- concrete result-envelope construct
- `VerificationResult`
- `VerificationStatus`
- result object shape
- result fields
- output carrier
- materialization / resolution
- reference representation
- non-success semantics
- non-success existence
- request/result mapping
- operation/result mapping
- operation judgment cardinality
- judgment basis
- target's future Verification role
- complete correlation representation
- structural contracts
- execution topology
- persistence
- API / serialization

## Consequences

**Positive:**

1. The minimum semantic contract no longer carries an unnecessary mandatory envelope-existence
   invariant, while future representational flexibility is fully preserved.
2. The successful judgment atom (ADR-0020) and every other prior Verification decision are reused
   without modification or reinterpretation.
3. No speculative structure, field, or type is introduced by this ADR.
4. The narrow scope of this decision keeps it independent of exact cardinality, carrier form,
   materialization, non-success, judgment basis, target role, and operation cardinality.

**Tradeoff:**

1. This ADR does not provide a concrete output representation; no `VerificationResult` shape can
   yet be written from this ADR alone.
2. Structural contracts and execution remain entirely blocked; this ADR does not unblock either.
3. A future richer or specialized Verification layer, if it needs a distinguishable result
   envelope, will require its own separate, evidenced decision.
4. Exact result-envelope cardinality, output representation, materialization, and non-success
   semantics all remain unresolved, so a complete Verification output cannot yet be specified end
   to end.

## ADR Relationship

ADR-0025 complements ADR-0015 through ADR-0024. It supersedes none of them. ADR-0020 remains
authoritative for the successful judgment atom itself; ADR-0019 remains authoritative for request
transport cardinality; ADR-0021 remains authoritative for the minimum polarity requirement;
ADR-0022 remains authoritative for the minimum totality requirement; ADR-0023 remains authoritative
for the minimum output content topology requirement; ADR-0024 remains authoritative for the minimum
result-envelope cardinality requirement. This ADR does not reopen, narrow, or extend any of those
decisions — it resolves only the additional, narrower result-envelope-cardinality **existence**
requirement question that ADR-0024 explicitly left open ("neither requires nor forbids a future
concrete result-envelope construct") and that no prior ADR addressed by name.
