# ADR-0023: Verification Minimum Output Content Topology Requirement Semantics

- Status: Accepted
- Date: 2026-09-04

> Status `Accepted` records that the semantic decision this ADR carries has already been approved by
> its decision review (M0-15GA). Until this ADR is merged to `main`, it is an **approved decision /
> local ADR draft**, not yet **accepted `main` authority**.

## Context

ADR-0015 froze Verification's minimum V1 semantic category — correctness/validity of derived
content, evaluated within the derivation context under which that content was produced — and
deferred all output semantics. ADR-0016 froze the first/minimum Verification subject as one
individual Prediction / Counterfactual consequence item. ADR-0017 preserved correctness/validity as
one undifferentiated semantic axis and froze the minimum explicit derivation-context axes. ADR-0018
froze a partial, explicit-axis-scoped correlation semantics for that subject, while leaving complete
correlation representation unready. ADR-0019 froze that a minimum Verification request transports
exactly one instance of the minimum subject, keeping request transport cardinality distinct from
operation cardinality and result cardinality.

ADR-0020 froze what minimally exists when Verification succeeds in producing a correctness/validity
judgment: one correctness/validity determination concerning one minimum subject, within the
subject's applicable derivation-context scope. ADR-0020 explicitly distinguished what the successful
judgment semantically means from how that meaning is represented, and recorded — as reversibility
commentary, not as an approval — that the frozen atom "remains fully compatible with a future
decision approving binary polarity, a finite categorical topology, or open/non-enumerated judgment
content," without approving any of them. ADR-0021 resolved that minimum mandatory polarity is
`NOT_REQUIRED`. ADR-0022 resolved that minimum mandatory totality is `NOT_REQUIRED`. Neither
ADR-0021 nor ADR-0022 addressed output content topology; both left it exactly where ADR-0020 had.

A sequence of read-only process gates (M0-15FX through M0-15GA) progressively isolated the
output-representation question that ADR-0015 had deferred. That work established, without deciding
representation: that a successful-only representation-constraint discovery could proceed
independently of judgment basis, non-success existence, result-envelope cardinality, and operation
cardinality; that the accepted successful-judgment atom already rejects a bare success-marker with no
semantic payload — ADR-0020's own context records that "no semantic payload at all" was considered
and not approved among the alternatives evaluated when the atom was frozen, and ADR-0021 confirms
that removing mandatory polarity "does not empty a successful determination of meaning" and does not
"remove, weaken, or redefine the judgment's underlying semantic content"; that semantic content
topology (the abstract organization of the judgment-value space) is analytically distinct from
concrete carrier form (how that content is encoded); and that no accepted authority establishes any
one specific topology as constitutive of the judgment's semantic legitimacy. A subsequent decision
review (M0-15GA) evaluated three positions — a specific topology required by the minimum, no specific
topology required by the minimum, and the requirement left unresolved — against that evidence and
approved the second. This ADR records the result of that approval. It does not reopen the discovery
or the review, and it does not create any production contract.

Process gate reports (M0-15FX–GA) are cited here only as process history establishing how this
question was narrowed. They are not architectural authority. This ADR's decision rests on accepted
architecture (ADR-0015 through ADR-0022) and on the approved M0-15GA review, not on the gate reports
themselves.

## Decision

### Minimum output content topology requirement

The minimum Verification semantic contract does **not** require the successful correctness/validity
judgment content to be constrained to, or represented through, any one particular mandatory semantic
topology.

Conceptually: `NO_SPECIFIC_OUTPUT_CONTENT_TOPOLOGY_REQUIRED_BY_MINIMUM`.

This is a **requirement-level** decision. It concerns only whether committing to one specific content
topology is one of the mandatory semantic invariants of the minimum Verification contract. It says
nothing about which topology, if any, a future concrete or richer representation will actually use —
every future concrete representation will naturally exhibit some semantic organization; this ADR
freezes only that the minimum contract does not mandate one such organization as an invariant.

### "Not required" precision — critical boundary

This ADR freezes `NOT_REQUIRED`. It does **not** freeze, and explicitly distinguishes this decision
from, every one of the following: `ABSENT`, `FORBIDDEN`, `IMPOSSIBLE`, `NON_TOPOLOGICAL`,
`ARBITRARY_REPRESENTATION`, `ANY_REPRESENTATION_IS_VALID`. Accordingly, this ADR does **not** state
or imply any of:

- "the successful judgment has no topology";
- "topology is absent from Verification semantics";
- "topology is forbidden";
- "any representation whatsoever satisfies the minimum contract";
- "the output may be arbitrary";
- "the output need not carry semantic content" (see "Successful content lower bound preserved"
  below).

The precise and only meaning frozen here: **committing to one specific content topology is not one
of the mandatory semantic invariants of the minimum Verification contract.** Whether a future,
richer, or specialized layer adopts a particular topology is a separate question this ADR does not
touch (see "Future richer topology" below).

### Successful content lower bound preserved

This ADR does not reopen, weaken, or redefine the accepted minimum expressiveness lower bound.
`SUCCESSFUL_MINIMUM_JUDGMENT_REQUIRES_SEMANTIC_JUDGMENT_CONTENT` remains frozen exactly as it follows
from ADR-0020 and ADR-0021: a successful minimum Verification judgment must faithfully preserve the
accepted correctness/validity determination itself, not merely record that a determination occurred.
`SUCCESS_MARKER_ONLY_SUFFICIENCY = REJECTED_BY_EXISTING_ACCEPTED_AUTHORITY` is inherited from
ADR-0020's own context (which considered and did not approve "no semantic payload at all" among the
evaluated alternatives) and from ADR-0021's explicit "does not empty... of meaning" language. This is
not a new ADR-0023 decision; it is a precise restatement of authority ADR-0020 and ADR-0021 already
established, carried forward here only so that "no specific topology required" is never misread as
"no semantic content required."

`NO_SPECIFIC_TOPOLOGY_REQUIRED` and `NO_SEMANTIC_CONTENT_REQUIRED` are different propositions. This
ADR freezes only the former. The latter remains false: semantic content is, and remains, mandatory.

### Requirement-level scope only

This ADR decides the *requirement* question only — whether the minimum contract mandates a specific
topology. It does not decide, and does not narrow, any of:

- which topology a future representation would use;
- whether topology commitment might become necessary for some future, specialized, separately
  evidenced Verification capability;
- how the already-mandatory semantic content (see above) is concretely carried.

### Future richer topology

`FUTURE_RICHER_OUTPUT_CONTENT_TOPOLOGY_NOT_PROHIBITED`.

A future, separately evidenced decision may adopt a particular content topology for a richer or
specialized Verification capability without contradicting this ADR. `NOT_REQUIRED` at the minimum
level does not forbid a stricter commitment at a higher, separately decided level. Possible future
topologies include, purely as compatibility examples and not as an exhaustive or approved list:
binary categorization, a finite predefined categorical space, open/non-enumerated content, or another
semantic organization not yet identified. This ADR does not approve, name, or design any of them.

### Open topology not selected

`OPEN_NON_ENUMERATED_CONTENT_NOT_SELECTED`. This ADR must not be read as approving open or free-form
judgment content as the minimum representation. Open content remains only one possible future
compatibility example (see "Future richer topology"), not a decision.

### Finite topology not selected

`FINITE_PREDEFINED_CONTENT_NOT_SELECTED`. This ADR does not approve, name, or count any finite
predefined category set. No category vocabulary is introduced.

### Polarity relation preserved

ADR-0021 remains fully authoritative and is not reopened:
`MINIMUM_POLARITY_REQUIREMENT_RESOLVED_AS_NOT_REQUIRED`. This ADR does not make a binary/polar
topology part of minimum V1. A future richer binary/polar topology remains possible only under its
own, separately evidenced scope, exactly as ADR-0021 already preserved. This ADR's decision is
broader than, and does not collapse into, the polarity decision: polarity concerns one specific
candidate topology (an opposed two-valued orientation); this ADR concerns whether *any* specific
topology commitment — polar or not — is mandatory at the minimum level.

### Content topology vs. concrete carrier form — critical boundary

`SEMANTIC_CONTENT_TOPOLOGY != CONCRETE_CARRIER_FORM`. Semantic content topology is the abstract
organization of the judgment-value semantic space (for example: finite vs. open, categorical vs.
otherwise). Concrete carrier form is how already-approved semantic content would be encoded (for
example: text, an enumerated type, a structured object, a value object, a reference/token, a
tuple/list). This ADR decides only the former, at the requirement level, and does not decide the
latter at all. This ADR does not choose `str`, `bool`, `Enum`, an object, a value object, a
structured payload, a reference/token, or a tuple/list as the carrier for any future Verification
output.

### Textual representation not approved

`TEXTUAL_OUTPUT_REPRESENTATION_NOT_APPROVED`. The existing textual patterns in `ReasoningOutcome`,
`PredictionCounterfactualResult`, and `EvaluationResult` remain adjacent representation precedent
only, as already classified by prior process discovery. No `str` decision is made by this ADR.

### Structured representation not approved

`STRUCTURED_OUTPUT_REPRESENTATION_NOT_APPROVED`. No schema, no field, and no object topology is
approved or sketched by this ADR.

### Reference / opaque carrier boundary

`MATERIALIZATION_REMAINS_DEFERRED`, exactly as prior ADRs left it.
`MATERIALIZATION_DEFERRED != OPAQUE_CARRIER_FORBIDDEN`: the deferred status of materialization is not
itself a prohibition on a future opaque or reference-based carrier — it means only that no
resolver/dereference mechanism is currently approved. This ADR approves neither a reference/token
carrier nor any resolver or dereference mechanism.

### Confidence / score boundary preserved

Preserving ADR-0020 without modification: confidence, probability, score, certainty, utility, and
ranking are not the minimum correctness/validity determination. This ADR does not reopen that
exclusion and does not introduce any of them as, or as part of, a content topology.

### Undifferentiated axis preserved

`CORRECTNESS_VALIDITY_REMAINS_UNDIFFERENTIATED`, exactly as ADR-0017 established and ADR-0020
preserved. This ADR does not imply, and must not be read as implying, that a future representation
requires two separate mandatory outputs — one for correctness and one for validity. Whatever topology
a future decision selects, it applies to the single undifferentiated axis, not to two.

### Semantic cardinality preserved

Preserving ADR-0020: one correctness/validity determination exists per minimum successful
Verification judgment. This ADR reaffirms that semantic cardinality is distinct from structural
cardinality: `ONE_DETERMINATION != ONE_FIELD != ONE_OBJECT != ONE_STRING != ONE_ENUM_MEMBER`. This
ADR decides none of the latter four.

### Result envelope preserved

`RESULT_ENVELOPE_CARDINALITY_REMAINS_DEFERRED`. This ADR does not decide one result, zero-or-one, a
collection, a result object, a payload, or a status field. Content topology and result-envelope
topology remain independent, separately deferred questions.

### Non-success preserved

`NON_SUCCESS_SEMANTICS_REMAIN_DEFERRED`, exactly as ADR-0015 through ADR-0022 left it. The narrower
existence question is process-parked pending new evidence (`NON_SUCCESS_EXISTENCE`,
`PARKED_UNTIL_NEW_EVIDENCE`); this ADR does not touch it. This ADR introduces no non-success
vocabulary — not `NO_JUDGMENT`, `UNKNOWN`, `UNVERIFIED`, `FAILED`, `NOT_VERIFIABLE`, `INDETERMINATE`,
`Optional`, or `None`.

### Judgment basis preserved

`ADDITIONAL_BASIS_REMAINS_UNRESOLVED`, exactly as ADR-0017 through ADR-0022 left it. This ADR does
not require the output to contain evidence, proof, supporting knowledge, rules, or provenance, and it
does not decide what sustains the correctness/validity determination.

### Context, target, and correlation preserved

Unchanged and not reopened by this ADR: `DERIVATION_CONTEXT_NOT_EXHAUSTIVELY_DEFINED`,
`TARGET_ASSOCIATION_REMAINS_UNRESOLVED`, `TARGET_FUTURE_CORRELATION_ROLE_REMAINS_UNRESOLVED`,
`A1_PARTIAL_CARRIER_SEMANTICS_APPROVED`, `A1_COMPLETE_CORRELATION_SEMANTICS_NOT_APPROVED`, and
`COMPLETE_CORRELATION_REPRESENTATION_REMAINS_UNREADY`.

### Totality preserved

`TOTALITY_NOT_REQUIRED_BY_MINIMUM` (ADR-0022) is not reopened. This ADR does not infer from either
decision any `Optional`/`None`/result-absence topology.

### Output status after this ADR

| Concern | Status |
| --- | --- |
| Successful judgment semantic content | Decided (ADR-0020) |
| Minimum semantic-content lower bound | Decided / inherited (ADR-0020, ADR-0021) |
| Mandatory polarity | Not required (ADR-0021) |
| Mandatory specific content topology | Not required (this ADR) |
| Concrete output carrier / representation | Unresolved |
| Non-success semantics | Deferred |
| Result-envelope cardinality | Deferred |

`OUTPUT_REPRESENTATION_REMAINS_UNRESOLVED` as a whole. This ADR narrows one dimension of that
prerequisite set — the topology requirement question — and does not claim output representation is
now fully solved.

### Structural readiness unaffected

Resolving this narrow topology-requirement question does not unblock structural work. Preserved
unless a future, separate accepted authority proves otherwise: `VerificationRequest`,
`VerificationResult`, `VerificationStatus`, `VerificationBasis`, `VerificationContext`, and
`VerificationTarget` remain **NOT APPROVED**. `REQUEST_STRUCTURAL_DISCOVERY` and
`RESULT_STRUCTURAL_DISCOVERY` remain **BLOCKED**. `STRUCTURAL_CONTRACTS_REMAIN_BLOCKED`.

### Execution unaffected

`VERIFICATION_EXECUTION_REMAINS_BLOCKED`. `OPERATION_JUDGMENT_CARDINALITY_REMAINS_DEFERRED`. This ADR
does not approve `VerificationExecutor`, `VerificationPort`, a `VerificationEngine` implementation,
`VerificationService`, `VerificationPolicy`, or a `VerificationAdapter`.

### Minimum-novelty rationale

ADR-0020 already provides a meaningful successful judgment atom. That atom is deliberately stable
across multiple future topology choices: ADR-0020's own reversibility commentary records explicit
compatibility with binary polarity, a finite categorical topology, and open/non-enumerated content
alike, without needing to retract anything regardless of which (if any) is later chosen. No accepted
Verification invariant establishes that one particular content topology must be mandatory for the
minimum contract to remain coherent. This ADR therefore freezes only the narrow finding that no
specific topology is required at minimum — it does not rest on the absence of evidence for a
mandatory-topology candidate alone; it rests positively on the accepted atom's demonstrated
meaningfulness prior to any topology commitment, the accepted authority's explicit multi-topology
compatibility statement, and, only as secondary methodological support, the same minimum-contract
discipline ADR-0021 and ADR-0022 already applied to their own, different, questions.

### Reversibility

`NOT_REQUIRED` does not mean `FORBIDDEN`. A future, separately evidenced, richer or specialized
Verification layer may adopt a particular content topology within its own scope without contradicting
this ADR. This ADR does not approve any such layer; it records only that none of them would need to
contradict or retract the decision made here.

### Decision summary

| Concern | Decision |
| --- | --- |
| Successful judgment atom | Unchanged (ADR-0020) |
| Minimum mandatory polarity | Not required (unchanged, ADR-0021) |
| Minimum mandatory totality | Not required (unchanged, ADR-0022) |
| Successful content lower bound | Semantic judgment content required (inherited) |
| Success-marker-only sufficiency | Rejected (inherited) |
| Mandatory specific content topology | Not required |
| Open topology | Not selected |
| Finite topology | Not selected |
| Binary/polar topology | Not selected; ADR-0021 unchanged |
| Concrete carrier form | Not decided |
| Textual representation | Not approved |
| Structured representation | Not approved |
| Reference/opaque carrier | Not approved; not forbidden |
| Confidence/score as judgment | Excluded (unchanged) |
| Correctness/validity differentiation | Undifferentiated (unchanged) |
| Semantic cardinality | One determination (unchanged) |
| Result-envelope cardinality | Deferred |
| Non-success semantics | Deferred |
| Judgment basis | Unresolved |
| Structural contracts | Blocked |
| Execution | Blocked |

## Not Decided Here

- open vs. finite topology
- binary topology for a future richer semantics
- concrete output carrier
- output field name
- output type
- textual representation
- structured representation
- reference/token representation
- result envelope
- status vocabulary
- non-success semantics
- judgment basis
- target's future Verification role
- complete correlation representation
- evidence representation
- provenance mechanism
- materialization / resolution
- operation-judgment cardinality
- execution topology
- persistence
- API / serialization

## Consequences

**Positive:**

1. One unnecessary mandatory design axis — a specific content topology — is removed from the minimum
   Verification semantic contract.
2. Successful-judgment semantic-content fidelity, already required by ADR-0020/0021, remains fully
   preserved and unweakened.
3. Future carrier and topology flexibility is preserved: no premature type, schema, or vocabulary is
   introduced.
4. No speculative structure is introduced by this ADR.
5. The narrow scope of this decision keeps it independent of non-success, result-envelope
   cardinality, judgment basis, target role, and complete correlation.

**Tradeoff:**

1. Concrete output representation remains entirely unresolved; no `VerificationResult` shape can yet
   be written from this ADR alone.
2. Structural result contracts and execution remain entirely blocked; this ADR does not narrow that
   blocker.
3. A future richer or specialized Verification layer, if it needs a specific topology, will require
   its own separate, evidenced decision.
4. Non-success semantics and result-envelope cardinality remain unresolved, so a complete Verification
   output cannot yet be specified end to end.

## ADR Relationship

ADR-0023 complements ADR-0015 through ADR-0022. It narrows only the output content topology
**requirement** question — whether the minimum Verification semantic contract mandates one specific
content topology — and answers it `NOT_REQUIRED`. It supersedes none of them. ADR-0020 remains
authoritative for the successful judgment atom itself; ADR-0021 remains authoritative for the minimum
polarity requirement; ADR-0022 remains authoritative for the minimum totality requirement. This ADR
does not reopen, narrow, or extend any of those three decisions — it resolves only the additional,
narrower topology-requirement question that ADR-0020's reversibility commentary left open and that
ADR-0021/0022 did not address.
