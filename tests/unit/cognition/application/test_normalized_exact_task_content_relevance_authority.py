import inspect
from dataclasses import replace

import pytest

from noema.cognition.application import (
    ContextRelevanceAuthority,
    NormalizedExactTaskContentRelevanceAuthority,
    RuntimeContentReferenceAuthority,
    RuntimeContentReferenceNotFoundError,
)
from noema.cognition.domain.context_composition import (
    ContextCandidate,
    ContextPackageZone,
    ContextSensitivity,
    ContextSlice,
    ContextSliceType,
    ContextTrustLevel,
)

_TASK_REF = "task:current"


class _RecordingContentAuthority(RuntimeContentReferenceAuthority):
    __slots__ = ("resolved_refs",)

    def __init__(self) -> None:
        super().__init__()
        self.resolved_refs: list[str] = []

    def resolve(self, *, content_ref: str) -> str:
        self.resolved_refs.append(content_ref)
        return super().resolve(content_ref=content_ref)


def _candidate(content_ref: str) -> ContextCandidate:
    return ContextCandidate(
        context_slice=ContextSlice(
            slice_type=ContextSliceType.TASK,
            content_ref=content_ref,
            zone=ContextPackageZone.COGNITIVE_STATE,
            sensitivity=ContextSensitivity.SECRET,
            trust=ContextTrustLevel.UNVERIFIED,
            instruction_authority=None,
            provenance_ref="provenance:1",
            content_size=5,
        ),
        relevance=None,
        age=None,
    )


def _judge(
    task_payload: str, *candidate_payloads: str
) -> tuple[tuple[float | None, ...], _RecordingContentAuthority]:
    content_authority = _RecordingContentAuthority()
    content_authority.register(content_ref=_TASK_REF, payload=task_payload)
    candidates = []
    for index, payload in enumerate(candidate_payloads):
        content_ref = f"task:prior:{index}"
        content_authority.register(content_ref=content_ref, payload=payload)
        candidates.append(_candidate(content_ref))
    authority = NormalizedExactTaskContentRelevanceAuthority(
        runtime_content_authority=content_authority
    )
    return authority.judge(task_ref=_TASK_REF, candidates=tuple(candidates)), content_authority


# --- construction and contract ----------------------------------------------


def test_constructor_accepts_runtime_content_authority() -> None:
    NormalizedExactTaskContentRelevanceAuthority(
        runtime_content_authority=RuntimeContentReferenceAuthority()
    )


def test_constructor_rejects_invalid_content_authority() -> None:
    with pytest.raises(TypeError, match="runtime_content_authority"):
        NormalizedExactTaskContentRelevanceAuthority(
            runtime_content_authority=object()  # type: ignore[arg-type]
        )


def test_constructor_requires_content_authority() -> None:
    with pytest.raises(TypeError):
        NormalizedExactTaskContentRelevanceAuthority()  # type: ignore[call-arg]


def test_realization_satisfies_context_relevance_authority() -> None:
    authority = NormalizedExactTaskContentRelevanceAuthority(
        runtime_content_authority=RuntimeContentReferenceAuthority()
    )
    assert isinstance(authority, ContextRelevanceAuthority)


def test_judge_is_synchronous() -> None:
    assert not inspect.iscoroutinefunction(NormalizedExactTaskContentRelevanceAuthority.judge)


# --- match semantics -----------------------------------------------------------


def test_exact_substantive_equality_is_fully_relevant() -> None:
    result, _ = _judge("What is Noema?", "What is Noema?")
    assert result == (1.0,)


def test_mismatch_has_no_relevance_judgment() -> None:
    result, _ = _judge("What is Noema?", "Something else.")
    assert result == (None,)


@pytest.mark.parametrize("task_payload", ["", " \t\n\r\n  "])
def test_task_without_substantive_content_yields_all_none(task_payload: str) -> None:
    result, _ = _judge(task_payload, task_payload, "anything", "")
    assert result == (None, None, None)


@pytest.mark.parametrize("task_payload", ["", "   \n"])
def test_candidate_contents_are_not_resolved_without_task_judgment_basis(
    task_payload: str,
) -> None:
    _, content_authority = _judge(task_payload, "a", "b")
    assert content_authority.resolved_refs == [_TASK_REF]


def test_empty_candidate_has_no_relevance_judgment() -> None:
    result, _ = _judge("question", "")
    assert result == (None,)


def test_whitespace_only_candidate_has_no_relevance_judgment() -> None:
    result, _ = _judge("question", " \t\n ")
    assert result == (None,)


@pytest.mark.parametrize(
    ("task_payload", "candidate_payload"),
    [
        ("question", " question"),
        ("question", "question "),
        ("a question", "a  question"),
        ("Question", "question"),
        ("question?", "question"),
    ],
    ids=["leading-whitespace", "trailing-whitespace", "interior-whitespace", "case", "punctuation"],
)
def test_non_normalized_differences_remain_significant(
    task_payload: str, candidate_payload: str
) -> None:
    result, _ = _judge(task_payload, candidate_payload)
    assert result == (None,)


def test_crlf_and_lf_normalize_equivalently() -> None:
    result, _ = _judge("line one\r\nline two", "line one\nline two")
    assert result == (1.0,)


def test_cr_and_lf_normalize_equivalently() -> None:
    result, _ = _judge("line one\rline two", "line one\nline two")
    assert result == (1.0,)


def test_nfc_canonical_equivalents_match() -> None:
    result, _ = _judge("café", "café")
    assert result == (1.0,)


def test_nfkc_compatibility_equivalents_remain_distinct() -> None:
    result, _ = _judge("ﬁle", "file")
    assert result == (None,)


def test_input_order_is_preserved() -> None:
    result, content_authority = _judge("question", "other", "question", "another")
    assert result == (None, 1.0, None)
    assert content_authority.resolved_refs == [
        _TASK_REF,
        "task:prior:0",
        "task:prior:1",
        "task:prior:2",
    ]


def test_duplicate_matching_candidates_each_receive_full_relevance() -> None:
    result, _ = _judge("question", "question", "question")
    assert result == (1.0, 1.0)


def test_task_is_resolved_exactly_once() -> None:
    _, content_authority = _judge("question", "question", "other", "question")
    assert content_authority.resolved_refs.count(_TASK_REF) == 1


def test_empty_candidate_tuple_yields_empty_result() -> None:
    result, _ = _judge("question")
    assert result == ()


# --- failure propagation ---------------------------------------------------------


def test_unresolved_task_propagates() -> None:
    authority = NormalizedExactTaskContentRelevanceAuthority(
        runtime_content_authority=RuntimeContentReferenceAuthority()
    )
    with pytest.raises(RuntimeContentReferenceNotFoundError):
        authority.judge(task_ref=_TASK_REF, candidates=())


def test_unresolved_candidate_with_substantive_task_propagates() -> None:
    content_authority = RuntimeContentReferenceAuthority()
    content_authority.register(content_ref=_TASK_REF, payload="question")
    authority = NormalizedExactTaskContentRelevanceAuthority(
        runtime_content_authority=content_authority
    )
    with pytest.raises(RuntimeContentReferenceNotFoundError):
        authority.judge(task_ref=_TASK_REF, candidates=(_candidate("task:unregistered"),))


def test_failure_on_later_candidate_returns_no_partial_result() -> None:
    content_authority = _RecordingContentAuthority()
    content_authority.register(content_ref=_TASK_REF, payload="question")
    content_authority.register(content_ref="task:prior:0", payload="question")
    authority = NormalizedExactTaskContentRelevanceAuthority(
        runtime_content_authority=content_authority
    )
    returned: list[tuple[float | None, ...]] = []

    with pytest.raises(RuntimeContentReferenceNotFoundError):
        returned.append(
            authority.judge(
                task_ref=_TASK_REF,
                candidates=(_candidate("task:prior:0"), _candidate("task:unregistered")),
            )
        )

    assert returned == []
    assert content_authority.resolved_refs == [_TASK_REF, "task:prior:0", "task:unregistered"]


# --- determinism and purity ------------------------------------------------------


def test_identical_inputs_produce_identical_results() -> None:
    content_authority = RuntimeContentReferenceAuthority()
    content_authority.register(content_ref=_TASK_REF, payload="question")
    content_authority.register(content_ref="task:prior:0", payload="question")
    content_authority.register(content_ref="task:prior:1", payload="other")
    authority = NormalizedExactTaskContentRelevanceAuthority(
        runtime_content_authority=content_authority
    )
    candidates = (_candidate("task:prior:0"), _candidate("task:prior:1"))

    first = authority.judge(task_ref=_TASK_REF, candidates=candidates)
    second = authority.judge(task_ref=_TASK_REF, candidates=candidates)

    assert first == second == (1.0, None)


def test_judging_does_not_mutate_candidates() -> None:
    content_authority = RuntimeContentReferenceAuthority()
    content_authority.register(content_ref=_TASK_REF, payload="question")
    content_authority.register(content_ref="task:prior:0", payload="question")
    authority = NormalizedExactTaskContentRelevanceAuthority(
        runtime_content_authority=content_authority
    )
    candidate = _candidate("task:prior:0")
    snapshot = replace(candidate)
    candidates = (candidate,)

    authority.judge(task_ref=_TASK_REF, candidates=candidates)

    assert candidates == (candidate,)
    assert candidates[0] is candidate
    assert candidate == snapshot
    assert candidate.relevance is None
