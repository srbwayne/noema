import inspect
from typing import Protocol, get_type_hints

import pytest

from noema.model_router.domain import ModelResource
from noema.model_router.ports import ModelExecutionRequest, ModelExecutionResult, ModelExecutor


def resource(**changes: object) -> ModelResource:
    values: dict[str, object] = {
        "resource_ref": "resource:primary",
        "provider_ref": "provider:test",
        "model_ref": "model:test-v1",
    }
    values.update(changes)
    return ModelResource(**values)


class StubModelExecutor:
    """Local test double documenting the Protocol's structural intent.

    Deliberately does NOT inherit from ModelExecutor: the port is a
    structural typing contract, not a base class adapters must extend.
    """

    async def execute(self, request: ModelExecutionRequest) -> ModelExecutionResult:
        return ModelExecutionResult(resource=request.resource, output_text="stub output")


def test_model_executor_is_a_protocol() -> None:
    assert issubclass(ModelExecutor, Protocol)


def test_model_executor_is_not_runtime_checkable() -> None:
    executor = StubModelExecutor()
    try:
        isinstance(executor, ModelExecutor)
    except TypeError as error:
        assert "runtime_checkable" in str(error) or "instance" in str(error).lower()
    else:
        raise AssertionError(
            "ModelExecutor must not be @runtime_checkable; "
            "isinstance() checks are not part of its supported API."
        )


def test_model_executor_is_not_an_abc() -> None:
    abstract_methods = getattr(ModelExecutor, "__abstractmethods__", frozenset())
    assert not abstract_methods


def test_model_executor_declares_execute() -> None:
    assert hasattr(ModelExecutor, "execute")


def test_model_executor_execute_is_a_coroutine_function() -> None:
    assert inspect.iscoroutinefunction(ModelExecutor.execute)


def test_model_executor_execute_has_exact_public_signature() -> None:
    signature = inspect.signature(ModelExecutor.execute)
    assert list(signature.parameters) == ["self", "request"]


def test_model_executor_execute_type_hints_are_request_and_result() -> None:
    hints = get_type_hints(ModelExecutor.execute)
    assert hints["request"] is ModelExecutionRequest
    assert hints["return"] is ModelExecutionResult


def test_model_executor_public_surface_is_only_execute() -> None:
    public_members = {
        name for name, value in vars(ModelExecutor).items() if not name.startswith("_")
    }
    assert public_members == {"execute"}


def test_model_executor_does_not_expose_selection_or_provider_metadata() -> None:
    forbidden = {
        "generate",
        "complete",
        "chat",
        "invoke",
        "call",
        "run",
        "stream",
        "route",
        "select",
        "supports",
        "health",
        "models",
    }
    declared_members = set(vars(ModelExecutor))
    assert declared_members.isdisjoint(forbidden)


@pytest.mark.asyncio
async def test_stub_executor_satisfies_the_protocol_structurally() -> None:
    request = ModelExecutionRequest(resource=resource(), input_text="hello")
    result = await StubModelExecutor().execute(request)
    assert isinstance(result, ModelExecutionResult)
