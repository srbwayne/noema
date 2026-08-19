from dataclasses import FrozenInstanceError, fields
from typing import get_type_hints

import pytest

from noema.cognition.domain.errors import InvalidPredictionCounterfactualResultError
from noema.cognition.domain.prediction_counterfactual import (
    PredictionCounterfactualResult,
    PredictionCounterfactualStatus,
)
from noema.shared.domain import DomainError


def derived_result(**changes: object) -> PredictionCounterfactualResult:
    values: dict[str, object] = {
        "target_ref": "target-1",
        "status": PredictionCounterfactualStatus.DERIVED,
        "consequences": ("latency increases",),
    }
    values.update(changes)
    return PredictionCounterfactualResult(**values)


def insufficient_knowledge_result(**changes: object) -> PredictionCounterfactualResult:
    values: dict[str, object] = {
        "target_ref": "target-1",
        "status": PredictionCounterfactualStatus.INSUFFICIENT_KNOWLEDGE,
        "consequences": (),
    }
    values.update(changes)
    return PredictionCounterfactualResult(**values)


# ---------- PredictionCounterfactualStatus ----------


def test_prediction_counterfactual_status_has_exact_two_members() -> None:
    assert list(PredictionCounterfactualStatus) == [
        PredictionCounterfactualStatus.DERIVED,
        PredictionCounterfactualStatus.INSUFFICIENT_KNOWLEDGE,
    ]


def test_prediction_counterfactual_status_values() -> None:
    assert PredictionCounterfactualStatus.DERIVED.value == "derived"
    assert PredictionCounterfactualStatus.INSUFFICIENT_KNOWLEDGE.value == "insufficient_knowledge"


# ---------- PredictionCounterfactualResult: shape ----------


def test_prediction_counterfactual_result_has_exact_fields() -> None:
    assert tuple(field.name for field in fields(PredictionCounterfactualResult)) == (
        "target_ref",
        "status",
        "consequences",
    )


def test_prediction_counterfactual_result_has_exact_type_hints() -> None:
    hints = get_type_hints(PredictionCounterfactualResult)
    assert hints == {
        "target_ref": str,
        "status": PredictionCounterfactualStatus,
        "consequences": tuple[str, ...],
    }


def test_prediction_counterfactual_result_is_frozen_slotted_and_has_no_dict() -> None:
    result = derived_result()
    assert not hasattr(result, "__dict__")
    with pytest.raises(FrozenInstanceError):
        result.target_ref = "other"  # type: ignore[misc]


def test_prediction_counterfactual_result_constructor_is_keyword_only() -> None:
    with pytest.raises(TypeError):
        PredictionCounterfactualResult(  # type: ignore[misc]
            "target-1", PredictionCounterfactualStatus.DERIVED, ("latency increases",)
        )


def test_prediction_counterfactual_result_requires_every_field() -> None:
    with pytest.raises(TypeError):
        PredictionCounterfactualResult(  # type: ignore[call-arg]
            target_ref="target-1", status=PredictionCounterfactualStatus.DERIVED
        )


# ---------- happy paths ----------


def test_prediction_counterfactual_result_valid_derived_single_consequence() -> None:
    result = PredictionCounterfactualResult(
        target_ref="target-1",
        status=PredictionCounterfactualStatus.DERIVED,
        consequences=("latency increases",),
    )
    assert result.target_ref == "target-1"
    assert result.status is PredictionCounterfactualStatus.DERIVED
    assert result.consequences == ("latency increases",)


def test_prediction_counterfactual_result_valid_derived_multiple_consequences_preserves_order() -> (
    None
):
    result = derived_result(consequences=("latency increases", "throughput decreases"))
    assert result.consequences == ("latency increases", "throughput decreases")


def test_prediction_counterfactual_result_valid_insufficient_knowledge() -> None:
    result = PredictionCounterfactualResult(
        target_ref="target-1",
        status=PredictionCounterfactualStatus.INSUFFICIENT_KNOWLEDGE,
        consequences=(),
    )
    assert result.status is PredictionCounterfactualStatus.INSUFFICIENT_KNOWLEDGE
    assert result.consequences == ()


# ---------- target_ref validation ----------


@pytest.mark.parametrize("value", [None, 1, True, "", " ", "\t", "\n"])
def test_prediction_counterfactual_result_rejects_invalid_target_ref(value: object) -> None:
    with pytest.raises(InvalidPredictionCounterfactualResultError, match="target_ref"):
        derived_result(target_ref=value)


def test_prediction_counterfactual_result_preserves_target_ref_whitespace_exactly() -> None:
    padded = "  padded value  "
    result = derived_result(target_ref=padded)
    assert result.target_ref == padded


# ---------- status validation ----------


@pytest.mark.parametrize("value", [None, "derived", "DERIVED", 1, object()])
def test_prediction_counterfactual_result_rejects_invalid_status(value: object) -> None:
    with pytest.raises(InvalidPredictionCounterfactualResultError, match="status"):
        derived_result(status=value, consequences=())


# ---------- consequences container validation ----------


@pytest.mark.parametrize(
    "invalid_container",
    [["latency increases"], {"latency increases"}, frozenset({"latency increases"}), "x", None],
)
def test_prediction_counterfactual_result_rejects_non_tuple_consequences(
    invalid_container: object,
) -> None:
    with pytest.raises(
        InvalidPredictionCounterfactualResultError, match="consequences must be a tuple"
    ):
        derived_result(consequences=invalid_container)


# ---------- consequence item validation ----------


@pytest.mark.parametrize(
    "invalid_consequences",
    [
        (123,),
        (None,),
        ("latency increases", 123),
        ("",),
        ("   ",),
        ("\t",),
        ("latency increases", ""),
    ],
)
def test_prediction_counterfactual_result_rejects_invalid_consequence_items(
    invalid_consequences: tuple[object, ...],
) -> None:
    with pytest.raises(InvalidPredictionCounterfactualResultError):
        derived_result(consequences=invalid_consequences)


# ---------- duplicates ----------


def test_prediction_counterfactual_result_rejects_exact_duplicate_consequences() -> None:
    with pytest.raises(
        InvalidPredictionCounterfactualResultError, match="must not contain duplicates"
    ):
        derived_result(consequences=("latency increases", "latency increases"))


def test_prediction_counterfactual_result_does_not_normalize_whitespace_consequences() -> None:
    result = derived_result(consequences=("latency increases", " latency increases "))
    assert result.consequences == ("latency increases", " latency increases ")


# ---------- status/cardinality invariant ----------


def test_prediction_counterfactual_result_rejects_derived_with_empty_consequences() -> None:
    with pytest.raises(InvalidPredictionCounterfactualResultError, match="inconsistent"):
        PredictionCounterfactualResult(
            target_ref="target-1",
            status=PredictionCounterfactualStatus.DERIVED,
            consequences=(),
        )


def test_prediction_counterfactual_result_rejects_insufficient_knowledge_with_consequences() -> (
    None
):
    with pytest.raises(InvalidPredictionCounterfactualResultError, match="inconsistent"):
        PredictionCounterfactualResult(
            target_ref="target-1",
            status=PredictionCounterfactualStatus.INSUFFICIENT_KNOWLEDGE,
            consequences=("latency increases",),
        )


# ---------- order preservation ----------


def test_prediction_counterfactual_result_preserves_caller_provided_order() -> None:
    result = derived_result(consequences=("second effect", "first effect"))
    assert result.consequences == ("second effect", "first effect")


# ---------- equality / hashing ----------


def test_prediction_counterfactual_result_is_hashable() -> None:
    hash(derived_result())
    hash(insufficient_knowledge_result())


def test_prediction_counterfactual_result_structural_equality() -> None:
    first = derived_result()
    second = derived_result()
    assert first == second
    assert hash(first) == hash(second)


def test_prediction_counterfactual_result_structural_equality_is_order_sensitive() -> None:
    forward = derived_result(consequences=("A", "B"))
    backward = derived_result(consequences=("B", "A"))
    assert forward != backward


# ---------- errors ----------


def test_invalid_prediction_counterfactual_result_error_inherits_directly_from_domain_error() -> (
    None
):
    assert InvalidPredictionCounterfactualResultError.__bases__ == (DomainError,)


# ---------- public surface ----------


def test_prediction_counterfactual_package_exports_result_and_status() -> None:
    from noema.cognition.domain import prediction_counterfactual

    assert "PredictionCounterfactualResult" in prediction_counterfactual.__all__
    assert "PredictionCounterfactualStatus" in prediction_counterfactual.__all__
