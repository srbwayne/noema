from dataclasses import MISSING, FrozenInstanceError, fields

import pytest

from noema.model_router.domain import (
    InvalidModelResourceCapabilitiesError,
    ModelCapability,
    ModelResource,
    ModelResourceCapabilities,
)
from noema.shared.domain import DomainError


def resource(**changes: object) -> ModelResource:
    values: dict[str, object] = {
        "resource_ref": "resource:primary",
        "provider_ref": "provider:test",
        "model_ref": "model:test-v1",
    }
    values.update(changes)
    return ModelResource(**values)


def test_model_resource_capabilities_has_exact_required_fields_in_order() -> None:
    contract_fields = fields(ModelResourceCapabilities)
    assert tuple(field.name for field in contract_fields) == ("resource", "capabilities")
    assert all(
        field.default is MISSING and field.default_factory is MISSING for field in contract_fields
    )


def test_model_resource_capabilities_does_not_expose_forward_looking_fields() -> None:
    field_names = {field.name for field in fields(ModelResourceCapabilities)}
    forbidden = {
        "required_capabilities",
        "preferred_capabilities",
        "availability",
        "status",
        "score",
        "rank",
        "priority",
        "cost",
        "latency",
        "privacy",
        "context_window",
        "temperature",
        "endpoint",
        "provider",
    }
    assert field_names.isdisjoint(forbidden)


def test_model_resource_capabilities_does_not_expose_routing_or_matching_methods() -> None:
    forbidden_methods = {
        "supports",
        "supports_all",
        "supports_any",
        "has_capability",
        "has_all",
        "contains",
        "match",
        "matches",
        "score",
        "rank",
        "route",
        "select",
        "choose",
        "best",
        "prefer",
        "filter",
        "invoke",
        "execute",
        "generate",
    }
    public_members = {name for name in vars(ModelResourceCapabilities) if not name.startswith("_")}
    assert public_members.isdisjoint(forbidden_methods)


def test_model_resource_capabilities_is_frozen_slotted_and_has_no_dict() -> None:
    profile = ModelResourceCapabilities(resource=resource(), capabilities=frozenset())
    assert not hasattr(profile, "__dict__")
    with pytest.raises(FrozenInstanceError):
        profile.capabilities = frozenset()  # type: ignore[misc]


def test_model_resource_capabilities_constructor_is_keyword_only() -> None:
    with pytest.raises(TypeError):
        ModelResourceCapabilities(resource(), frozenset())  # type: ignore[misc]


def test_model_resource_capabilities_accepts_valid_nonempty_capabilities() -> None:
    the_resource = resource()
    capabilities = frozenset({ModelCapability.TEXT_GENERATION, ModelCapability.STRUCTURED_OUTPUT})
    profile = ModelResourceCapabilities(resource=the_resource, capabilities=capabilities)
    assert profile.resource is the_resource
    assert profile.capabilities == capabilities


def test_model_resource_capabilities_accepts_empty_frozenset_without_inference() -> None:
    profile = ModelResourceCapabilities(resource=resource(), capabilities=frozenset())
    assert profile.capabilities == frozenset()
    assert ModelCapability.TEXT_GENERATION not in profile.capabilities


@pytest.mark.parametrize("invalid_resource", [None, "resource:primary", {}, (), object()])
def test_model_resource_capabilities_rejects_non_model_resource(
    invalid_resource: object,
) -> None:
    with pytest.raises(InvalidModelResourceCapabilitiesError, match="resource"):
        ModelResourceCapabilities(resource=invalid_resource, capabilities=frozenset())  # type: ignore[arg-type]


@pytest.mark.parametrize("invalid_container", [None, [], (), set(), {}, ""])
def test_model_resource_capabilities_rejects_non_frozenset_container(
    invalid_container: object,
) -> None:
    with pytest.raises(InvalidModelResourceCapabilitiesError, match="frozenset"):
        ModelResourceCapabilities(resource=resource(), capabilities=invalid_container)  # type: ignore[arg-type]


@pytest.mark.parametrize("invalid_item", ["text_generation", None, 1, object()])
def test_model_resource_capabilities_rejects_non_capability_items(
    invalid_item: object,
) -> None:
    with pytest.raises(InvalidModelResourceCapabilitiesError, match="ModelCapability"):
        ModelResourceCapabilities(resource=resource(), capabilities=frozenset((invalid_item,)))


def test_model_resource_capabilities_equality_is_unordered() -> None:
    the_resource = resource()
    first = ModelResourceCapabilities(
        resource=the_resource,
        capabilities=frozenset((ModelCapability.TEXT_GENERATION, ModelCapability.TOOL_CALLING)),
    )
    second = ModelResourceCapabilities(
        resource=the_resource,
        capabilities=frozenset((ModelCapability.TOOL_CALLING, ModelCapability.TEXT_GENERATION)),
    )
    assert first == second
    assert hash(first) == hash(second)


def test_model_resource_capabilities_differs_when_capability_sets_differ() -> None:
    the_resource = resource()
    first = ModelResourceCapabilities(
        resource=the_resource, capabilities=frozenset((ModelCapability.TEXT_GENERATION,))
    )
    second = ModelResourceCapabilities(
        resource=the_resource, capabilities=frozenset((ModelCapability.TOOL_CALLING,))
    )
    assert first != second


def test_model_resource_is_intact_with_exactly_its_three_fields() -> None:
    resource_fields = fields(ModelResource)
    assert tuple(field.name for field in resource_fields) == (
        "resource_ref",
        "provider_ref",
        "model_ref",
    )


def test_invalid_model_resource_capabilities_error_inherits_directly_from_domain_error() -> None:
    assert InvalidModelResourceCapabilitiesError.__bases__ == (DomainError,)
