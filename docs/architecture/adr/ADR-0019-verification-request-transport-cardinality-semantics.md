# ADR-0019: Verification Request Transport Cardinality Semantics

- Status: Accepted
- Date: 2026-08-26

## Context

ADR-0016 froze the minimum V1 Verification subject: one individual Prediction / Counterfactual
consequence item, represented as one textual consequence statement. ADR-0017 froze the minimum
explicit derivation-context axes for that subject. ADR-0018 froze a partial, explicit-axis-scoped
correlation semantics — an individual consequence value, associated by opaque reference to its
baseline and, when applicable, its explicit hypothetical divergences — while leaving concrete
context membership, target association, materialization, judgment basis, and every cardinality
dimension explicitly deferred.

ADR-0016 explicitly left one further question open: whether a future request could transport
multiple independent minimum subjects, noting only that such transport "is not prohibited." M0-15CA
(Verification Remaining Structural-Prerequisite Dependency Review) identified request transport
cardinality as the single, structurally unavoidable dependency separating the currently
already-frozen minimum subject/correlation semantics from the ability to begin
`VerificationRequest` structural discovery — distinct from, and prior to, every other remaining
dimension (target, implicit assumptions, judgment basis, materialization, output, non-success,
operation cardinality, result cardinality), none of which was found to block this specific
question. M0-15CB then reviewed and approved a decision on exactly this question. This ADR records
the result of that approval. It does not reopen the discovery, and it does not create any
production contract.

## Decision

### Decision scope

This ADR decides one thing only: how many instances of the already-frozen minimum Verification
subject a minimum Verification request transports.

### Subject cardinality is not reopened

Subject cardinality — the minimum semantic subject of a single Verification judgment — remains
exactly what ADR-0016 already froze: one individual Prediction / Counterfactual consequence item.
This ADR does not restate that as new content, does not reopen subject granularity, and does not
alter it in any way. **Request transport cardinality** is a distinct question: not what the
judgment's subject is, but how many such subjects a minimum request instance carries.

### Judgment boundary

ADR-0016 already establishes that one Verification judgment concerns one individual subject. This
ADR does not infer, from that already-frozen fact, that one subject per judgment automatically
entails one subject per request. The two are independent dimensions; this ADR resolves the request
dimension on its own evidence, not by logical extension from judgment semantics.

### One subject per minimum request

A **minimum** Verification request transports **exactly one** instance of the minimum Verification
subject: one individual Prediction / Counterfactual consequence item.

The word "minimum" is essential and integral to this decision. This ADR does not state that every
future Verification request or transport envelope must always contain exactly one subject — only
that the minimum, currently evidenced request form does.

This request-transport-cardinality decision does not constrain operation cardinality or result
cardinality, and it does not prohibit a future batching mechanism or a future batch/multi-request
transport form under its own, separately evidenced architectural decision.

### Multi-subject minimum request not approved

Transporting multiple independent minimum subjects within a single minimum request is **not
approved**. This is a "not approved as minimum," not a "prohibited forever," finding. The reasons:

- no concrete Verification consumer or semantic requirement currently demands that multiple
  independent consequences enter one Verification request atomically (no transaction semantics,
  no all-or-nothing judgment requirement, no shared batch invariant, no mandatory simultaneous
  verification, and no aggregate consumer contract exists anywhere in the repository);
- no approved cross-subject semantics exists to give a multi-subject collection any meaning beyond
  "several independent items" (see "Cross-subject semantics" below);
- approving multi-subject transport as the minimum would require deciding additional, currently
  unsupported structural semantics — at minimum, a second transport-cardinality layer and some
  future item/envelope representation — none of which any current evidence justifies.

This ADR does not state that multi-subject transport is impossible. It states only that it is not
part of the currently evidenced minimum.

### Future batch transport not prohibited

A future, separately evidenced capability may batch multiple atomic minimum requests, introduce an
envelope, or introduce another transport form entirely. This ADR does not design any such
mechanism, does not name any future field, class, or container for it, and does not foreclose it.
Approving exactly one subject per minimum request today is monotonic with, and reversible toward,
such a future capability: nothing about this decision would need to be retracted or contradicted if
a future batch mechanism were later introduced under its own evidence.

### Collection as one subject remains rejected

ADR-0016 already establishes that a collection of consequence statements is not the minimum
Verification subject. This ADR preserves that finding without modification. A hypothetical future
batch of independent subjects would remain, conceptually, **multiple independent subjects** — never
**one aggregate Verification subject**. This ADR does not create or imply any aggregate subject
concept.

### Cross-subject semantics

No cross-subject semantics are approved by this ADR: not ordering, not dependency, not causal
relation, not consistency, not comparison, not aggregate correctness, not all/any semantics, not
collective success, and not transactional semantics. This mirrors ADR-0010's equivalent refusal for
multiple consequences within one Prediction / Counterfactual result. This ADR creates none of these
for Verification.

### Future batch context-association topology — unresolved

Because multi-subject minimum transport is not approved, this ADR does not decide, and explicitly
leaves open, what context-association topology a hypothetical future batch would use. It does not
claim that such a future batch would necessarily duplicate context per item, share one context
across items, mix both, or use a batch-level context construct. No authority currently chooses
among these; the question remains entirely future-only, contingent on a future, separate decision
to approve multi-subject transport in the first place.

### Prediction / Counterfactual result multiplicity is neutral evidence

`PredictionCounterfactualResult` may carry multiple consequence statements for one target. This
does not imply that Verification requests should be batched. ADR-0016 already establishes that the
consequence collection is not the minimum subject, that the whole P/C result is not the minimum
subject, and that no cross-item relationship semantics are frozen among those consequences. The
fact that an upstream result may contain several consequences is neutral evidence about the
*source* that may eventually feed several independent Verification subjects — it says nothing about
how those subjects should be *packaged* into requests, and it does not, by itself, support batch
transport as the minimum.

### Evaluation precedent

`EvaluationRequest` (ADR-0013) is a flat request centered on exactly one individual Prediction /
Counterfactual consequence. This is **strong structural precedent** for the same pattern here: a
second, independently arrived-at Evaluation-Engine decision converging on one-subject-per-request
for the same P/C consequence granularity that ADR-0016 already reused for Verification's own
subject. It is **not direct Verification authority** — Evaluation's ADR does not bind Verification's
request shape — but the independent convergence is recorded as meaningful, corroborating evidence
for this ADR's decision, not as its sole basis.

### Prediction / Counterfactual request precedent

`PredictionRequest` and `CounterfactualRequest` (ADR-0009) provide useful precedent for minimal,
flat domain request contracts in this repository. This ADR does not confuse the number of P/C
*request types* (two: Prediction and Counterfactual) with *subject transport cardinality*; those
two request types each transport one derivation operation, not a subject collection, and the
precedent is used here only for the general idiom of flat, non-enveloping request contracts already
established in this domain.

### Minimum-novelty rationale

One subject per minimum request composes the already-frozen semantic atom (subject plus its
ADR-0018 correlation association) exactly once, introducing no new batch or envelope semantic
layer. Multi-subject minimum transport currently lacks positive evidence and would additionally
require resolving several currently unaddressed invariant questions — such as duplicate subject
values, identical text under different derivation contexts, subjects drawn from different
baselines, and subjects mixing Prediction and Counterfactual origin — none of which exist for the
one-subject form. This ADR's decision is a semantic-evidence finding, not a preference for
implementation simplicity or performance.

### Zero-subject boundary

By the semantics frozen here, a minimum Verification request transports exactly one subject.
Zero-subject transport is therefore not an instance of the minimum request semantics at all — it is
excluded by definition, not by a validation rule. This ADR does not create validation code, an
error type, a message, or an `Optional`/container rule to express this; the exclusion is
definitional.

### Operation cardinality

`OPERATION_JUDGMENT_CARDINALITY_REMAINS_DEFERRED`. This ADR does not decide one request per
operation, one operation per request, one judgment per process invocation, or any batch execution
semantics.

### Result cardinality

`RESULT_ENVELOPE_CARDINALITY_REMAINS_DEFERRED`. This ADR does not infer any request-to-result
one-to-one relationship, and it does not decide any result shape.

### Complete correlation representation

`A1_PARTIAL_CARRIER_SEMANTICS_APPROVED`, `A1_COMPLETE_CORRELATION_SEMANTICS_NOT_APPROVED`, and
`COMPLETE_CORRELATION_REPRESENTATION_REMAINS_UNREADY` all remain exactly as ADR-0018 left them.
This ADR does not extend, narrow, or otherwise touch ADR-0018's carrier semantics.

### Explicit context association

ADR-0018 remains fully authoritative for the individual consequence semantic value, the baseline
opaque-reference association, and the explicit hypothetical-divergence opaque-reference association.
This ADR adds only that exactly one such subject-and-association unit belongs to one minimum
request semantic instance. No field is named or implied by this ADR.

### Output

Output representation remains deferred. This ADR does not approve `bool`, valid/invalid,
verified/unverified, a textual judgment shape, a score, or any status vocabulary.

### Non-success

`NON_SUCCESS_SEMANTICS_REMAIN_DEFERRED`. This ADR introduces no non-success vocabulary.

### Target

`TARGET_ASSOCIATION_REMAINS_UNRESOLVED`. No target field or association is approved by this ADR.

### Implicit assumptions

`IMPLICIT_ASSUMPTION_CORRELATION_ROLE_REMAINS_UNRESOLVED`. This ADR makes no decision about
implicit assumptions.

### Judgment basis

`ADDITIONAL_BASIS_REMAINS_UNRESOLVED`. This ADR does not assert that correlation/transport
cardinality has any bearing on what sustains a correctness/validity determination.

### Materialization

`MATERIALIZATION_REMAINS_DEFERRED`. This ADR does not approve any resolver and does not imply local
content availability.

### Provenance / identity

`PROVENANCE_MECHANISM_REMAINS_UNRESOLVED`, `OCCURRENCE_DISTINCTION_NEED_REMAINS_UNRESOLVED`, and
identity remains **not approved**. This ADR does not create `request_id`, `subject_id`,
`consequence_id`, `verification_id`, or `batch_id`.

### Concrete request structure not approved

This ADR does **not** create `VerificationRequest`. It does not choose a class name beyond
referring to the future conceptual contract, field names, field types, a reference type, a
dataclass shape, a wrapper, a container, validation rules, an error type, or a module/package
placement. No hypothetical code block or field listing is presented by this ADR.

### Concrete reference type

Remains deferred. Opaque-reference semantics are already frozen by ADR-0018. This ADR does not
choose `str`, `UUID`, `TSID`, or any wrapper type.

### Divergence container

Remains deferred. This ADR does not choose `tuple`, `list`, `frozenset`, ordering, or duplicate
handling.

### Structural contract gate

ADR-0015 states that structural contract discovery (request/result) remains blocked until its
prerequisite dimensions are separately decided. ADR-0018 explicitly preserved structural contracts
as blocked. This ADR resolves exactly one additional dimension of that prerequisite set — request
transport cardinality — and no more. Therefore:

- `VerificationRequest`: **NOT APPROVED**;
- `REQUEST_STRUCTURAL_DISCOVERY`: **BLOCKED**;
- structural contracts generally: **BLOCKED**.

This ADR does not claim that request structural discovery is now ready. Whether the full ADR-0015 /
ADR-0018 structural prerequisite set is satisfied is a separate determination for a dedicated,
future readiness review, not made by this ADR.

### Result and execution

`VerificationResult`: **NOT APPROVED**. `VerificationStatus`: **NOT APPROVED**. Verification
execution remains **BLOCKED**. This ADR does not approve `VerificationExecutor`,
`VerificationPort`, a `VerificationEngine` implementation, `VerificationService`, or a
`VerificationAdapter`.

### World Model / Prediction-Counterfactual execution

World Model production remains **BLOCKED** by ADR-0006. Prediction / Counterfactual Implementation
Gate item 4 (execution port) remains **PARKED/BLOCKED**.

### Provider independence

This decision is independent of any LLM, `ModelRouter`, provider, prompt, temperature, tooling,
JSON schema, or model confidence, consistent with ADR-0002.

### Decision summary

| Concern | Decision |
| --- | --- |
| Minimum Verification subject | Existing one-individual-consequence semantics preserved |
| Request transport cardinality | Exactly one minimum subject per minimum Verification request |
| Multi-subject minimum request | Not approved |
| Future batch transport | Not prohibited; separate future decision |
| Collection as one subject | Not approved |
| Future batch context topology | Unresolved |
| Operation cardinality | Deferred |
| Result cardinality | Deferred |
| Complete correlation representation | Unready / not approved |
| Output | Deferred |
| Non-success | Deferred |
| Target association | Unresolved |
| Concrete request structure | Not approved |
| Structural contract discovery | Blocked |
| Execution | Blocked |

## Not Decided Here

- `VerificationRequest` field names
- request concrete type shape
- concrete baseline reference type
- concrete divergence reference type
- divergence container
- validation rules
- validation error
- package/module placement
- multi-subject batch envelope
- batch item type
- shared vs. per-subject context in a future batch
- batch identity
- batch ordering
- batch success semantics
- operation cardinality
- result cardinality
- result structure
- output representation
- non-success semantics
- target's future Verification role
- implicit-assumption correlation role
- complete correlation representation
- materialization / resolution
- judgment basis
- provenance mechanism
- occurrence identity
- execution topology
- concrete consumer
- persistence
- API / serialization

## Consequences

**Positive:**

- The minimum request transport atom is now semantically bounded: exactly one subject.
- No batch or envelope abstraction is introduced without evidence.
- Request transport cardinality is cleanly separated from judgment cardinality and from operation
  cardinality.
- Future batching remains possible under its own, separately evidenced decision.
- No change is made to any Prediction / Counterfactual or Evaluation contract.

**Tradeoff:**

- Structural `VerificationRequest` discovery remains blocked; this ADR resolves one prerequisite
  dimension, not the full set ADR-0015 named.
- No concrete `VerificationRequest` exists as a result of this ADR.
- A future batch transport capability, if ever pursued, would require its own additional semantics
  (context topology, cross-subject semantics, batch identity) not addressed here.
- Result structure, output representation, and execution topology remain entirely unresolved.

## ADR Relationship

ADR-0019 complements ADR-0015, ADR-0016, ADR-0017, and ADR-0018. ADR-0015 remains authoritative for
the minimum Verification correctness/validity semantic axis and the structural prerequisite gate.
ADR-0016 remains authoritative for the minimum subject and its cardinality — one individual
consequence item — which this ADR does not reopen. ADR-0017 remains authoritative for the minimum
explicit derivation-context axes and their associated unresolved dimensions. ADR-0018 remains
authoritative for the partial explicit-axis correlation and reference semantics. ADR-0019 resolves
only request transport cardinality — how many instances of the already-frozen subject a minimum
request carries — and supersedes none of the ADRs listed above.
