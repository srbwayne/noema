from dataclasses import FrozenInstanceError, fields
from typing import get_type_hints

import pytest

from noema.cognition.domain.errors import (
    InvalidCounterfactualRequestError,
    InvalidPredictionRequestError,
)
from noema.cognition.domain.prediction_counterfactual import (
    CounterfactualRequest,
    PredictionRequest,
)
from noema.shared.domain import DomainError


def prediction_request(**changes: object) -> PredictionRequest:
    values: dict[str, object] = {
        "baseline_ref": "baseline-1",
        "target_ref": "target-1",
        "target_statement": "what happens to latency?",
    }
    values.update(changes)
    return PredictionRequest(**values)


def counterfactual_request(**changes: object) -> CounterfactualRequest:
    values: dict[str, object] = {
        "baseline_ref": "baseline-1",
        "target_ref": "target-1",
        "target_statement": "what happens to latency?",
        "divergence_refs": ("divergence-2", "divergence-1"),
    }
    values.update(changes)
    return CounterfactualRequest(**values)


# ---------- PredictionRequest ----------


def test_prediction_request_happy_path_preserves_fields_exactly() -> None:
    request = PredictionRequest(
        baseline_ref="baseline-1",
        target_ref="target-1",
        target_statement="what happens to latency?",
    )
    assert request.baseline_ref == "baseline-1"
    assert request.target_ref == "target-1"
    assert request.target_statement == "what happens to latency?"


def test_prediction_request_has_exact_fields() -> None:
    assert tuple(field.name for field in fields(PredictionRequest)) == (
        "baseline_ref",
        "target_ref",
        "target_statement",
    )


def test_prediction_request_has_exact_type_hints() -> None:
    hints = get_type_hints(PredictionRequest)
    assert hints == {
        "baseline_ref": str,
        "target_ref": str,
        "target_statement": str,
    }


def test_prediction_request_is_frozen_slotted_and_has_no_dict() -> None:
    request = prediction_request()
    assert not hasattr(request, "__dict__")
    with pytest.raises(FrozenInstanceError):
        request.baseline_ref = "other"  # type: ignore[misc]


def test_prediction_request_constructor_is_keyword_only() -> None:
    with pytest.raises(TypeError):
        PredictionRequest("baseline-1", "target-1", "what happens to latency?")  # type: ignore[misc]


def test_prediction_request_requires_every_field() -> None:
    with pytest.raises(TypeError):
        PredictionRequest(baseline_ref="baseline-1", target_ref="target-1")  # type: ignore[call-arg]


@pytest.mark.parametrize("field_name", ["baseline_ref", "target_ref", "target_statement"])
@pytest.mark.parametrize("value", [None, 1, True, "", " ", "\t", "\n"])
def test_prediction_request_rejects_invalid_strings(field_name: str, value: object) -> None:
    with pytest.raises(InvalidPredictionRequestError, match=field_name):
        prediction_request(**{field_name: value})


@pytest.mark.parametrize("field_name", ["baseline_ref", "target_ref", "target_statement"])
def test_prediction_request_preserves_string_whitespace_exactly(field_name: str) -> None:
    padded = "  padded value  "
    request = prediction_request(**{field_name: padded})
    assert getattr(request, field_name) == padded


def test_prediction_request_is_hashable() -> None:
    hash(prediction_request())


def test_prediction_request_structural_equality() -> None:
    first = prediction_request()
    second = prediction_request()
    assert first == second
    assert hash(first) == hash(second)


# ---------- CounterfactualRequest ----------


def test_counterfactual_request_happy_path_preserves_caller_order() -> None:
    request = CounterfactualRequest(
        baseline_ref="baseline-1",
        target_ref="target-1",
        target_statement="what happens to latency?",
        divergence_refs=("divergence-2", "divergence-1"),
    )
    assert request.baseline_ref == "baseline-1"
    assert request.target_ref == "target-1"
    assert request.target_statement == "what happens to latency?"
    assert request.divergence_refs == ("divergence-2", "divergence-1")


def test_counterfactual_request_has_exact_fields() -> None:
    assert tuple(field.name for field in fields(CounterfactualRequest)) == (
        "baseline_ref",
        "target_ref",
        "target_statement",
        "divergence_refs",
    )


def test_counterfactual_request_has_exact_type_hints() -> None:
    hints = get_type_hints(CounterfactualRequest)
    assert hints == {
        "baseline_ref": str,
        "target_ref": str,
        "target_statement": str,
        "divergence_refs": tuple[str, ...],
    }


def test_counterfactual_request_is_frozen_slotted_and_has_no_dict() -> None:
    request = counterfactual_request()
    assert not hasattr(request, "__dict__")
    with pytest.raises(FrozenInstanceError):
        request.baseline_ref = "other"  # type: ignore[misc]


def test_counterfactual_request_constructor_is_keyword_only() -> None:
    with pytest.raises(TypeError):
        CounterfactualRequest(  # type: ignore[misc]
            "baseline-1", "target-1", "what happens to latency?", ("divergence-1",)
        )


def test_counterfactual_request_requires_divergence_refs() -> None:
    with pytest.raises(TypeError):
        CounterfactualRequest(  # type: ignore[call-arg]
            baseline_ref="baseline-1",
            target_ref="target-1",
            target_statement="what happens to latency?",
        )


@pytest.mark.parametrize("field_name", ["baseline_ref", "target_ref", "target_statement"])
@pytest.mark.parametrize("value", [None, 1, True, "", " ", "\t", "\n"])
def test_counterfactual_request_rejects_invalid_common_strings(
    field_name: str, value: object
) -> None:
    with pytest.raises(InvalidCounterfactualRequestError, match=field_name):
        counterfactual_request(**{field_name: value})


@pytest.mark.parametrize("field_name", ["baseline_ref", "target_ref", "target_statement"])
def test_counterfactual_request_preserves_common_string_whitespace_exactly(
    field_name: str,
) -> None:
    padded = "  padded value  "
    request = counterfactual_request(**{field_name: padded})
    assert getattr(request, field_name) == padded


@pytest.mark.parametrize(
    "invalid_container", [[], set(), frozenset(), None, "divergence-1", (x for x in ())]
)
def test_counterfactual_request_rejects_non_tuple_divergence_refs(
    invalid_container: object,
) -> None:
    with pytest.raises(InvalidCounterfactualRequestError, match="divergence_refs must be a tuple"):
        counterfactual_request(divergence_refs=invalid_container)


def test_counterfactual_request_rejects_empty_divergence_refs() -> None:
    with pytest.raises(
        InvalidCounterfactualRequestError,
        match="divergence_refs must contain at least one reference",
    ):
        counterfactual_request(divergence_refs=())


@pytest.mark.parametrize(
    "invalid_refs",
    [
        ("",),
        ("   ",),
        ("divergence-1", ""),
        ("divergence-1", 123),
        ("divergence-1", None),
    ],
)
def test_counterfactual_request_rejects_invalid_divergence_items(
    invalid_refs: tuple[object, ...],
) -> None:
    with pytest.raises(InvalidCounterfactualRequestError):
        counterfactual_request(divergence_refs=invalid_refs)


def test_counterfactual_request_rejects_duplicate_divergence_refs() -> None:
    with pytest.raises(
        InvalidCounterfactualRequestError, match="divergence_refs must not contain duplicates"
    ):
        counterfactual_request(divergence_refs=("D1", "D1"))


def test_counterfactual_request_does_not_normalize_equivalent_whitespace_refs() -> None:
    request = counterfactual_request(divergence_refs=("D1", " D1 "))
    assert request.divergence_refs == ("D1", " D1 ")


def test_counterfactual_request_preserves_caller_provided_order() -> None:
    request = counterfactual_request(divergence_refs=("D2", "D1"))
    assert request.divergence_refs == ("D2", "D1")


def test_counterfactual_request_accepts_single_divergence() -> None:
    request = counterfactual_request(divergence_refs=("D1",))
    assert request.divergence_refs == ("D1",)


def test_counterfactual_request_is_hashable() -> None:
    hash(counterfactual_request())


def test_counterfactual_request_structural_equality_is_order_sensitive() -> None:
    forward = counterfactual_request(divergence_refs=("D1", "D2"))
    backward = counterfactual_request(divergence_refs=("D2", "D1"))
    assert forward != backward


def test_counterfactual_request_structural_equality_for_identical_order() -> None:
    first = counterfactual_request(divergence_refs=("D1", "D2"))
    second = counterfactual_request(divergence_refs=("D1", "D2"))
    assert first == second
    assert hash(first) == hash(second)


# ---------- errors ----------


@pytest.mark.parametrize(
    "error_type",
    [InvalidPredictionRequestError, InvalidCounterfactualRequestError],
)
def test_prediction_counterfactual_errors_inherit_directly_from_domain_error(
    error_type: type[DomainError],
) -> None:
    assert error_type.__bases__ == (DomainError,)


# ---------- public surface ----------


def test_prediction_counterfactual_package_exports_expected_public_surface() -> None:
    from noema.cognition.domain import prediction_counterfactual

    assert prediction_counterfactual.__all__ == [
        "CounterfactualRequest",
        "PredictionCounterfactualResult",
        "PredictionCounterfactualStatus",
        "PredictionRequest",
    ]


def test_prediction_counterfactual_package_does_not_export_forward_looking_names() -> None:
    from noema.cognition.domain import prediction_counterfactual

    forbidden = {
        "DerivationTarget",
        "Scenario",
        "Baseline",
        "Divergence",
        "Intervention",
        "PredictionResult",
        "CounterfactualResult",
        "PredictionOutcome",
        "CounterfactualOutcome",
        "Consequence",
        "PossibleConsequence",
        "PredictionMode",
        "CounterfactualMode",
        "DerivationKind",
        "BaseDerivationRequest",
        "PredictionExecutor",
        "CounterfactualExecutor",
        "PredictionEngine",
        "CounterfactualEngine",
    }
    public_members = {name for name in vars(prediction_counterfactual) if not name.startswith("_")}
    assert public_members.isdisjoint(forbidden)
