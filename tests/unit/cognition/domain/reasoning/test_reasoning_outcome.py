from dataclasses import MISSING, FrozenInstanceError, fields, replace

import pytest

from noema.cognition.domain.context_composition import ContextCandidate, ContextSlice
from noema.cognition.domain.errors import InvalidReasoningOutcomeError
from noema.cognition.domain.modes import CognitiveMode
from noema.cognition.domain.reasoning import (
    InformationNeed,
    ReasoningOutcome,
    ReasoningStatus,
    ReasoningStrategy,
)


def information_need(
    description: str = "Need fact A",
    *,
    subject_ref: str = "subject:123",
) -> InformationNeed:
    return InformationNeed(subject_ref=subject_ref, description=description)


def outcome(**changes: object) -> ReasoningOutcome:
    current = ReasoningOutcome(
        problem_ref="problem:123",
        strategy=ReasoningStrategy.DIRECT,
        status=ReasoningStatus.COMPLETED,
        conclusion="answer",
        reason_summary="Evidence supports the conclusion.",
        information_needs=(),
    )
    return replace(current, **changes)


def test_reasoning_outcome_has_exact_required_fields() -> None:
    contract_fields = fields(ReasoningOutcome)
    assert tuple(field.name for field in contract_fields) == (
        "problem_ref",
        "strategy",
        "status",
        "conclusion",
        "reason_summary",
        "information_needs",
    )
    assert all(
        field.default is MISSING and field.default_factory is MISSING for field in contract_fields
    )
    assert not {
        "confidence",
        "claims",
        "hypotheses",
        "evidence",
        "reasoning_steps",
        "chain_of_thought",
        "trace",
        "model",
        "provider",
    } & {field.name for field in contract_fields}


@pytest.mark.parametrize(
    "status,conclusion,needs",
    [
        (ReasoningStatus.COMPLETED, "answer", ()),
        (ReasoningStatus.PARTIAL, "partial answer", (information_need(),)),
        (ReasoningStatus.NEEDS_INFORMATION, None, (information_need(),)),
        (ReasoningStatus.UNRESOLVED, None, ()),
    ],
)
def test_reasoning_outcome_accepts_valid_status_matrix(
    status: ReasoningStatus,
    conclusion: str | None,
    needs: tuple[InformationNeed, ...],
) -> None:
    current = outcome(status=status, conclusion=conclusion, information_needs=needs)
    assert current.status is status
    assert current.conclusion == conclusion
    assert current.information_needs == needs


@pytest.mark.parametrize(
    "status,conclusion,needs",
    [
        (ReasoningStatus.COMPLETED, None, ()),
        (ReasoningStatus.COMPLETED, "answer", (information_need(),)),
        (ReasoningStatus.PARTIAL, None, (information_need(),)),
        (ReasoningStatus.PARTIAL, "partial", ()),
        (ReasoningStatus.NEEDS_INFORMATION, "answer", (information_need(),)),
        (ReasoningStatus.NEEDS_INFORMATION, None, ()),
        (ReasoningStatus.UNRESOLVED, "answer", ()),
        (ReasoningStatus.UNRESOLVED, None, (information_need(),)),
    ],
)
def test_reasoning_outcome_rejects_invalid_status_matrix(
    status: ReasoningStatus,
    conclusion: str | None,
    needs: tuple[InformationNeed, ...],
) -> None:
    with pytest.raises(InvalidReasoningOutcomeError, match="inconsistent"):
        outcome(status=status, conclusion=conclusion, information_needs=needs)


@pytest.mark.parametrize("value", [None, 1, True, "", " ", "\t", "\n"])
def test_reasoning_outcome_rejects_invalid_problem_ref(value: object) -> None:
    with pytest.raises(InvalidReasoningOutcomeError, match="problem_ref"):
        outcome(problem_ref=value)


@pytest.mark.parametrize("value", [None, "direct", 1, CognitiveMode.FAST])
def test_reasoning_outcome_requires_reasoning_strategy(value: object) -> None:
    with pytest.raises(InvalidReasoningOutcomeError, match="strategy"):
        outcome(strategy=value)


@pytest.mark.parametrize("value", [None, "completed", 1, ReasoningStrategy.DIRECT])
def test_reasoning_outcome_requires_reasoning_status(value: object) -> None:
    with pytest.raises(InvalidReasoningOutcomeError, match="status"):
        outcome(status=value)


@pytest.mark.parametrize("value", ["", " ", "\t", "\n"])
def test_reasoning_outcome_rejects_empty_conclusion(value: str) -> None:
    with pytest.raises(InvalidReasoningOutcomeError, match="conclusion"):
        outcome(conclusion=value)


@pytest.mark.parametrize("value", [None, 1, True, "", " ", "\t", "\n"])
def test_reasoning_outcome_rejects_invalid_reason_summary(value: object) -> None:
    with pytest.raises(InvalidReasoningOutcomeError, match="reason_summary"):
        outcome(reason_summary=value)


@pytest.mark.parametrize("value", [[], None, {}])
def test_reasoning_outcome_requires_information_needs_tuple(value: object) -> None:
    with pytest.raises(InvalidReasoningOutcomeError, match="tuple"):
        outcome(information_needs=value)


@pytest.mark.parametrize("value", ["need", None, ContextSlice, ContextCandidate])
def test_reasoning_outcome_requires_information_need_elements(value: object) -> None:
    with pytest.raises(InvalidReasoningOutcomeError, match="InformationNeed"):
        outcome(
            status=ReasoningStatus.PARTIAL,
            information_needs=(value,),
        )


def test_reasoning_outcome_rejects_structural_duplicate_information_needs() -> None:
    need = information_need()
    with pytest.raises(InvalidReasoningOutcomeError, match="duplicate"):
        outcome(
            status=ReasoningStatus.PARTIAL,
            information_needs=(need, need),
        )


def test_same_subject_ref_is_not_information_need_identity_and_order_is_preserved() -> None:
    first = information_need("Need fact A")
    second = information_need("Need fact B")
    current = outcome(
        status=ReasoningStatus.PARTIAL,
        conclusion="partial answer",
        information_needs=(first, second),
    )
    assert first.subject_ref == second.subject_ref
    assert first != second
    assert current.information_needs == (first, second)


def test_reasoning_outcome_is_frozen_slotted_keyword_only_and_equal() -> None:
    first = outcome()
    second = outcome()
    assert first == second
    assert not hasattr(first, "__dict__")
    with pytest.raises(FrozenInstanceError):
        first.reason_summary = "Changed"
    with pytest.raises(TypeError):
        ReasoningOutcome(
            "problem:123",
            ReasoningStrategy.DIRECT,
            ReasoningStatus.COMPLETED,
            "answer",
            "summary",
            (),
        )
