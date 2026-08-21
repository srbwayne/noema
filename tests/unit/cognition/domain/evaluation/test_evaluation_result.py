from dataclasses import FrozenInstanceError, fields
from typing import get_type_hints

import pytest

from noema.cognition.domain.errors import InvalidEvaluationResultError
from noema.cognition.domain.evaluation import EvaluationResult, EvaluationStatus
from noema.shared.domain import DomainError


class StrSubclass(str):
    """A legitimate str subclass, used to exercise the isinstance contract."""


def judged_result(**changes: object) -> EvaluationResult:
    values: dict[str, object] = {
        "target_ref": "target-1",
        "consequence": "latency decreases",
        "status": EvaluationStatus.JUDGED,
        "utility_judgment": "beneficial",
    }
    values.update(changes)
    return EvaluationResult(**values)


def no_judgment_result(**changes: object) -> EvaluationResult:
    values: dict[str, object] = {
        "target_ref": "target-1",
        "consequence": "latency decreases",
        "status": EvaluationStatus.NO_JUDGMENT,
        "utility_judgment": None,
    }
    values.update(changes)
    return EvaluationResult(**values)


# ---------- EvaluationStatus ----------


def test_evaluation_status_has_exact_two_members() -> None:
    assert list(EvaluationStatus) == [
        EvaluationStatus.JUDGED,
        EvaluationStatus.NO_JUDGMENT,
    ]


def test_evaluation_status_values() -> None:
    assert EvaluationStatus.JUDGED.value == "judged"
    assert EvaluationStatus.NO_JUDGMENT.value == "no_judgment"


# ---------- EvaluationResult: shape ----------


def test_evaluation_result_has_exact_fields() -> None:
    assert tuple(field.name for field in fields(EvaluationResult)) == (
        "target_ref",
        "consequence",
        "status",
        "utility_judgment",
    )


def test_evaluation_result_has_exact_type_hints() -> None:
    hints = get_type_hints(EvaluationResult)
    assert hints == {
        "target_ref": str,
        "consequence": str,
        "status": EvaluationStatus,
        "utility_judgment": str | None,
    }


def test_evaluation_result_is_frozen_slotted_and_has_no_dict() -> None:
    result = judged_result()
    assert not hasattr(result, "__dict__")
    with pytest.raises(FrozenInstanceError):
        result.target_ref = "other"  # type: ignore[misc]


def test_evaluation_result_constructor_is_keyword_only() -> None:
    with pytest.raises(TypeError):
        EvaluationResult(  # type: ignore[misc]
            "target-1", "latency decreases", EvaluationStatus.JUDGED, "beneficial"
        )


def test_evaluation_result_requires_every_field() -> None:
    with pytest.raises(TypeError):
        EvaluationResult(  # type: ignore[call-arg]
            target_ref="target-1",
            consequence="latency decreases",
            status=EvaluationStatus.JUDGED,
        )


# ---------- happy paths ----------


def test_evaluation_result_valid_judged_with_textual_judgment() -> None:
    result = EvaluationResult(
        target_ref="target-1",
        consequence="latency decreases",
        status=EvaluationStatus.JUDGED,
        utility_judgment="beneficial",
    )
    assert result.target_ref == "target-1"
    assert result.consequence == "latency decreases"
    assert result.status is EvaluationStatus.JUDGED
    assert result.utility_judgment == "beneficial"


def test_evaluation_result_valid_no_judgment_with_none() -> None:
    result = EvaluationResult(
        target_ref="target-1",
        consequence="latency decreases",
        status=EvaluationStatus.NO_JUDGMENT,
        utility_judgment=None,
    )
    assert result.status is EvaluationStatus.NO_JUDGMENT
    assert result.utility_judgment is None


# ---------- target_ref validation ----------


@pytest.mark.parametrize("value", [None, 1, True, "", " ", "\t", "\n"])
def test_evaluation_result_rejects_invalid_target_ref(value: object) -> None:
    with pytest.raises(InvalidEvaluationResultError, match="target_ref"):
        judged_result(target_ref=value)


def test_evaluation_result_preserves_target_ref_whitespace_exactly() -> None:
    padded = "  padded value  "
    result = judged_result(target_ref=padded)
    assert result.target_ref == padded


# ---------- consequence validation ----------


@pytest.mark.parametrize("value", [None, 1, True, "", " ", "\t", "\n"])
def test_evaluation_result_rejects_invalid_consequence(value: object) -> None:
    with pytest.raises(InvalidEvaluationResultError, match="consequence"):
        judged_result(consequence=value)


def test_evaluation_result_preserves_consequence_whitespace_exactly() -> None:
    padded = "  padded value  "
    result = judged_result(consequence=padded)
    assert result.consequence == padded


# ---------- status validation ----------


@pytest.mark.parametrize("value", [None, "judged", "JUDGED", "no_judgment", 1, True, object()])
def test_evaluation_result_rejects_invalid_status(value: object) -> None:
    with pytest.raises(InvalidEvaluationResultError, match="status"):
        judged_result(status=value)


# ---------- utility_judgment validation ----------


@pytest.mark.parametrize("value", [1, True, "", " ", "\t", "\n"])
def test_evaluation_result_rejects_invalid_utility_judgment(value: object) -> None:
    with pytest.raises(InvalidEvaluationResultError, match="utility_judgment"):
        judged_result(utility_judgment=value)


def test_evaluation_result_preserves_utility_judgment_text_exactly() -> None:
    padded = "  beneficial overall  "
    result = judged_result(utility_judgment=padded)
    assert result.utility_judgment == padded


def test_evaluation_result_accepts_str_subclass_utility_judgment() -> None:
    result = judged_result(utility_judgment=StrSubclass("beneficial"))
    assert result.utility_judgment == "beneficial"


def test_evaluation_result_accepts_str_subclass_target_ref() -> None:
    result = judged_result(target_ref=StrSubclass("target-1"))
    assert result.target_ref == "target-1"


def test_evaluation_result_accepts_str_subclass_consequence() -> None:
    result = judged_result(consequence=StrSubclass("latency decreases"))
    assert result.consequence == "latency decreases"


# ---------- cross-validation matrix ----------


def test_evaluation_result_rejects_judged_with_none_utility_judgment() -> None:
    with pytest.raises(InvalidEvaluationResultError, match="inconsistent"):
        EvaluationResult(
            target_ref="target-1",
            consequence="latency decreases",
            status=EvaluationStatus.JUDGED,
            utility_judgment=None,
        )


def test_evaluation_result_rejects_no_judgment_with_textual_value() -> None:
    with pytest.raises(InvalidEvaluationResultError, match="inconsistent"):
        EvaluationResult(
            target_ref="target-1",
            consequence="latency decreases",
            status=EvaluationStatus.NO_JUDGMENT,
            utility_judgment="beneficial",
        )


# ---------- equality / hashing ----------


def test_evaluation_result_is_hashable() -> None:
    hash(judged_result())
    hash(no_judgment_result())


def test_evaluation_result_structural_equality() -> None:
    first = judged_result()
    second = judged_result()
    assert first == second
    assert hash(first) == hash(second)


@pytest.mark.parametrize(
    ("field_name", "other_value"),
    [
        ("target_ref", "target-2"),
        ("consequence", "latency increases"),
        ("utility_judgment", "harmful"),
    ],
)
def test_evaluation_result_structural_inequality(field_name: str, other_value: str) -> None:
    first = judged_result()
    second = judged_result(**{field_name: other_value})
    assert first != second


# ---------- errors ----------


def test_invalid_evaluation_result_error_inherits_directly_from_domain_error() -> None:
    assert InvalidEvaluationResultError.__bases__ == (DomainError,)


def test_invalid_evaluation_result_error_is_exported_from_errors_package() -> None:
    from noema.cognition.domain import errors

    assert "InvalidEvaluationResultError" in errors.__all__
    assert errors.InvalidEvaluationResultError is InvalidEvaluationResultError


# ---------- public surface ----------


def test_evaluation_package_exports_result_and_status() -> None:
    from noema.cognition.domain import evaluation

    assert "EvaluationResult" in evaluation.__all__
    assert "EvaluationStatus" in evaluation.__all__


def test_evaluation_package_does_not_export_invalid_evaluation_result_error() -> None:
    from noema.cognition.domain import evaluation

    assert "InvalidEvaluationResultError" not in evaluation.__all__
    assert not hasattr(evaluation, "InvalidEvaluationResultError")
