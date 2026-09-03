# ADR-0022: Verification Minimum Totality Requirement Semantics

- Status: Accepted
- Date: 2026-09-02

> Status `Accepted` records that the semantic decision this ADR carries has already been approved by
> its decision review (M0-15EU). Until this ADR is merged to `main`, it is an **approved decision /
> local ADR draft**, not yet **accepted `main` authority**.

## Context

ADR-0015 froze Verification's minimum V1 semantic category — correctness/validity of derived
content, evaluated within the derivation context under which that content was produced — and
deferred all output semantics. ADR-0016 froze the first/minimum Verification subject as one
individual Prediction / Counterfactual consequence item. ADR-0017 preserved correctness/validity as
one undifferentiated semantic axis and froze the minimum explicit derivation-context axes. ADR-0018
froze a partial, explicit-axis-scoped correlation semantics for that subject. ADR-0019 froze that a
minimum Verification request transports exactly one instance of the minimum subject. ADR-0020 froze
what minimally exists when Verification succeeds in producing a correctness/validity judgment — one
determination concerning one minimum subject, within the subject's applicable derivation-context
scope — while leaving polarity unresolved. ADR-0021 resolved that the minimum successful judgment
does not require a polarity dimension.

Across ADR-0015 through ADR-0021, one dimension of the output-semantic prerequisite set that
ADR-0015 identified was recorded, repeatedly and deliberately, as unresolved:
`VERIFICATION_TOTALITY_NOT_ESTABLISHED`. ADR-0020 stated it directly: "Whether every structurally
valid future Verification request must yield a determination remains undecided." ADR-0021 preserved
it unchanged: totality "remain[s] unresolved/deferred exactly as before this ADR."

A sequence of read-only process gates (M0-15EQ through M0-15ET) selected this question as the next
Verification discovery target and gathered its evidence without deciding it. That discovery
established:

- no accepted Verification authority (ADR-0015 through ADR-0021) positively requires that every
  semantically valid minimum Verification request produce a successful minimum judgment;
- no accepted Verification authority positively permits a semantically valid minimum request to
  exist without a successful determination;
- the ADR-0020 / ADR-0021 clauses recording `VERIFICATION_TOTALITY_NOT_ESTABLISHED` are direct
  authority for the *pre-decision unresolved status* only — they are not evidence that a mandatory
  totality requirement is false, and not evidence that a non-total case exists;
- ADR-0020's conditional wording ("when Verification succeeds in producing a correctness/validity
  judgment") is neutral for totality — it is compatible with a mandatory totality requirement and
  with the absence of one, and is not evidence that a valid request can exist without a judgment;
- the case where an upstream Prediction / Counterfactual result contains zero consequence items,
  and the zero-subject transport case, both lie **outside** the totality domain — in neither does a
  semantically valid minimum Verification request exist (ADR-0016, ADR-0019), so neither supports or
  contradicts a totality requirement.

A subsequent decision review (M0-15EU) evaluated three positions — totality required by the minimum
(A), totality not required by the minimum (B), and totality left unresolved (C) — against that
evidence and against the accepted minimum-contract decision methodology, and approved B. This ADR
records the result of that approval. It does not reopen the discovery or the review, and it does not
create any production contract.

## Decision

### Minimum totality requirement

The minimum Verification semantic contract does **not** require every semantically valid minimum
Verification request to produce a successful minimum Verification judgment.

Conceptually: `MINIMUM_VERIFICATION_CONTRACT_DOES_NOT_REQUIRE_TOTALITY`, i.e.
`TOTALITY_NOT_REQUIRED_BY_MINIMUM`.

This is a **requirement-level** decision. It concerns only whether totality is one of the mandatory
semantic invariants of the minimum Verification contract. It does **not** assert the existence of
any concrete case in which a valid minimum request produces no judgment.

### "Not required" precision — critical boundary

This ADR freezes `NOT_REQUIRED`. It does **not** freeze, and it explicitly distinguishes this
decision from, every one of the following: `NON_TOTAL`, `NOT_TOTAL`, `OPTIONAL_RESULT`,
`NO_JUDGMENT_EXISTS`, `JUDGMENT_ABSENCE_EXISTS`, `MAY_RETURN_NOTHING`, `CAN_FAIL`, `UNVERIFIABLE`,
`PARTIAL`, `UNKNOWN`, `INDETERMINATE`.

Accordingly, this ADR does **not** state or imply any of:

- "Verification is non-total";
- "some semantically valid Verification request necessarily produces no judgment";
- "some semantically valid Verification request definitely has no judgment";
- "Verification supports a no-judgment case";
- "a successful determination is optional";
- "a Verification result is optional", "`VerificationResult | None`", or "`Optional[VerificationResult]`";
- "a result status must encode the absence of a judgment".

The precise and only meaning frozen here: **totality is not one of the mandatory semantic invariants
of the minimum Verification contract.** Whether a non-total case exists, what it would mean, and
whether it would produce anything, are all separate questions this ADR does not touch (see
"Non-success boundary" below).

### Requirement resolution token

This ADR freezes `MINIMUM_TOTALITY_REQUIREMENT_RESOLVED_AS_NOT_REQUIRED`.

This supersedes the prior open state `VERIFICATION_TOTALITY_NOT_ESTABLISHED` **only** with respect
to the single narrower question: *is totality mandatory for the minimum Verification semantic
contract?* The answer to that question is now `NOT_REQUIRED`.

This ADR does **not** claim that every possible future totality question is permanently closed. A
future, separately evidenced decision may still address totality for a richer or specialized layer
(see "Future specialized totality" below).

### Future specialized totality

`FUTURE_SPECIALIZED_TOTALITY_REQUIREMENT_NOT_PROHIBITED`.

A future, separately evidenced specialized Verification operation or capability may require that
every valid request **within its own scope** produce a successful judgment. Such a richer
requirement does not contradict the minimum contract frozen here: `NOT_REQUIRED` at the minimum
level does not forbid a stricter guarantee at a higher, separately decided level. This ADR does not
design, name, or scope any such capability.

### Semantic content preserved — ADR-0020 relationship

ADR-0020 remains authoritative and unchanged.
`ONE_SUCCESSFUL_CORRECTNESS_VALIDITY_DETERMINATION_PER_MINIMUM_VERIFICATION_JUDGMENT` remains the
authoritative description of the minimum successful Verification judgment.

This ADR does not redefine the successful judgment, the minimum subject, the undifferentiated
correctness/validity axis, the derivation-context scope, or judgment cardinality. ADR-0020 tells
what the minimum successful judgment **is** when one is semantically produced. ADR-0022 decides only
that producing such a judgment for every semantically valid minimum request is **not** a mandatory
minimum-contract invariant.

`SUCCESSFUL_JUDGMENT_ATOM_MEANINGFUL_WITHOUT_MANDATORY_TOTALITY`: ADR-0020's atom remains a complete
semantic description of a successful judgment even though the minimum contract does not mandate that
every valid request produce one. This statement does not describe what happens when a successful
judgment is not produced; it records only that the atom's meaning does not depend on a mandatory
totality invariant.

### ADR-0021 relationship — methodological precedent only

ADR-0021 is classified here as `ANALOGOUS_MINIMUM_REQUIREMENT_DECISION_PATTERN`. It is **not**
substantive totality authority, and this ADR does **not** state that ADR-0021 implies totality must
be not required.

Only ADR-0021's accepted decision methodology is reused:

- a mandatory dimension of the minimum semantic contract is frozen only when there is sufficient
  evidence of its necessity;
- an unsupported mandatory dimension is not added to the minimum semantic contract;
- `NOT_REQUIRED` does not forbid richer future semantics under their own, separately evidenced
  decisions.

### Candidate A (totality required by the minimum) — why not selected

A candidate requiring every semantically valid minimum Verification request to produce a successful
minimum judgment is **semantically coherent** and is **not** rejected as contradictory or
impossible. It is not selected because:

- no accepted Verification authority demonstrates that a mandatory totality requirement is necessary
  for the minimum contract;
- ADR-0020's successful judgment atom remains meaningful without a mandatory totality requirement,
  so totality is not needed for the minimum contract to be coherent;
- requiring universal totality would add an unsupported mandatory invariant to the minimum semantic
  contract;
- as a secondary consideration, its reversibility concern is conditional: Candidate A would impose a
  universal requirement over every semantically valid *minimum* Verification request, and it would
  need revision only if future accepted architecture established that a request still governed by
  that same minimum Verification contract may legitimately exist without a successful judgment. The
  mere later existence of a differently scoped or specialized Verification capability would not, by
  itself, contradict Candidate A.

Ordinary-language intuitions about how "verification" commonly works (for example, "verification
must always return a verdict") are not treated as architectural evidence and played no part in this
rejection.

### Candidate C (totality remains unresolved) — why not selected

Leaving totality unresolved was a safe and coherent option, fully consistent with accepted
architecture, and this ADR does not treat it as wrong. It is not selected because the narrower
necessity question is now sufficiently bounded: a mandatory totality requirement is not necessary
for ADR-0020's successful judgment atom to remain meaningful, and the accepted minimum-contract
decision methodology permits resolving that mandatory-requirement question now, as `NOT_REQUIRED`,
rather than leaving it open indefinitely while it continues to sit in the output-semantic
prerequisite set.

### Adjacent precedent classification

The following are used only to show that a judgment- or derivation-producing operation elsewhere in
this codebase can have a legitimate outcome in which no judgment / no derived content is produced —
that such a design is architecturally coherent. None of them is Verification authority, none makes
non-totality mandatory for Verification, and no vocabulary is imported from any of them:

- **ADR-0011** (Prediction / Counterfactual result-state semantics) — `UPSTREAM_PRECEDENT`. A valid
  Prediction / Counterfactual derivation may legitimately sustain zero consequence statements
  (its "Insufficient Knowledge" state), and that is recorded there as a legitimate semantic outcome
  of a valid derivation attempt, not an exception.
- **ADR-0014** (Evaluation result structure) — `ADJACENT_ARCHITECTURE_PRECEDENT`. A structurally
  valid Evaluation request may semantically yield no utility/value judgment (`NO_JUDGMENT`), a valid
  semantic result condition in its own right.
- **`ReasoningOutcome`** unresolved behaviour — `ADJACENT_ARCHITECTURE_PRECEDENT`. It carries a
  valid unresolved state that is not a technical failure.

`Evaluation != Verification`, and Prediction / Counterfactual result-state ownership is explicitly
not Verification's (ADR-0011). These precedents inform the coherence and reversibility analysis
only.

### Discovery-evidence precision

- The ADR-0020 / ADR-0021 clauses recording `VERIFICATION_TOTALITY_NOT_ESTABLISHED` were
  `DIRECT_AUTHORITY_FOR_PRE_DECISION_UNRESOLVED_STATUS`. They were not evidence that a mandatory
  totality requirement is false, and this ADR does not present them as such.
- ADR-0020's wording "when Verification succeeds in producing a correctness/validity judgment" was
  `NEUTRAL / INSUFFICIENT_TO_DECIDE` for totality. This ADR does not present it as evidence that a
  non-total case exists.

### AGENTS.md scope

`EU_AGENTS_ATTRIBUTION_NOT_USED_AS_SEMANTIC_AUTHORITY`. `AGENTS.md`'s governing rule concerns not
introducing speculative or shared abstractions before a concrete use demonstrates they are needed;
it is not a general rule about semantic invariants and it does not directly decide the totality
question. This ADR does not rely on `AGENTS.md` for the totality semantic decision. The reasoning
above rests on ADR-0021's explicit minimum-contract methodology and on ADR-0020's successful
judgment atom.

### Non-success boundary

`NON_SUCCESS_SEMANTICS_REMAIN_DEFERRED`, exactly as prior ADRs left it. This ADR introduces no
Verification state, vocabulary, or representation for the absence of a successful determination —
not `NO_JUDGMENT`, `UNKNOWN`, `UNVERIFIED`, `INDETERMINATE`, `FAILED`, `INSUFFICIENT_EVIDENCE`,
`NOT_VERIFIABLE`, `UNRESOLVED`, `NO_RESULT`, or any equivalent. It does not decide **why** a
successful determination might not occur, **whether** such a case occurs at all, or **whether** such
a case would produce any result. Totality (a requirement-level question) and non-success (what any
future non-total semantic condition would mean, if such a condition is separately established) are
distinct decisions; this ADR makes only the former.

### Output representation boundary

`OUTPUT_REPRESENTATION_REMAINS_UNRESOLVED`. This ADR does not approve `bool`, `str`, an `Enum`, a
`status` field, a `judgment` field, a payload shape, a score, a confidence value, `Optional`, or
`None` as any part of a Verification output. The existence-or-not of a mandatory totality invariant
is a semantic question, not a representational one.

### Result-envelope boundary

`RESULT_ENVELOPE_CARDINALITY_REMAINS_DEFERRED`. `NOT_REQUIRED` totality does **not** imply
zero-or-one results, an optional result, a nullable result, or "one result carrying a status". This
ADR decides no result container topology and infers none from the decision recorded here.

### Operation-cardinality boundary

`OPERATION_JUDGMENT_CARDINALITY_REMAINS_DEFERRED`. This ADR does not infer one request per
operation, one operation per request, or that a non-mandatory totality requirement means an
operation may produce zero judgments. Operation semantics remain a separate, deferred concern.

### Polarity boundary

ADR-0021 remains authoritative: minimum mandatory polarity is `NOT REQUIRED`. This ADR does not
reopen polarity topology or vocabulary, and it does not tie totality to polarity in either
direction.

### Correlation boundary

`A1_PARTIAL_CARRIER_SEMANTICS_APPROVED`, `A1_COMPLETE_CORRELATION_SEMANTICS_NOT_APPROVED`, and
`COMPLETE_CORRELATION_REPRESENTATION_REMAINS_UNREADY` all remain exactly as ADR-0018, ADR-0020, and
ADR-0021 left them. Totality does not modify correlation semantics.

### Target / judgment-basis / materialization boundary

`TARGET_FUTURE_CORRELATION_ROLE_REMAINS_UNRESOLVED`, `ADDITIONAL_BASIS_REMAINS_UNRESOLVED`, and
`MATERIALIZATION_REMAINS_DEFERRED`, exactly as prior ADRs left them. This ADR does not add target to
any Verification decision, does not decide what sustains a correctness/validity determination, and
approves no resolver or materializer.

### Structural contracts

Not approved: `VerificationRequest`, `VerificationResult`, `VerificationStatus`.
`REQUEST_STRUCTURAL_DISCOVERY` and `RESULT_STRUCTURAL_DISCOVERY` remain **BLOCKED**.
`STRUCTURAL_CONTRACTS_REMAIN_BLOCKED`. This ADR alone does not run a structural-prerequisite
readiness review; it resolves only the minimum totality requirement question.

### Execution

`VERIFICATION_EXECUTION_REMAINS_BLOCKED`. This ADR does not approve `VerificationExecutor`,
`VerificationPort`, a `VerificationEngine` implementation, `VerificationService`,
`VerificationPolicy`, `VerificationAdapter`, or `VerificationExecutionError`.
`OPERATION_JUDGMENT_CARDINALITY_REMAINS_DEFERRED` is preserved.

### World Model / Prediction-Counterfactual execution

World Model production remains **BLOCKED** by ADR-0006. Prediction / Counterfactual Implementation
Gate item 4 (execution port) remains **PARKED/BLOCKED**. Neither is altered by this ADR.

### Provider independence

This decision is independent of any LLM, `ModelRouter`, provider, prompt, temperature, tooling, JSON
schema, or model confidence, consistent with ADR-0002.

### Single semantic increment

`ONE_NEW_VERIFICATION_TOTALITY_SEMANTIC_INCREMENT_FAMILY`. This ADR contains exactly one new
semantic increment family: the minimum mandatory totality requirement is `NOT_REQUIRED`. Everything
else in this ADR is a scope boundary, preserved prior authority, rationale, or future-compatibility
statement. No non-success semantics, result topology, execution semantics, or output representation
is introduced.

### Minimum-novelty rationale

The minimum Verification semantic contract should carry only invariants demonstrated to be
necessary. ADR-0020 already provides a meaningful successful judgment atom, and no accepted
Verification authority demonstrates that requiring that atom for every semantically valid minimum
request is necessary for the minimum contract to remain coherent. Freezing a mandatory totality
invariant would therefore add an unsupported invariant. Resolving the mandatory-requirement question
as `NOT_REQUIRED`, while leaving a future specialized totality requirement possible rather than
foreclosing it, preserves reversibility toward whatever a future, separately evidenced decision
might approve.

### Reversibility

`NOT_REQUIRED` does not mean `FORBIDDEN`. A future, separately evidenced specialized Verification
operation or capability may require totality within its own scope without contradicting this ADR.
This ADR does not approve any such capability; it records only that none of them would need to
contradict or retract the decision made here.

### Decision summary

| Concern | Decision |
| --- | --- |
| Successful minimum judgment atom | One correctness/validity determination (unchanged, ADR-0020) |
| Minimum mandatory polarity | Not required (unchanged, ADR-0021) |
| Mandatory totality in the minimum contract | Not required |
| Verification asserted non-total | No |
| A concrete no-judgment case asserted to exist | No |
| Future specialized totality requirement | Not prohibited; separate future decision |
| Prior open state `VERIFICATION_TOTALITY_NOT_ESTABLISHED` | Superseded only for the mandatory-minimum-requirement question |
| Non-success semantics | Deferred |
| Output representation | Unresolved |
| Result-envelope cardinality | Deferred |
| Operation-judgment cardinality | Deferred |
| Complete correlation representation | Unready |
| Target future role / judgment basis / materialization | Unresolved / deferred |
| Structural contracts | Blocked |
| Execution | Blocked |

## Not Decided Here

- whether a semantically valid minimum Verification request ever produces no successful determination
- the semantic character of any non-total outcome
- non-success vocabulary or states
- whether a non-total outcome produces any result
- output representation
- output field name or type
- result-envelope cardinality or topology
- operation-judgment cardinality
- request or result structure
- complete correlation representation
- target future correlation role
- additional judgment basis
- materialization / resolution
- any future specialized totality requirement and its scope
- polarity topology or vocabulary
- persistence, serialization, or API/network contracts

## Consequences

**Positive:**

- The minimum Verification semantic contract no longer carries an unresolved mandatory totality
  question in its output-semantic prerequisite set; the mandatory-requirement question is resolved
  as `NOT_REQUIRED`.
- The decision adds no unsupported mandatory invariant to the minimum contract.
- ADR-0020's successful judgment atom and every other prior Verification decision are reused without
  modification or reinterpretation.
- Full reversibility toward a future, separately evidenced specialized totality requirement is
  preserved.
- No speculative structure, status vocabulary, result topology, or representation is introduced.
- The decision is deliberately narrow: it is independent of non-success semantics, output
  representation, result-envelope cardinality, operation cardinality, correlation, and polarity.

**Tradeoff:**

- The output-semantic prerequisite set ADR-0015 identified remains only partially resolved;
  non-success semantics, output representation, result-envelope cardinality, and complete
  correlation representation are all still open, and structural contract discovery remains blocked.
- Whether any non-total outcome actually occurs, and what it would mean, is left entirely to a
  separate future decision; this ADR neither affirms nor denies its existence.
- A future decision may still need to determine whether a specialized Verification capability
  requires totality within its own scope, and none of that work is done here.

## ADR Relationship

ADR-0022 complements ADR-0015, ADR-0016, ADR-0017, ADR-0018, ADR-0019, ADR-0020, and ADR-0021. It
resolves only the minimum totality **requirement** question — whether producing a successful minimum
judgment for every semantically valid minimum request is a mandatory invariant of the minimum
Verification contract — and answers it `NOT_REQUIRED`. It supersedes none of the prior ADRs. ADR-0020
remains authoritative for the successful judgment atom itself; the prior
`VERIFICATION_TOTALITY_NOT_ESTABLISHED` state that ADR-0020 and ADR-0021 recorded is narrowed by this
ADR only for the mandatory-minimum-requirement question, not resolved in full. ADR-0021 is reused
only as an analogous minimum-requirement decision methodology, not as substantive totality authority.
ADR-0011 and ADR-0014 are adjacent architectural precedents for the coherence of a legitimate
no-judgment / no-derived-content outcome elsewhere in the codebase; neither is Verification
authority, and no vocabulary is imported from them.
