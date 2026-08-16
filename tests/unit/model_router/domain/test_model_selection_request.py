from dataclasses import MISSING, FrozenInstanceError, fields

import pytest

from noema.model_router.domain import (
    InvalidModelSelectionRequestError,
    ModelCapability,
    ModelCapabilityRequirements,
    ModelResource,
    ModelResourceCapabilities,
    ModelSelectionRequest,
)


def resource(**changes: object) -> ModelResource:
    values: dict[str, object] = {
        "resource_ref": "resource:primary",
        "provider_ref": "provider:test",
        "model_ref": "model:test-v1",
    }
    values.update(changes)
    return ModelResource(**values)


def candidate(**changes: object) -> ModelResourceCapabilities:
    values: dict[str, object] = {
        "resource": resource(),
        "capabilities": frozenset({ModelCapability.TEXT_GENERATION}),
    }
    values.update(changes)
    return ModelResourceCapabilities(**values)


def requirements(**changes: object) -> ModelCapabilityRequirements:
    values: dict[str, object] = {"required_capabilities": frozenset()}
    values.update(changes)
    return ModelCapabilityRequirements(**values)


def test_model_selection_request_has_exact_required_fields_in_order() -> None:
    contract_fields = fields(ModelSelectionRequest)
    assert tuple(field.name for field in contract_fields) == ("requirements", "candidates")
    assert all(
        field.default is MISSING and field.default_factory is MISSING for field in contract_fields
    )


def test_model_selection_request_does_not_expose_forward_looking_fields() -> None:
    field_names = {field.name for field in fields(ModelSelectionRequest)}
    forbidden = {
        "preferred_capabilities",
        "selected_resource",
        "status",
        "reason",
        "ranking",
        "score",
        "policy",
        "registry",
        "available_resources",
    }
    assert field_names.isdisjoint(forbidden)


def test_model_selection_request_does_not_expose_behavior_methods() -> None:
    forbidden_methods = {
        "match",
        "matches",
        "filter",
        "select",
        "route",
        "rank",
        "score",
        "choose",
        "best",
        "eligible",
    }
    public_members = {name for name in vars(ModelSelectionRequest) if not name.startswith("_")}
    assert public_members.isdisjoint(forbidden_methods)


def test_model_selection_request_is_frozen_slotted_and_has_no_dict() -> None:
    request = ModelSelectionRequest(requirements=requirements(), candidates=frozenset())
    assert not hasattr(request, "__dict__")
    with pytest.raises(FrozenInstanceError):
        request.candidates = frozenset()  # type: ignore[misc]


def test_model_selection_request_constructor_is_keyword_only() -> None:
    with pytest.raises(TypeError):
        ModelSelectionRequest(requirements(), frozenset())  # type: ignore[misc]


def test_model_selection_request_accepts_valid_candidates() -> None:
    candidate_a = candidate()
    candidate_b = candidate(resource=resource(resource_ref="resource:secondary"))
    the_requirements = requirements()
    request = ModelSelectionRequest(
        requirements=the_requirements,
        candidates=frozenset({candidate_a, candidate_b}),
    )
    assert request.requirements is the_requirements
    assert request.candidates == frozenset({candidate_a, candidate_b})


def test_model_selection_request_accepts_empty_candidates() -> None:
    request = ModelSelectionRequest(requirements=requirements(), candidates=frozenset())
    assert request.candidates == frozenset()


def test_model_selection_request_accepts_empty_requirements() -> None:
    request = ModelSelectionRequest(
        requirements=requirements(required_capabilities=frozenset()),
        candidates=frozenset(),
    )
    assert request.requirements.required_capabilities == frozenset()


@pytest.mark.parametrize(
    "invalid_requirements",
    [None, frozenset(), {}, object()],
)
def test_model_selection_request_rejects_non_requirements(
    invalid_requirements: object,
) -> None:
    with pytest.raises(InvalidModelSelectionRequestError, match="requirements"):
        ModelSelectionRequest(requirements=invalid_requirements, candidates=frozenset())  # type: ignore[arg-type]


def test_model_selection_request_rejects_model_resource_as_requirements() -> None:
    with pytest.raises(InvalidModelSelectionRequestError, match="requirements"):
        ModelSelectionRequest(requirements=resource(), candidates=frozenset())  # type: ignore[arg-type]


def test_model_selection_request_rejects_model_resource_capabilities_as_requirements() -> None:
    with pytest.raises(InvalidModelSelectionRequestError, match="requirements"):
        ModelSelectionRequest(requirements=candidate(), candidates=frozenset())  # type: ignore[arg-type]


@pytest.mark.parametrize("invalid_container", [None, [], (), set(), {}, ""])
def test_model_selection_request_rejects_non_frozenset_candidates(
    invalid_container: object,
) -> None:
    with pytest.raises(InvalidModelSelectionRequestError, match="frozenset"):
        ModelSelectionRequest(requirements=requirements(), candidates=invalid_container)  # type: ignore[arg-type]


@pytest.mark.parametrize("invalid_item", ["resource", None, object()])
def test_model_selection_request_rejects_non_capabilities_candidate_items(
    invalid_item: object,
) -> None:
    with pytest.raises(InvalidModelSelectionRequestError, match="ModelResourceCapabilities"):
        ModelSelectionRequest(requirements=requirements(), candidates=frozenset((invalid_item,)))


def test_model_selection_request_rejects_model_resource_as_candidate_item() -> None:
    with pytest.raises(InvalidModelSelectionRequestError, match="ModelResourceCapabilities"):
        ModelSelectionRequest(requirements=requirements(), candidates=frozenset((resource(),)))


def test_model_selection_request_equality_is_unordered() -> None:
    candidate_a = candidate()
    candidate_b = candidate(resource=resource(resource_ref="resource:secondary"))
    the_requirements = requirements()
    first = ModelSelectionRequest(
        requirements=the_requirements,
        candidates=frozenset((candidate_a, candidate_b)),
    )
    second = ModelSelectionRequest(
        requirements=the_requirements,
        candidates=frozenset((candidate_b, candidate_a)),
    )
    assert first == second
    assert hash(first) == hash(second)
