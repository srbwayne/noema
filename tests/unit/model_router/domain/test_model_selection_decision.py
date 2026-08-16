from dataclasses import MISSING, FrozenInstanceError, fields

import pytest

from noema.model_router.domain import (
    InvalidModelSelectionDecisionError,
    ModelCapability,
    ModelResource,
    ModelResourceCapabilities,
    ModelSelectionDecision,
)


def resource(**changes: object) -> ModelResource:
    values: dict[str, object] = {
        "resource_ref": "resource:primary",
        "provider_ref": "provider:test",
        "model_ref": "model:test-v1",
    }
    values.update(changes)
    return ModelResource(**values)


def test_model_selection_decision_has_exact_required_field() -> None:
    contract_fields = fields(ModelSelectionDecision)
    assert tuple(field.name for field in contract_fields) == ("selected_resource",)
    assert all(
        field.default is MISSING and field.default_factory is MISSING for field in contract_fields
    )


def test_model_selection_decision_does_not_expose_forward_looking_fields() -> None:
    field_names = {field.name for field in fields(ModelSelectionDecision)}
    forbidden = {
        "status",
        "state",
        "outcome",
        "reason",
        "selection_reason",
        "reason_code",
        "rationale",
        "explanation",
        "request",
        "requirements",
        "candidates",
        "selected_candidate",
    }
    assert field_names.isdisjoint(forbidden)


def test_model_selection_decision_does_not_expose_behavior_methods() -> None:
    forbidden_methods = {
        "route",
        "select",
        "rank",
        "score",
        "retry",
        "fallback",
        "matches",
        "validate_request",
        "correlate",
    }
    public_members = {name for name in vars(ModelSelectionDecision) if not name.startswith("_")}
    assert public_members.isdisjoint(forbidden_methods)


def test_model_selection_decision_is_frozen_slotted_and_has_no_dict() -> None:
    decision = ModelSelectionDecision(selected_resource=resource())
    assert not hasattr(decision, "__dict__")
    with pytest.raises(FrozenInstanceError):
        decision.selected_resource = resource()  # type: ignore[misc]


def test_model_selection_decision_constructor_is_keyword_only() -> None:
    with pytest.raises(TypeError):
        ModelSelectionDecision(resource())  # type: ignore[misc]


def test_model_selection_decision_accepts_valid_resource() -> None:
    the_resource = resource()
    decision = ModelSelectionDecision(selected_resource=the_resource)
    assert decision.selected_resource is the_resource


@pytest.mark.parametrize(
    "invalid_resource",
    [None, "resource", {}, object()],
)
def test_model_selection_decision_rejects_non_model_resource(
    invalid_resource: object,
) -> None:
    with pytest.raises(InvalidModelSelectionDecisionError, match="selected_resource"):
        ModelSelectionDecision(selected_resource=invalid_resource)  # type: ignore[arg-type]


def test_model_selection_decision_rejects_model_resource_capabilities() -> None:
    profile = ModelResourceCapabilities(
        resource=resource(), capabilities=frozenset({ModelCapability.TEXT_GENERATION})
    )
    with pytest.raises(InvalidModelSelectionDecisionError, match="selected_resource"):
        ModelSelectionDecision(selected_resource=profile)  # type: ignore[arg-type]


def test_model_selection_decision_does_not_accept_none() -> None:
    with pytest.raises(InvalidModelSelectionDecisionError):
        ModelSelectionDecision(selected_resource=None)  # type: ignore[arg-type]


def test_model_selection_decision_structural_equality_and_hashability() -> None:
    first = ModelSelectionDecision(selected_resource=resource())
    second = ModelSelectionDecision(selected_resource=resource())
    assert first == second
    assert hash(first) == hash(second)


def test_model_selection_decision_differs_when_resource_differs() -> None:
    first = ModelSelectionDecision(selected_resource=resource())
    second = ModelSelectionDecision(selected_resource=resource(resource_ref="resource:secondary"))
    assert first != second


def test_invalid_model_selection_request_and_decision_error_hierarchy() -> None:
    from noema.model_router.domain import InvalidModelSelectionRequestError
    from noema.shared.domain import DomainError

    assert InvalidModelSelectionRequestError.__bases__ == (DomainError,)
    assert InvalidModelSelectionDecisionError.__bases__ == (DomainError,)


def test_existing_model_router_contracts_remain_intact() -> None:
    from noema.model_router.domain import ModelCapabilityRequirements

    assert tuple(field.name for field in fields(ModelResource)) == (
        "resource_ref",
        "provider_ref",
        "model_ref",
    )
    assert tuple(field.name for field in fields(ModelResourceCapabilities)) == (
        "resource",
        "capabilities",
    )
    assert tuple(field.name for field in fields(ModelCapabilityRequirements)) == (
        "required_capabilities",
    )
    assert {member.name for member in ModelCapability} == {
        "TEXT_GENERATION",
        "STRUCTURED_OUTPUT",
        "TOOL_CALLING",
    }
