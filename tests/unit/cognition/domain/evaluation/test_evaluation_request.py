from dataclasses import FrozenInstanceError, fields
from typing import get_type_hints

import pytest

from noema.cognition.domain.errors import InvalidEvaluationRequestError
from noema.cognition.domain.evaluation import EvaluationRequest
from noema.shared.domain import DomainError


def evaluation_request(**changes: object) -> EvaluationRequest:
    values: dict[str, object] = {
        "target_ref": "target-1",
        "consequence": "latency decreases",
        "normative_statement": "prefer lower latency",
    }
    values.update(changes)
    return EvaluationRequest(**values)


# ---------- EvaluationRequest ----------


def test_evaluation_request_happy_path_preserves_fields_exactly() -> None:
    request = EvaluationRequest(
        target_ref="target-1",
        consequence="latency decreases",
        normative_statement="prefer lower latency",
    )
    assert request.target_ref == "target-1"
    assert request.consequence == "latency decreases"
    assert request.normative_statement == "prefer lower latency"


def test_evaluation_request_has_exact_fields() -> None:
    assert tuple(field.name for field in fields(EvaluationRequest)) == (
        "target_ref",
        "consequence",
        "normative_statement",
    )


def test_evaluation_request_has_exact_type_hints() -> None:
    hints = get_type_hints(EvaluationRequest)
    assert hints == {
        "target_ref": str,
        "consequence": str,
        "normative_statement": str,
    }


def test_evaluation_request_is_frozen_slotted_and_has_no_dict() -> None:
    request = evaluation_request()
    assert not hasattr(request, "__dict__")
    with pytest.raises(FrozenInstanceError):
        request.target_ref = "other"  # type: ignore[misc]


def test_evaluation_request_constructor_is_keyword_only() -> None:
    with pytest.raises(TypeError):
        EvaluationRequest("target-1", "latency decreases", "prefer lower latency")  # type: ignore[misc]


@pytest.mark.parametrize(
    "missing_field",
    ["target_ref", "consequence", "normative_statement"],
)
def test_evaluation_request_requires_every_field(missing_field: str) -> None:
    values: dict[str, object] = {
        "target_ref": "target-1",
        "consequence": "latency decreases",
        "normative_statement": "prefer lower latency",
    }
    del values[missing_field]
    with pytest.raises(TypeError):
        EvaluationRequest(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize("field_name", ["target_ref", "consequence", "normative_statement"])
@pytest.mark.parametrize("value", [None, 1, True, "", " ", "\t", "\n"])
def test_evaluation_request_rejects_invalid_strings(field_name: str, value: object) -> None:
    with pytest.raises(InvalidEvaluationRequestError, match=field_name):
        evaluation_request(**{field_name: value})


@pytest.mark.parametrize("field_name", ["target_ref", "consequence", "normative_statement"])
def test_evaluation_request_preserves_string_whitespace_exactly(field_name: str) -> None:
    padded = "  padded value  "
    request = evaluation_request(**{field_name: padded})
    assert getattr(request, field_name) == padded


def test_evaluation_request_is_hashable() -> None:
    hash(evaluation_request())


def test_evaluation_request_structural_equality() -> None:
    first = evaluation_request()
    second = evaluation_request()
    assert first == second
    assert hash(first) == hash(second)


@pytest.mark.parametrize(
    ("field_name", "other_value"),
    [
        ("target_ref", "target-2"),
        ("consequence", "latency increases"),
        ("normative_statement", "prefer higher throughput"),
    ],
)
def test_evaluation_request_structural_inequality(field_name: str, other_value: str) -> None:
    first = evaluation_request()
    second = evaluation_request(**{field_name: other_value})
    assert first != second


# ---------- errors ----------


def test_invalid_evaluation_request_error_inherits_directly_from_domain_error() -> None:
    assert InvalidEvaluationRequestError.__bases__ == (DomainError,)


def test_invalid_evaluation_request_error_is_exported_from_errors_package() -> None:
    from noema.cognition.domain import errors

    assert "InvalidEvaluationRequestError" in errors.__all__
    assert errors.InvalidEvaluationRequestError is InvalidEvaluationRequestError


# ---------- public surface ----------


def test_evaluation_package_exports_expected_public_surface() -> None:
    from noema.cognition.domain import evaluation

    assert evaluation.__all__ == ["EvaluationRequest"]


def test_evaluation_package_does_not_export_forward_looking_names() -> None:
    from noema.cognition.domain import evaluation

    forbidden = {
        "EvaluationResult",
        "EvaluationOutcome",
        "EvaluationStatus",
        "Utility",
        "UtilityValue",
        "UtilityJudgment",
        "EvaluationExecutor",
        "EvaluationPort",
        "Evaluator",
        "EvaluationEngine",
        "EvaluationPolicy",
        "EvaluationCriterion",
        "NormativeFrame",
        "EvaluationFrame",
        "EvaluationSubject",
        "ConsequenceSubject",
        "EvaluatedConsequence",
    }
    public_members = {name for name in vars(evaluation) if not name.startswith("_")}
    assert public_members.isdisjoint(forbidden)
