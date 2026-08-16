from dataclasses import MISSING, FrozenInstanceError, fields

import pytest

from noema.model_router.domain import (
    ModelResource,
    ModelResourceCapabilities,
    ModelSelectionDecision,
)
from noema.model_router.ports import ModelExecutionRequest, ModelExecutionResult


def resource(**changes: object) -> ModelResource:
    values: dict[str, object] = {
        "resource_ref": "resource:primary",
        "provider_ref": "provider:test",
        "model_ref": "model:test-v1",
    }
    values.update(changes)
    return ModelResource(**values)


# --- ModelExecutionRequest -------------------------------------------------


def test_execution_request_has_exact_fields_in_order() -> None:
    contract_fields = fields(ModelExecutionRequest)
    assert tuple(field.name for field in contract_fields) == ("resource", "input_text")
    assert all(
        field.default is MISSING and field.default_factory is MISSING for field in contract_fields
    )


def test_execution_request_does_not_expose_forward_looking_fields() -> None:
    field_names = {field.name for field in fields(ModelExecutionRequest)}
    forbidden = {
        "provider_ref",
        "model_ref",
        "capabilities",
        "status",
        "reason",
        "error",
        "usage",
        "tokens",
        "cost",
        "latency",
        "finish_reason",
        "temperature",
        "messages",
        "tools",
        "metadata",
        "raw_response",
        "system_prompt",
        "chat_history",
        "roles",
        "prompt_template",
        "instructions",
        "context",
    }
    assert field_names.isdisjoint(forbidden)


def test_execution_request_is_frozen_slotted_and_has_no_dict() -> None:
    request = ModelExecutionRequest(resource=resource(), input_text="hello")
    assert not hasattr(request, "__dict__")
    with pytest.raises(FrozenInstanceError):
        request.input_text = "other"  # type: ignore[misc]


def test_execution_request_constructor_is_keyword_only() -> None:
    with pytest.raises(TypeError):
        ModelExecutionRequest(resource(), "hello")  # type: ignore[misc]


def test_execution_request_is_hashable_and_structurally_equal() -> None:
    the_resource = resource()
    first = ModelExecutionRequest(resource=the_resource, input_text="hello")
    second = ModelExecutionRequest(resource=the_resource, input_text="hello")
    assert first == second
    assert hash(first) == hash(second)


def test_execution_request_accepts_valid_resource_and_text() -> None:
    the_resource = resource()
    request = ModelExecutionRequest(resource=the_resource, input_text="hello")
    assert request.resource is the_resource
    assert request.input_text == "hello"


@pytest.mark.parametrize("invalid_resource", [None, "resource", {}, object()])
def test_execution_request_rejects_non_model_resource(invalid_resource: object) -> None:
    with pytest.raises(TypeError, match="resource must be a ModelResource"):
        ModelExecutionRequest(resource=invalid_resource, input_text="hello")  # type: ignore[arg-type]


def test_execution_request_rejects_model_selection_decision_as_resource() -> None:
    decision = ModelSelectionDecision(selected_resource=resource())
    with pytest.raises(TypeError, match="resource must be a ModelResource"):
        ModelExecutionRequest(resource=decision, input_text="hello")  # type: ignore[arg-type]


def test_execution_request_rejects_model_resource_capabilities_as_resource() -> None:
    profile = ModelResourceCapabilities(resource=resource(), capabilities=frozenset())
    with pytest.raises(TypeError, match="resource must be a ModelResource"):
        ModelExecutionRequest(resource=profile, input_text="hello")  # type: ignore[arg-type]


@pytest.mark.parametrize("invalid_text", [None, 1, True, b"bytes", [], {}])
def test_execution_request_rejects_non_string_input_text(invalid_text: object) -> None:
    with pytest.raises(TypeError, match="input_text must be a string"):
        ModelExecutionRequest(resource=resource(), input_text=invalid_text)  # type: ignore[arg-type]


@pytest.mark.parametrize("blank_text", ["", " ", "\t", "\n", " \t\n "])
def test_execution_request_rejects_blank_input_text(blank_text: str) -> None:
    with pytest.raises(ValueError, match="input_text must be a non-empty string"):
        ModelExecutionRequest(resource=resource(), input_text=blank_text)


def test_execution_request_preserves_surrounding_whitespace_exactly() -> None:
    request = ModelExecutionRequest(resource=resource(), input_text="  hello  ")
    assert request.input_text == "  hello  "


# --- ModelExecutionResult ---------------------------------------------------


def test_execution_result_has_exact_fields_in_order() -> None:
    contract_fields = fields(ModelExecutionResult)
    assert tuple(field.name for field in contract_fields) == ("resource", "output_text")
    assert all(
        field.default is MISSING and field.default_factory is MISSING for field in contract_fields
    )


def test_execution_result_does_not_expose_forward_looking_fields() -> None:
    field_names = {field.name for field in fields(ModelExecutionResult)}
    forbidden = {
        "provider_ref",
        "model_ref",
        "capabilities",
        "status",
        "reason",
        "error",
        "exception",
        "failure_reason",
        "retryable",
        "provider_error",
        "error_code",
        "usage",
        "tokens",
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "cost",
        "latency",
        "duration",
        "finish_reason",
        "stop_reason",
        "raw_response",
        "provider_response",
        "response_object",
        "sdk_response",
        "headers",
        "http_status",
    }
    assert field_names.isdisjoint(forbidden)


def test_execution_result_is_frozen_slotted_and_has_no_dict() -> None:
    result = ModelExecutionResult(resource=resource(), output_text="answer")
    assert not hasattr(result, "__dict__")
    with pytest.raises(FrozenInstanceError):
        result.output_text = "other"  # type: ignore[misc]


def test_execution_result_constructor_is_keyword_only() -> None:
    with pytest.raises(TypeError):
        ModelExecutionResult(resource(), "answer")  # type: ignore[misc]


def test_execution_result_is_hashable_and_structurally_equal() -> None:
    the_resource = resource()
    first = ModelExecutionResult(resource=the_resource, output_text="answer")
    second = ModelExecutionResult(resource=the_resource, output_text="answer")
    assert first == second
    assert hash(first) == hash(second)


def test_execution_result_accepts_valid_resource_and_text() -> None:
    the_resource = resource()
    result = ModelExecutionResult(resource=the_resource, output_text="answer")
    assert result.resource is the_resource
    assert result.output_text == "answer"


@pytest.mark.parametrize("invalid_resource", [None, "resource", {}, object()])
def test_execution_result_rejects_non_model_resource(invalid_resource: object) -> None:
    with pytest.raises(TypeError, match="resource must be a ModelResource"):
        ModelExecutionResult(resource=invalid_resource, output_text="answer")  # type: ignore[arg-type]


@pytest.mark.parametrize("invalid_text", [None, 1, True, b"bytes", [], {}])
def test_execution_result_rejects_non_string_output_text(invalid_text: object) -> None:
    with pytest.raises(TypeError, match="output_text must be a string"):
        ModelExecutionResult(resource=resource(), output_text=invalid_text)  # type: ignore[arg-type]


@pytest.mark.parametrize("blank_text", ["", " ", "\t", "\n", " \t\n "])
def test_execution_result_rejects_blank_output_text(blank_text: str) -> None:
    with pytest.raises(ValueError, match="output_text must be a non-empty string"):
        ModelExecutionResult(resource=resource(), output_text=blank_text)


def test_execution_result_preserves_surrounding_whitespace_exactly() -> None:
    result = ModelExecutionResult(resource=resource(), output_text="  answer  ")
    assert result.output_text == "  answer  "


# --- Existing contracts intact ----------------------------------------------


def test_existing_model_router_contracts_remain_intact() -> None:
    from noema.model_router.application import ModelRouter
    from noema.model_router.domain import (
        ModelCapabilityRequirements,
        ModelSelectionRequest,
        ModelSelector,
    )

    assert tuple(field.name for field in fields(ModelResource)) == (
        "resource_ref",
        "provider_ref",
        "model_ref",
    )
    assert tuple(field.name for field in fields(ModelSelectionRequest)) == (
        "requirements",
        "candidates",
    )
    assert tuple(field.name for field in fields(ModelSelectionDecision)) == ("selected_resource",)
    assert tuple(field.name for field in fields(ModelCapabilityRequirements)) == (
        "required_capabilities",
    )
    assert {name for name in vars(ModelSelector) if not name.startswith("_")} == {"select"}
    assert {name for name in vars(ModelRouter) if not name.startswith("_")} == {"route"}
