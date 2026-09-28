# ADR-0041: First Deterministic Context Relevance Realization

- Status: Accepted
- Date: 2026-09-28

## Context

ADR-0037 defined what a known `ContextCandidate.relevance` value means:
`CURRENT_TASK_PERTINENCE`, scoped to one context composition, with `None` meaning
`NO_RELEVANCE_JUDGMENT_EXISTS`. ADR-0038 assigned production authority to a generic,
Cognition-owned `COGNITION_CONTEXT_RELEVANCE_AUTHORITY`. ADR-0039 fixed the producer contract:
composition-batch granularity, positional correlation, an ordered `float | None` result, and an
operational failure kept distinct from `None`. ADR-0040 fixed integration: the authority is
invoked by `ContextPackagePreparer` after projection and before required-slice activation, results
are validated and applied by the preparer, failures propagate fail-closed, zero candidates skip the
producer, and activation is by bound authority with no feature flag.

None of those ADRs selected an algorithm. Each recorded:

```text
AUTHORIZED_DETERMINISTIC_RELEVANCE_ALGORITHM_EXISTS = NO
CONTEXT_RELEVANCE_PRODUCER_IMPLEMENTATION_READY = NO
NEXT_CONTEXT_RELEVANCE_ARCHITECTURE_BLOCKER = CONCRETE_RELEVANCE_PRODUCER_REALIZATION
```

A read-only discovery pass (POST-M0-18EH) established that:

- at the ADR-0040 invocation point, the current task's exact content and every prior-`TASK`
  candidate's exact content are resolvable, synchronously and in memory, through the existing
  `RuntimeContentReferenceAuthority`, without a second canonical-state observation and without any
  architecture dependency change;
- in the first-DIRECT runtime, `DirectReasoningOperation.execute` registers `task_ref` as a content
  reference denoting the exact `problem_statement` before `ContextPackagePreparer.prepare` runs, so
  `task_ref` is resolvable there. This is a property of the first-DIRECT runtime path, not a
  guarantee made by the generic producer contract;
- every `task_ref` and every prior-`TASK` `content_ref` is a distinct generated identifier, so
  reference equality never detects repeated task content -- only resolved payload comparison can;
- lexical scoring families (token containment, token Jaccard, character n-gram overlap, TF/TF-IDF,
  edit distance) are feasible with the standard library, but can emit known low scores for
  pertinent but differently-worded content. Under ADR-0040's accepted `REQUIRED_WHEN_PRIOR_EXISTS`
  policy, a graded lexical realization can make required `TASK` coverage unsatisfied when every
  candidate capable of satisfying that required `TASK` slot receives a known relevance value below
  `minimum_relevance`. POST-M0-18EH established this as a material operational risk for the
  explored lexical families, not as an unconditional outcome of every topic change;
- metadata-based heuristics (age, position, provenance, trust, sensitivity, authority, zone,
  content size, slice type) are prohibited relevance surrogates under ADR-0030, ADR-0037, and
  ADR-0039.

This ADR records the canonical selection of the first deterministic algorithm that realizes
`COGNITION_CONTEXT_RELEVANCE_AUTHORITY`. It authorizes the algorithmic decision only.

## Decision

### Inherited authority, not redefined

```text
CONTEXT_RELEVANCE_SEMANTIC = CURRENT_TASK_PERTINENCE
CONTEXT_RELEVANCE_SEMANTIC_SCOPE = PER_CONTEXT_COMPOSITION
CONTEXT_RELEVANCE_PRODUCTION_AUTHORITY = COGNITION_CONTEXT_RELEVANCE_AUTHORITY
NONE_RELEVANCE_SEMANTIC = NO_RELEVANCE_JUDGMENT_EXISTS
RELEVANCE_PRODUCER_GRANULARITY = COMPOSITION_BATCH
RELEVANCE_CORRELATION_AUTHORITY = POSITIONAL
ONE_AUTHORITY_PER_COMPOSITION_SCORE_SET = YES
RESULT_CARDINALITY_EQUALS_INPUT_CANDIDATE_CARDINALITY = YES
CURRENT_TASK_REFERENCE_REQUIRED = YES
RELEVANCE_PRODUCTION_FAILURE_SEMANTICS = OPERATION_LEVEL_FAILURE_DISTINCT_FROM_RESULT
RELEVANCE_PRODUCER_TIMING = AFTER_PROJECTION_BEFORE_REQUIRED_SLICE_ACTIVATION
RELEVANCE_INTEGRATION_SHAPE = PREPARER_DELEGATES_TO_DISTINCT_RELEVANCE_AUTHORITY
RELEVANCE_AUTHORITY_INTEGRATION_LAYER = COGNITION_APPLICATION
RELEVANCE_PRODUCTION_FAILURE_POLICY = FAIL_CLOSED_PROPAGATE
ZERO_CANDIDATE_RELEVANCE_POLICY = SKIP_PRODUCER
RELEVANCE_PRODUCTION_ACTIVATION_POLICY = BOUND_AUTHORITY
SEPARATE_RELEVANCE_FEATURE_FLAG = NO
KNOWN_LOW_REQUIRED_TASK_POLICY = REQUIRED_WHEN_PRIOR_EXISTS
LOW_SCORE_CLAMP_TO_MINIMUM_RELEVANCE_AUTHORIZED = NO
LEGITIMATE_LOW_SCORE_TO_NONE_SUBSTITUTION_AUTHORIZED = NO
```

All inherited unchanged from ADR-0037, ADR-0038, ADR-0039, and ADR-0040; none is reinterpreted
here.

### Algorithm selection

```text
FIRST_DETERMINISTIC_RELEVANCE_ALGORITHM = NORMALIZED_EXACT_TASK_CONTENT_MATCH
ALGORITHM_KIND = DETERMINISTIC_PARTIAL_JUDGE
DETERMINISTIC_RELEVANCE_ALGORITHM_AUTHORIZED = YES
AUTHORIZED_DETERMINISTIC_RELEVANCE_ALGORITHM_EXISTS = YES

ALGORITHM_PROVIDER_DEPENDENT = NO
ALGORITHM_MODEL_DEPENDENT = NO
ALGORITHM_VECTOR_STORE_DEPENDENT = NO
ALGORITHM_THIRD_PARTY_DEPENDENCY_REQUIRED = NO
```

`NORMALIZED_EXACT_TASK_CONTENT_MATCH` is one realization of `COGNITION_CONTEXT_RELEVANCE_AUTHORITY`.
It produces the maximal known relevance judgment for a candidate exactly when both normalized
contents have substantive content and the candidate's normalized content is identical to the
current task's normalized content, and makes no judgment otherwise. For contents on which this
realization has a judgment basis, normalized identity is sufficient for its maximal judgment: a
prior task whose substantive content is identical to the current task's substantive content is,
by ADR-0037's definition, maximally pertinent to the task designated by `task_ref`, because it is
the same task content. This is an exact-content identity test, not a similarity measure, and it
does not make similarity the definition of relevance
(`SEMANTIC_SIMILARITY_IS_RELEVANCE_DEFINITION = NO` is preserved).

The algorithm is deterministic: identical inputs always produce an identical result tuple. It
requires only Python standard-library Unicode normalization (`unicodedata`) and string operations.

### Content resolution

```text
CONTENT_RESOLUTION_STRATEGY = EXISTING_RUNTIME_CONTENT_REFERENCE_AUTHORITY
CONTENT_RESOLUTION_REQUIRED_BY_GENERIC_CONTRACT = NO
CONTENT_RESOLUTION_REQUIRED_BY_THIS_REALIZATION = YES
```

ADR-0039's generic producer contract does not require resolved content. This realization does,
because its judgment rule compares content. It resolves:

- the current task's content from `task_ref`, through the existing
  `RuntimeContentReferenceAuthority`;
- each candidate's content from `candidate.context_slice.content_ref`, through the same authority,
  only when the judgment rule requires it (see the ordering below).

Resolution through `RuntimeContentReferenceAuthority` is not a canonical-state observation
(ADR-0039), so it introduces no second snapshot. `ContextPackagePreparer` remains the sole owner of
the per-operation canonical-state observation.

Content is resolved only when the judgment rule requires it. One production operation performs
exactly this ordering:

1. resolve the current task's content from `task_ref`;
2. normalize it;
3. evaluate whether the normalized task content has substantive content (see "Judgment basis"
   below).

If the normalized task content has no substantive content, the operation has no judgment basis for
any candidate: it does not resolve any candidate's `content_ref`, and it returns a complete
positional tuple containing `None` once for every input candidate.

If the normalized task content has substantive content, the operation resolves each candidate's
`content_ref`, normalizes it, and computes that candidate's local `1.0 | None` judgment. Judgments
are retained locally, and the result tuple is returned only after the complete candidate batch has
been processed successfully.

```text
CANDIDATE_CONTENT_RESOLUTION_REQUIRED_WHEN_TASK_HAS_JUDGMENT_BASIS = YES
CANDIDATE_CONTENT_RESOLUTION_PERFORMED_WHEN_TASK_HAS_NO_JUDGMENT_BASIS = NO
ALL_NONE_RESULT_WITHOUT_CANDIDATE_RESOLUTION_WHEN_TASK_HAS_NO_JUDGMENT_BASIS = YES
```

The current task's content is resolved exactly once per production operation.

### Exact normalization

```text
NORMALIZATION_PIPELINE = NORMALIZE_LINE_ENDINGS_TO_LF_THEN_UNICODE_NFC
```

The same pipeline is applied to the current task's content and to every candidate content that is
resolved. Exactly these three steps are performed, in exactly this order:

1. replace every CRLF sequence (`"\r\n"`, U+000D U+000A) with LF (`"\n"`, U+000A);
2. replace every remaining CR (`"\r"`, U+000D) with LF (`"\n"`, U+000A);
3. apply Unicode Normalization Form C (NFC) to the result.

No other transformation is applied:

```text
UNICODE_NFC = YES
UNICODE_NFKC = NO
CASEFOLD = NO
STRIP_LEADING_OR_TRAILING_WHITESPACE = NO
INTERIOR_WHITESPACE_COLLAPSE = NO
STEMMING = NO
STOPWORD_REMOVAL = NO
PUNCTUATION_REMOVAL = NO
LOCALE_SPECIFIC_NORMALIZATION = NO
```

Consequently this realization preserves:

- case differences;
- indentation;
- interior whitespace;
- leading and trailing whitespace;
- punctuation;
- compatibility-character distinctions (for example, superscript and subscript digits, ligatures,
  and full-width forms remain distinct from their compatibility equivalents).

Rationale. This realization emits only the maximal known relevance value, `1.0`. A false-positive
equality therefore asserts maximal pertinence for content that is not identical to the current
task, which is more harmful than conservative abstention. The pipeline removes only differences
that are representational rather than textual:

- line-ending normalization removes CRLF/CR versus LF representation differences while preserving
  line structure;
- NFC canonicalizes only canonically-equivalent Unicode sequences (for example, a precomposed
  character versus its base character plus combining mark), which denote the same text.

NFKC, casefolding, and whitespace stripping or collapsing are excluded because each can equate
texts whose meaning differs -- for example `x²` and `x2` under NFKC, identifiers differing only in
case under casefolding, and code differing only in indentation under whitespace collapse.

### Judgment basis

```text
SUBSTANTIVE_CONTENT_REQUIRED_FOR_KNOWN_JUDGMENT = YES
```

A normalized text has substantive content if and only if it contains at least one character for
which Python `str.isspace()` is false:

```text
has_substantive_content(text) = any(not character.isspace() for character in text)
```

This predicate only decides whether a judgment basis exists. It does not transform the text, and it
is not part of the normalization pipeline: exact equality still compares the normalized strings
themselves, with every whitespace character preserved. An empty text has no substantive content,
and neither does a text consisting only of whitespace characters.

```text
EMPTY_CONTENT_IMPLIES_NONE = YES
WHITESPACE_ONLY_CONTENT_IMPLIES_NONE = YES
```

A whitespace-only current task cannot produce a known judgment for any candidate. A whitespace-only
candidate cannot receive a known judgment. Two identical whitespace-only payloads do not produce
`1.0`.

Whitespace in text that does have substantive content is never reinterpreted: `" foo"` and
`"foo"` both have substantive content and remain different, so they do not match.

### Exact judgment rule

For one production operation over the ordered candidate batch, with `T` the normalized current task
content and `C_i` the normalized content of the candidate at position `i`:

```text
if not has_substantive_content(T):
    every judgment[i] = None           # no candidate content is resolved
else:
    for each position i, in input order:
        if not has_substantive_content(C_i):
            judgment[i] = None
        elif C_i == T:
            judgment[i] = 1.0
        else:
            judgment[i] = None
```

Equality is exact code-point-sequence equality of the normalized strings.

```text
KNOWN_JUDGMENT_RULE = has_substantive_content(normalized_task)
                      AND has_substantive_content(normalized_candidate)
                      AND normalized_candidate == normalized_task
KNOWN_JUDGMENT_VALUE = 1.0
ABSTENTION_RULE = every other case -> None

DETERMINISTIC_RELEVANCE_KNOWN_SCORE_SET = ONE_ONLY
KNOWN_RELEVANCE_VALUE = 1.0
DETERMINISTIC_RELEVANCE_ABSTENTION_VALUE = None
DETERMINISTIC_RELEVANCE_ALGORITHM_IS_PARTIAL = YES
DIFFERENT_CONTENT_IMPLIES_ZERO_RELEVANCE = NO
DIFFERENT_CONTENT_IMPLIES_NO_JUDGMENT_BY_THIS_REALIZATION = YES
EMPTY_CONTENT_IMPLIES_NONE = YES
WHITESPACE_ONLY_CONTENT_IMPLIES_NONE = YES
```

### Meaning of `None` in this realization

`None` means exactly what it means everywhere in this domain: `NO_RELEVANCE_JUDGMENT_EXISTS`. It
does not mean:

- zero relevance;
- low relevance;
- rejection;
- resolution failure;
- producer operational failure.

This realization's semantic domain is intentionally partial. It has a basis for a known judgment
only when both normalized contents have substantive content and are identical. A content mismatch
is not evidence that the candidate is not pertinent -- pertinent content may be worded differently
-- so this realization makes no judgment for it. This is abstention, not
`LEGITIMATE_LOW_SCORE_TO_NONE_SUBSTITUTION`: the realization never computes a low score and never
replaces one with `None`. Content without substantive content -- empty or whitespace-only --
likewise provides no basis for an identity judgment, so it yields `None` rather than a known value.

### Resolution failure

```text
CONTENT_RESOLUTION_FAILURE_POLICY = FAIL_CLOSED_PROPAGATE
RESOLUTION_FAILURE_IMPLIES_NONE = NO
PARTIAL_RESULT_AFTER_RESOLUTION_FAILURE = NO
```

Fail-closed applies to every resolution that this realization actually requires and attempts. If
the current task's `task_ref` cannot be resolved, or a candidate's `content_ref` whose resolution is
required (because the current task has substantive content) cannot be resolved, the failure is an
operational failure of the production operation and propagates. It is never translated to `None`,
no result tuple is returned, and no partial result is exposed -- judgments already computed locally
for earlier candidates in the batch are discarded with the failed operation. ADR-0039's
`OPERATION_LEVEL_FAILURE_DISTINCT_FROM_RESULT` and ADR-0040's `FAIL_CLOSED_PROPAGATE` remain
authoritative; this ADR only confirms that content-resolution failure is such an operational
failure for this realization.

A future `ContextCandidate` family whose `content_ref` is not resolvable through
`RuntimeContentReferenceAuthority` causes an operational failure, not abstention, whenever this
realization needs to inspect that candidate. If the current task itself has no judgment basis,
candidate contents are not resolved and the operation legitimately returns all `None`. This is not
failure suppression: no candidate resolution is required to determine that result, so no
resolution is attempted and none fails. Whether a future candidate family should be judged by this
realization is outside this ADR; the current runtime's candidate scope is `PRIOR_TASK_ONLY`, for
which every `content_ref` is resolvable.

### Batch semantics

```text
RELEVANCE_PRODUCER_GRANULARITY = COMPOSITION_BATCH
RELEVANCE_CORRELATION_AUTHORITY = POSITIONAL
ONE_AUTHORITY_PER_COMPOSITION_SCORE_SET = YES
RESULT_CARDINALITY_EQUALS_INPUT_CANDIDATE_CARDINALITY = YES
```

A successful operation returns exactly one element per input candidate, in input order. Each element
is `1.0` or `None`, and a successful batch may contain them in any positional combination --
including all `1.0` and all `None`. A mix of `1.0` and `None` is two ordinary outcomes, not partial
failure. A zero-candidate batch is never submitted (`ZERO_CANDIDATE_RELEVANCE_POLICY =
SKIP_PRODUCER`).

### Known-low behavior

```text
KNOWN_LOW_RELEVANCE_SCORE_PRODUCED_BY_THIS_REALIZATION = NO
KNOWN_LOW_REQUIRED_TASK_FAILURE_RISK_INTRODUCED_BY_THIS_ALGORITHM = NO
```

This realization never emits a known score below `1.0`. Because
`ContextCompositionPolicy.minimum_relevance` is at most `1.0`, every known score this realization
emits satisfies the relevance condition for eligibility, so it cannot cause the known-low
required-`TASK` failure that ADR-0040 accepts under `REQUIRED_WHEN_PRIOR_EXISTS`. Whenever no
candidate matches, the result is all `None`, which ADR-0040 already establishes as equivalent to
the current runtime.

### Scale statement

On this realization's scale, the only known value is `1.0`, meaning that both normalized contents
have substantive content and the candidate's normalized content is identical to the current task's
normalized content. No threshold value of `minimum_relevance` excludes a known value produced by
this realization. This is a statement about this realization's scale only; it does not change
`minimum_relevance`'s semantics (ADR-0037) or its use by `ContextComposer`.

### Runtime consequences once bound

This ADR does not bind the realization (see below). Once a later gate binds it, it can still change
context selection, under existing `ContextComposer` rules that this ADR does not reinterpret:

- a prior `TASK` candidate whose normalized content has substantive content and is exactly
  identical to the normalized current-task content (which therefore also has substantive content)
  receives `1.0` and therefore becomes eligible for optional enrichment, which a candidate with
  `relevance=None` never is;
- repeated identical prior tasks are distinct canonical entries (ADR-0030 performs no
  deduplication), so when their content has substantive content, several of them may each receive
  `1.0` and contribute multiple structurally distinct slices, subject to existing composer rules,
  `max_slices`, and `max_total_content_size`;
- required-slot ranking remains governed by the existing canonical composer ordering, in which
  relevance is one ranking dimension among others and does not outrank the dimensions that precede
  it.

### Runtime activation

```text
PRODUCTION_BOOTSTRAP_BINDING_AUTHORIZED = NO
RUNTIME_ACTIVATION_AUTHORIZATION = DEFERRED
SEPARATE_RELEVANCE_FEATURE_FLAG = NO
CURRENT_RUNTIME_CHANGED_BY_ADR_0041 = NO
```

Algorithm authorization is separate from runtime activation. Under ADR-0040, activation is by
binding a concrete authority into the runtime object graph. This ADR does not authorize binding
this realization into the production bootstrap. Not binding it introduces no feature flag: the
concrete authority is simply absent from the canonical production object graph, and every current
configuration keeps behaving exactly as today.

A future implementation may instantiate and test this realization without making it part of the
canonical production object graph. A later gate must evaluate implementation evidence before
production bootstrap binding is authorized.

### Deferred lexical scoring

```text
LEXICAL_SCORING_FRONTIER = DEFERRED
```

The following lexical families are not selected for the first realization:

- token containment;
- token Jaccard;
- character n-gram overlap;
- TF / TF-IDF;
- edit-distance / `difflib` similarity.

They are not thereby permanently forbidden. Each emits graded known scores, including known low
scores for pertinent but differently-worded content, and therefore requires separate evidence,
calibration, and operational-risk decisions -- in particular its interaction with
`REQUIRED_WHEN_PRIOR_EXISTS` -- before it may become an authoritative relevance judgment.

### Rejected surrogates

The following remain rejected as relevance evidence under existing ADR authority (ADR-0030,
ADR-0037, ADR-0038, ADR-0039) and are not used by this realization:

- age / recency;
- position;
- provenance;
- same-runtime membership;
- trust;
- sensitivity;
- instruction authority;
- zone;
- content size;
- slice-type weighting;
- Attention score reuse;
- `CognitiveItem.relevance` reuse;
- blends that use any such prohibited surrogate as relevance evidence.

### Model-backed frontier

```text
MODEL_BACKED_REALIZATION_IS_SEPARATE_FRONTIER = YES
NEW_RUNTIME_MODEL_CALL_AUTHORIZED = NO
MODEL_OR_PROVIDER_SELECTED = NO
COGNITIVE_BUDGET_CHANGE_AUTHORIZED = NO
PORT_BOUNDARY_CHANGE_AUTHORIZED = NO
```

This ADR selects no model, provider, embedding technique, or vector store, and authorizes no model
or tool call and no `CognitiveBudget` change.

### Implementation state

```text
CONCRETE_RELEVANCE_PRODUCER_IMPLEMENTATION_AUTHORIZED = NO
CONCRETE_RELEVANCE_PRODUCER_IMPLEMENTATION_STARTED = NO
GENERIC_RELEVANCE_INTEGRATION_FOUNDATION_IMPLEMENTATION_AUTHORIZED = NO
PRODUCTION_BOOTSTRAP_BINDING_AUTHORIZED = NO
CURRENT_CONCRETE_RELEVANCE_PRODUCER_EXISTS = NO
NEXT_MILESTONE_IDENTIFIER = UNASSIGNED
M0_19_ASSIGNED = NO
```

This ADR authorizes the algorithmic decision only. It does not authorize writing source code or
tests, does not name a concrete Python class, `Protocol`, method signature, module, or exception
type, and does not change any architecture dependency allow-list.

## Not Decided Here

- Implementation of the generic integration foundation or of this realization.
- Concrete type, module placement within `cognition.application`, method signature, and the
  exception type for result-contract violations.
- Production bootstrap binding and runtime activation.
- Any lexical, graded, or model-backed scoring.
- Deduplication of repeated identical prior tasks, or any change to `ContextComposer` ordering or
  eligibility.
- Relevance judgment for any `ContextCandidate` family other than the current prior-`TASK` scope.
- A milestone identifier.

## Consequences

**Positive:**

- An authorized deterministic realization of `COGNITION_CONTEXT_RELEVANCE_AUTHORITY` now exists at
  the decision level, giving the generic integration foundation a concrete, non-speculative
  realization to be implemented against.
- The realization is provider-, model-, and dependency-free, fully deterministic, and conforms to
  the ADR-0039 batch contract and the ADR-0040 integration semantics without any architecture
  change.
- It never emits a known low score, so it introduces no known-low required-`TASK` failure, and
  whenever nothing matches its result is equivalent to the current all-`None` runtime.
- Its conservative normalization keeps its only known claim -- maximal pertinence -- restricted to
  content that is textually identical up to line-ending representation and canonical Unicode
  equivalence.

**Tradeoffs:**

- Coverage is deliberately narrow: only exact normalized repetition of substantively nonblank
  current-task content receives a known judgment; every other candidate remains `None`.
- Pertinent but differently-worded prior tasks receive no judgment, and conservative normalization
  means representational variants such as case or whitespace differences also receive none.
- Once bound, repeated identical prior tasks with substantive content may contribute multiple
  slices of identical content.
- Content resolution failure for any candidate this realization needs to inspect aborts the
  operation, which would matter for a future candidate family not resolvable through
  `RuntimeContentReferenceAuthority`.
- No runtime capability changes until separate implementation and binding gates pass.

## ADR Relationship

ADR-0041 supplements ADR-0037 (Context relevance semantics), ADR-0038 (Context relevance
ownership), ADR-0039 (Context relevance producer contract), and ADR-0040 (Context relevance producer
integration semantics). It concretizes one algorithm realization under the semantic, ownership,
contract, and integration authorities already canonical there.

```text
ADR_0041_SUPERSEDES_ADR_0037 = NO
ADR_0041_SUPERSEDES_ADR_0038 = NO
ADR_0041_SUPERSEDES_ADR_0039 = NO
ADR_0041_SUPERSEDES_ADR_0040 = NO
```

It relies on ADR-0030's rejected relevance surrogates and prior-`TASK` projection, and on ADR-0031's
first-DIRECT runtime pipeline, without changing either. It introduces no new top-level Cognition
subsystem and changes no frozen ADR-0005 component's structure.
