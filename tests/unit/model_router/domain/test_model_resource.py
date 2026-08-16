from dataclasses import MISSING, FrozenInstanceError, fields

import pytest

from noema.model_router.domain import InvalidModelResourceError, ModelResource
from noema.shared.domain import DomainError


def valid_resource(**changes: object) -> ModelResource:
    values: dict[str, object] = {
        "resource_ref": "resource:primary",
        "provider_ref": "provider:test",
        "model_ref": "model:test-v1",
    }
    values.update(changes)
    return ModelResource(**values)


def test_model_resource_has_exact_required_fields_in_order() -> None:
    contract_fields = fields(ModelResource)
    assert tuple(field.name for field in contract_fields) == (
        "resource_ref",
        "provider_ref",
        "model_ref",
    )
    assert all(
        field.default is MISSING and field.default_factory is MISSING for field in contract_fields
    )


def test_model_resource_does_not_expose_forward_looking_fields() -> None:
    field_names = {field.name for field in fields(ModelResource)}
    forbidden = {
        "agent_ref",
        "agent_id",
        "identity",
        "memory",
        "goals",
        "workspace",
        "capabilities",
        "available",
        "availability",
        "status",
        "latency",
        "score",
        "cost",
        "privacy",
        "context_window",
        "max_tokens",
        "temperature",
        "api_key",
        "endpoint",
    }
    assert field_names.isdisjoint(forbidden)


def test_model_resource_does_not_expose_routing_methods() -> None:
    forbidden_methods = {
        "supports",
        "score",
        "rank",
        "route",
        "select",
        "invoke",
        "execute",
        "generate",
    }
    public_members = {name for name in vars(ModelResource) if not name.startswith("_")}
    assert public_members.isdisjoint(forbidden_methods)


def test_model_resource_is_frozen_slotted_and_has_no_dict() -> None:
    resource = valid_resource()
    assert not hasattr(resource, "__dict__")
    with pytest.raises(FrozenInstanceError):
        resource.resource_ref = "other"


def test_model_resource_constructor_is_keyword_only() -> None:
    with pytest.raises(TypeError):
        ModelResource("resource:primary", "provider:test", "model:test-v1")  # type: ignore[misc]


def test_model_resource_accepts_valid_references_exactly() -> None:
    resource = valid_resource(
        resource_ref="resource:primary",
        provider_ref="provider:test",
        model_ref="model:test-v1",
    )
    assert resource.resource_ref == "resource:primary"
    assert resource.provider_ref == "provider:test"
    assert resource.model_ref == "model:test-v1"


def test_model_resource_structural_equality_and_hashability() -> None:
    first = valid_resource()
    second = valid_resource()
    assert first == second
    assert hash(first) == hash(second)


def test_model_resource_inequality_when_any_ref_differs() -> None:
    first = valid_resource()
    second = valid_resource(model_ref="model:other")
    assert first != second


def test_model_resource_does_not_normalize_surrounding_whitespace() -> None:
    resource = valid_resource(
        resource_ref=" resource ",
        provider_ref=" provider ",
        model_ref=" model ",
    )
    assert resource.resource_ref == " resource "
    assert resource.provider_ref == " provider "
    assert resource.model_ref == " model "


def test_model_resource_does_not_coerce_non_string_values() -> None:
    with pytest.raises(InvalidModelResourceError):
        valid_resource(resource_ref=1)  # type: ignore[arg-type]


@pytest.mark.parametrize("field_name", ["resource_ref", "provider_ref", "model_ref"])
@pytest.mark.parametrize("invalid_value", [None, 1, True, (), object()])
def test_each_field_rejects_non_string_values(field_name: str, invalid_value: object) -> None:
    with pytest.raises(InvalidModelResourceError, match=field_name):
        valid_resource(**{field_name: invalid_value})


@pytest.mark.parametrize("field_name", ["resource_ref", "provider_ref", "model_ref"])
@pytest.mark.parametrize("invalid_value", ["", " ", "\t", "\n"])
def test_each_field_rejects_empty_or_whitespace_strings(
    field_name: str, invalid_value: str
) -> None:
    with pytest.raises(InvalidModelResourceError, match=field_name):
        valid_resource(**{field_name: invalid_value})


def test_invalid_model_resource_error_inherits_directly_from_domain_error() -> None:
    assert InvalidModelResourceError.__bases__ == (DomainError,)
