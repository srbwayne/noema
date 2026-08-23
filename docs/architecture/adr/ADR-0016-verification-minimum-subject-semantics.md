# ADR-0016: Verification Minimum Subject Semantics

- Status: Accepted
- Date: 2026-08-23

## Context

ADR-0005 freezes `Verification Engine` as a distinct structural component of COGNITION V1. ADR-0015
froze the minimum V1 Verification semantic axis: correctness/validity of derived content, evaluated
within the derivation context under which that content was produced, uniformly for Prediction and
Counterfactual. ADR-0015 deliberately left the first/minimum Verification subject deferred, because
identifying *what* is judged first required knowing *what kind of judgment* Verification performs.
With that operation semantics now resolved, M0-15R resumed the subject question through read-only
discovery.

ADR-0010 already establishes the minimum representation of a Prediction / Counterfactual
consequence: a textual consequence statement. Each statement represents one consequence item; no
per-consequence identity, reference, or dedicated value object exists. `PredictionCounterfactualResult`
may carry one or more such statements for the same target, and ADR-0010 explicitly assigns them no
relationship, ordering, or exhaustiveness semantics. The P/C result also carries `target_ref` and
`status`, alongside the consequence statements — metadata about the derivation, not derived content
itself. This ADR records the result of that discovery. It does not extend it, and it does not create
any production contract.

## Decision

### First/minimum Verification subject

The first/minimum V1 Verification subject is **one individual Prediction / Counterfactual
consequence item**.

At the existing P/C boundary, that subject is already represented as **one textual consequence
statement** — the same minimal representation ADR-0010 already froze. No new structure is
introduced to express it.

### What is judged vs. within what it is judged

Verification judges the correctness/validity **of** the individual consequence item. That is
distinct from the derivation context **within which** that judgment is made (ADR-0015). The subject
is the value being judged; the derivation context is the semantic backdrop the judgment refers to.
This ADR freezes only the former. The latter — its composition and how it reaches a future
Verification operation — remains entirely deferred (see "Derivation context remains distinct"
below).

### Individual-consequence evidence

ADR-0010 already establishes, for the minimum consequence representation: a textual consequence
statement; each statement represents one consequence item; no per-consequence identity; no
`consequence_ref`; no dedicated `Consequence` value object; no own `target_ref`; no confidence; no
probability; no utility; no verification field. This makes the individual consequence item the
smallest already-existing unit of derived content that satisfies ADR-0015's axis without
introducing any new structure.

### Derivation context remains distinct

ADR-0015 remains authoritative: correctness/validity is evaluated within the derivation context
under which the content was produced. This ADR does not freeze the composition or representation of
that context. It does not approve, as a requirement of the subject, any of: `baseline_ref`,
`divergence_refs`, `scenario_ref`, `context_ref`, `world_model_ref`, `evidence_ref`, a
`PredictionRequest` dependency, a `CounterfactualRequest` dependency, or a
`PredictionCounterfactualResult` dependency. The derivation context is not part of the subject
frozen here.

### Consequence collection is not the minimum subject

ADR-0010 permits multiple consequence statements for the same target but assigns them no AND/OR
semantics, no ordering, no completeness/exhaustiveness claim, no cross-item consistency
requirement, no causal relation, and no scenario-branch relation. Treating the collection itself as
one Verification subject would require inventing exactly this kind of collective semantics, which
no ADR approves. Collection-as-subject is **not approved** by this decision. This does not prohibit
a future request from transporting multiple independent individual subjects — that is a transport
question, addressed below, and remains deferred.

### Whole P/C result is not the minimum subject

`PredictionCounterfactualResult` is an envelope containing `target_ref`, `status`, and
`consequences`. The derived content lives in the consequence items; `target_ref` and `status` play
different roles and do not become part of the minimum subject merely by co-existing in the same
result. Additionally, when `status` is `INSUFFICIENT_KNOWLEDGE`, `consequences` is empty — that
result carries no derived-content item at all. The whole result is therefore not the semantically
correct minimum unit for the axis ADR-0015 froze.

### Empty P/C result

When a Prediction / Counterfactual result contains zero consequence items, no instance of the
minimum Verification subject has been produced by that result. This does not mean Verification
failed, returned no judgment, is unknown, or is unverifiable — those would be claims about a
Verification operation that does not yet exist. It means only that no derived-content subject item
exists in that particular upstream result. This ADR introduces no Verification non-success
vocabulary to describe it.

### P/C status is not the subject

`PredictionCounterfactualStatus` remains state/metadata of the P/C result. `DERIVED` and
`INSUFFICIENT_KNOWLEDGE` are not reused as Verification output or status by this ADR.

### target_ref boundary

`target_ref` is not part of the minimum Verification subject frozen here. This ADR does not decide
that `target_ref` is the Verification correlation mechanism, does not decide that it is required
derivation-context representation, and does not decide that it is unnecessary forever. Its eventual
role in correlation, semantic scoping, or derivation-context transport — if any — remains entirely
deferred to a future decision.

### No new consequence identity

Selecting an individual consequence item as the minimum semantic subject does not itself require or
justify a new consequence identity. This ADR does not approve `consequence_id`, `consequence_ref`,
a `UUID`, a `TSID`, a `VerificationSubjectId`, or a `DerivedConsequenceId`. This does not mean
Verification can never need consequence identity: future concrete evidence involving correlation,
provenance, or occurrence distinction may justify a separate identity decision. No identity is
approved now.

### No subject wrapper

Selecting the subject does not itself justify a dedicated wrapper. This ADR does not create or
approve `VerificationSubject`, `DerivedContent`, `DerivedConsequence`, `VerifiedConsequence`, or a
`Consequence` value object. The existing representation — a textual consequence statement — remains
sufficient to freeze the minimum subject. This does not mean a wrapper can never exist; it means no
evidence justifies one now.

### Subject value vs. occurrence

This decision is value-oriented: the minimum subject is the textual semantic value of the
consequence item. This ADR does not decide occurrence identity, and it does not invent semantics
for two textually identical strings appearing across different requests, results, or scenarios.
That question, if concretely needed for correlation or provenance, requires its own future
decision.

### Evaluation precedent

ADR-0012 independently arrived at the same P/C consequence granularity for a different semantic
axis (utility/value judgment). This ADR selects that same granularity because it is also
independently appropriate for derived-content correctness/validity — not because Evaluation chose
it. The structural facts that support this decision (no identity, no wrapper, uniform applicability
to Prediction and Counterfactual) are properties of the consequence item itself, re-verified here
against Verification's own axis.

### Other artifacts not approved as minimum subject

`EpistemicClaim`, `ReasoningOutcome`, `Plan`, and `EvaluationResult` are not approved as the
first/minimum Verification subject. No evidence in the repository establishes any of them as the
first/minimum derived-content subject this ADR freezes. This does not declare that Verification can
never consume or reference other artifacts — ownership does not imply prohibition of consumption —
only that none of them is approved as the minimum subject here. Future subject categories remain
possible under their own separate, evidenced decisions.

### Future subject extension

This ADR defines the first/minimum V1 Verification subject. It does not define an exhaustive set of
every subject category Verification may ever support. Future extension requires its own evidence
and architectural decision.

### Request cardinality: deferred

This ADR does not decide whether a future `VerificationRequest` receives exactly one subject, one
or more subjects, a tuple, a batch, or a collection. Request cardinality remains deferred.

### Operation cardinality: deferred

This ADR does not infer that one Verification operation corresponds to exactly one consequence.
Operation/orchestration cardinality remains deferred.

### Correlation: deferred

This ADR does not decide whether Verification correlates its subject by the consequence text alone,
by `target_ref` + consequence, by a `scenario_ref` + consequence, or by any `result_ref`,
`request_ref`, `subject_ref`, or `verification_ref`. Correlation remains deferred and is not copied
from ADR-0012.

### Reference representation: deferred

This ADR does not decide how the derivation context reaches a future Verification operation. No
reference field, type, or dependency is approved. Reference representation remains deferred.

### Output representation: deferred

This ADR does not decide any concrete output representation — not `bool`, pass/fail, valid/invalid,
verified/unverified, a `VerificationStatus` enum, a textual judgment, a score, or a confidence
value. Output representation remains deferred.

### Non-success semantics: deferred

This ADR does not decide `UNKNOWN`, `UNVERIFIED`, `NOT_VERIFIABLE`, `INSUFFICIENT_EVIDENCE`,
`INDETERMINATE`, or `UNRESOLVED` as Verification vocabulary. Non-success semantics remain deferred.

### Request / result / status structure not approved

This ADR does not approve `VerificationRequest`, `VerificationResult`, or `VerificationStatus`. It
does not infer field names, tuple shapes, validation rules, or cross-field invariants for any of
them.

### Prediction / Counterfactual contract preservation

`PredictionCounterfactualResult` remains unchanged. No `consequence_id`, `consequence_ref`,
wrapper, verification field, discriminator, or context field is added to it by this ADR.

### Evaluation boundary

Evaluation and Verification remain distinct, exactly as ADR-0012 and ADR-0015 established.
Evaluation concerns a utility/value judgment; Verification concerns correctness/validity. The fact
that both may take an individual P/C consequence as their first subject does not merge the
components or their outputs. No dependency between Evaluation and Verification, in either
direction, is approved by this ADR.

### Epistemic / Confidence boundary

Confidence, provenance, `EpistemicStatus`, supporting/counter evidence, and conflict semantics
remain owned by the existing Epistemic Model / Confidence Engine components, unaffected by this
ADR. This ADR does not absorb them, and it does not prohibit a future, separately decided
Verification capability from referencing an existing Epistemic concept without owning it.

### Situation Model / World Model boundary

The Situation Model's ownership of the agent's current believed situation is preserved. World Model
production remains **BLOCKED** by ADR-0006. Neither is required structurally by this ADR.

### Execution boundary

Verification execution remains completely blocked. This ADR does not approve
`VerificationExecutor`, `VerificationPort`, a `VerificationEngine` implementation,
`VerificationService`, `VerificationPolicy`, `VerificationAdapter`, or
`VerificationExecutionError`. No concrete production Verification consumer exists.

### Provider independence

This subject semantics is independent of any LLM, `ModelRouter`, provider, prompt, temperature,
tool calling, JSON schema, or model confidence.

### Minimum-novelty rationale

No additional architectural decision is required to select the individual consequence item as the
first/minimum semantic subject: it reuses the exact representation ADR-0010 already froze, with no
new identity, wrapper, collective semantics, or status vocabulary. Many structural and execution
decisions remain deferred, as enumerated throughout this ADR.

### Reversibility

An atomic first/minimum subject is composable into future transport or orchestration shapes without
redefining the semantic atom itself. This does not approve batch transport. It does not prohibit a
future, separately evidenced, coarser-grained subject category from being introduced later.

### Decision summary

| Concern | Decision |
| --- | --- |
| First/minimum Verification subject | One individual P/C consequence item |
| Existing subject representation | One textual consequence statement |
| Subject semantic orientation | Value-level derived content |
| Derivation context part of subject | No |
| `target_ref` part of subject | No |
| `target_ref` future role | Deferred |
| Consequence collection as one subject | Not approved |
| Whole P/C result as minimum subject | Not approved |
| Empty P/C result produces minimum subject | No |
| New consequence identity | Not required/approved by this decision |
| New consequence wrapper | Not justified/approved by this decision |
| Request cardinality | Deferred |
| Operation cardinality | Deferred |
| Correlation | Deferred |
| Reference representation | Deferred |
| Output representation | Deferred |
| Non-success semantics | Deferred |
| Request/result/status structure | Deferred |
| Execution topology | Deferred |
| Future subject categories | Possible under separate decision |

## Not Decided Here

- request cardinality
- operation cardinality
- correlation
- `target_ref` future correlation/context role
- derivation-context representation
- reference representation
- request structure
- result structure
- status vocabulary
- output representation
- non-success semantics
- evidence representation
- occurrence identity
- future consequence identity if later justified
- persistence
- serialization/API
- execution port
- application/engine
- adapter/provider
- execution errors
- concrete consumer
- future additional Verification subject categories

## Consequences

**Positive:**

1. The first/minimum Verification subject is now semantically defined.
2. The unit matches existing P/C consequence-item semantics; no new type is introduced.
3. No new identity or wrapper is required for this decision.
4. `PredictionCounterfactualResult` is unchanged.
5. Subject discovery no longer blocks later semantic work on Verification.

**Tradeoff:**

1. Request cardinality remains unresolved.
2. Correlation remains unresolved.
3. Derivation-context representation remains unresolved.
4. Output representation remains unresolved.
5. Non-success semantics remain unresolved.
6. Structural contracts (request/result) remain blocked.
7. Execution remains entirely blocked.
8. No concrete production consumer exists.

## ADR Relationship

ADR-0016 complements ADR-0015. ADR-0015 remains authoritative for the Verification minimum
semantic axis, the derivation-context semantic scope, the actuality boundary, the
process-vs-content boundary, and the component boundaries preserved here. ADR-0010 remains
authoritative for P/C consequence representation and collection semantics. ADR-0012 is referenced
as independent precedent for granularity, but is not the authority for Verification subject
semantics. ADR-0016 supersedes none of them.
