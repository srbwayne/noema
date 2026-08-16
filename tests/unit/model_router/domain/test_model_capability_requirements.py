from dataclasses import MISSING, FrozenInstanceError, fields

import pytest

from noema.model_router.domain import (
    InvalidModelCapabilityRequirementsError,
    ModelCapability,
    ModelCapabilityRequirements,
    ModelResource,
    ModelResourceCapabilities,
)
from noema.shared.domain import DomainError


def test_model_capability_requirements_has_exact_required_field() -> None:
    contract_fields = fields(ModelCapabilityRequirements)
    assert tuple(field.name for field in contract_fields) == ("required_capabilities",)
    assert all(
        field.default is MISSING and field.default_factory is MISSING for field in contract_fields
    )


def test_model_capability_requirements_does_not_expose_forward_looking_fields() -> None:
    field_names = {field.name for field in fields(ModelCapabilityRequirements)}
    forbidden = {
        "preferred_capabilities",
        "optional_capabilities",
        "excluded_capabilities",
        "forbidden_capabilities",
        "resource",
        "resource_ref",
        "provider_ref",
        "model_ref",
        "candidates",
        "availability",
        "score",
        "rank",
        "priority",
        "cost",
        "privacy",
    }
    assert field_names.isdisjoint(forbidden)


def test_model_capability_requirements_does_not_expose_matching_or_routing_methods() -> None:
    forbidden_methods = {
        "matches",
        "match",
        "is_satisfied_by",
        "satisfied_by",
        "is_compatible_with",
        "compatible_with",
        "supports",
        "supports_all",
        "supports_any",
        "accepts",
        "filter",
        "select",
        "route",
        "rank",
        "score",
        "choose",
        "best",
    }
    public_members = {
        name for name in vars(ModelCapabilityRequirements) if not name.startswith("_")
    }
    assert public_members.isdisjoint(forbidden_methods)


def test_model_capability_requirements_is_frozen_slotted_and_has_no_dict() -> None:
    requirements = ModelCapabilityRequirements(required_capabilities=frozenset())
    assert not hasattr(requirements, "__dict__")
    with pytest.raises(FrozenInstanceError):
        requirements.required_capabilities = frozenset()  # type: ignore[misc]


def test_model_capability_requirements_constructor_is_keyword_only() -> None:
    with pytest.raises(TypeError):
        ModelCapabilityRequirements(frozenset())  # type: ignore[misc]


def test_model_capability_requirements_accepts_valid_nonempty_set() -> None:
    capabilities = frozenset({ModelCapability.TEXT_GENERATION, ModelCapability.STRUCTURED_OUTPUT})
    requirements = ModelCapabilityRequirements(required_capabilities=capabilities)
    assert requirements.required_capabilities == capabilities


def test_model_capability_requirements_accepts_empty_frozenset_without_inference() -> None:
    requirements = ModelCapabilityRequirements(required_capabilities=frozenset())
    assert requirements.required_capabilities == frozenset()
    assert ModelCapability.TEXT_GENERATION not in requirements.required_capabilities


@pytest.mark.parametrize("invalid_container", [None, [], (), set(), {}, ""])
def test_model_capability_requirements_rejects_non_frozenset_container(
    invalid_container: object,
) -> None:
    with pytest.raises(InvalidModelCapabilityRequirementsError, match="frozenset"):
        ModelCapabilityRequirements(required_capabilities=invalid_container)  # type: ignore[arg-type]


@pytest.mark.parametrize("invalid_item", ["text_generation", "tool_calling", None, 1, object()])
def test_model_capability_requirements_rejects_non_capability_items(
    invalid_item: object,
) -> None:
    with pytest.raises(InvalidModelCapabilityRequirementsError, match="ModelCapability"):
        ModelCapabilityRequirements(required_capabilities=frozenset((invalid_item,)))


def test_model_capability_requirements_equality_is_unordered() -> None:
    first = ModelCapabilityRequirements(
        required_capabilities=frozenset(
            (ModelCapability.TEXT_GENERATION, ModelCapability.TOOL_CALLING)
        )
    )
    second = ModelCapabilityRequirements(
        required_capabilities=frozenset(
            (ModelCapability.TOOL_CALLING, ModelCapability.TEXT_GENERATION)
        )
    )
    assert first == second
    assert hash(first) == hash(second)


def test_model_capability_requirements_differs_when_sets_differ() -> None:
    first = ModelCapabilityRequirements(
        required_capabilities=frozenset((ModelCapability.TEXT_GENERATION,))
    )
    second = ModelCapabilityRequirements(
        required_capabilities=frozenset((ModelCapability.TOOL_CALLING,))
    )
    assert first != second


def test_invalid_model_capability_requirements_error_inherits_directly_from_domain_error() -> None:
    assert InvalidModelCapabilityRequirementsError.__bases__ == (DomainError,)


def test_existing_model_router_contracts_remain_intact() -> None:
    assert tuple(field.name for field in fields(ModelResource)) == (
        "resource_ref",
        "provider_ref",
        "model_ref",
    )
    assert tuple(field.name for field in fields(ModelResourceCapabilities)) == (
        "resource",
        "capabilities",
    )
    assert {member.name for member in ModelCapability} == {
        "TEXT_GENERATION",
        "STRUCTURED_OUTPUT",
        "TOOL_CALLING",
    }
