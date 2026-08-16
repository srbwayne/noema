import dataclasses
import inspect
from typing import get_type_hints

import pytest
from ollama import AsyncClient, GenerateResponse, RequestError, ResponseError

from noema.model_router import infrastructure
from noema.model_router.domain import ModelResource
from noema.model_router.infrastructure import OllamaModelExecutor
from noema.model_router.ports import (
    ModelExecutionError,
    ModelExecutionRequest,
    ModelExecutionResult,
    ModelExecutor,
)


def resource(**changes: object) -> ModelResource:
    values: dict[str, object] = {
        "resource_ref": "resource:primary",
        "provider_ref": "provider:ollama",
        "model_ref": "model:llama3",
    }
    values.update(changes)
    return ModelResource(**values)


class FakeAsyncClient:
    """A minimal test double standing in for ``ollama.AsyncClient``."""

    def __init__(self, *, response: object = None, error: BaseException | None = None) -> None:
        self._response = response
        self._error = error
        self.call_count = 0
        self.calls: list[dict[str, object]] = []

    async def generate(self, **kwargs: object) -> object:
        self.call_count += 1
        self.calls.append(kwargs)
        if self._error is not None:
            raise self._error
        return self._response


def test_ollama_model_executor_has_exact_slots() -> None:
    assert OllamaModelExecutor.__slots__ == ("_provider_ref", "_client")


def test_ollama_model_executor_instances_have_no_dict() -> None:
    executor = OllamaModelExecutor(provider_ref="provider:ollama", client=FakeAsyncClient())
    assert not hasattr(executor, "__dict__")


def test_ollama_model_executor_constructor_is_keyword_only() -> None:
    with pytest.raises(TypeError):
        OllamaModelExecutor("provider:ollama", FakeAsyncClient())  # type: ignore[misc]
    OllamaModelExecutor(provider_ref="provider:ollama", client=FakeAsyncClient())


def test_ollama_model_executor_public_surface_is_only_execute() -> None:
    public_members = {name for name in vars(OllamaModelExecutor) if not name.startswith("_")}
    assert public_members == {"execute"}


def test_ollama_model_executor_execute_is_async() -> None:
    assert inspect.iscoroutinefunction(OllamaModelExecutor.execute)


def test_ollama_model_executor_construction_does_no_io() -> None:
    client = FakeAsyncClient()
    OllamaModelExecutor(provider_ref="provider:ollama", client=client)
    assert client.call_count == 0


@pytest.mark.parametrize("invalid_provider_ref", [None, 123, object(), b"provider:ollama"])
def test_ollama_model_executor_rejects_non_string_provider_ref(
    invalid_provider_ref: object,
) -> None:
    with pytest.raises(TypeError, match="provider_ref must be a string"):
        OllamaModelExecutor(
            provider_ref=invalid_provider_ref,  # type: ignore[arg-type]
            client=FakeAsyncClient(),
        )


@pytest.mark.parametrize("blank_provider_ref", ["", " ", "\t", "\n"])
def test_ollama_model_executor_rejects_blank_provider_ref(blank_provider_ref: str) -> None:
    with pytest.raises(ValueError, match="provider_ref must be a non-empty string"):
        OllamaModelExecutor(provider_ref=blank_provider_ref, client=FakeAsyncClient())


def test_ollama_model_executor_stores_provider_ref_unnormalized() -> None:
    executor = OllamaModelExecutor(provider_ref="  provider:ollama  ", client=FakeAsyncClient())
    assert executor._provider_ref == "  provider:ollama  "


@pytest.mark.asyncio
async def test_ollama_model_executor_rejects_resource_with_mismatched_provider_ref() -> None:
    client = FakeAsyncClient(response=GenerateResponse(response="answer"))
    executor = OllamaModelExecutor(provider_ref="provider:ollama", client=client)
    request = ModelExecutionRequest(
        resource=resource(provider_ref="provider:other"), input_text="hello"
    )

    with pytest.raises(
        ModelExecutionError,
        match="resource provider_ref does not match Ollama executor provider_ref",
    ):
        await executor.execute(request)

    assert client.call_count == 0


@pytest.mark.asyncio
async def test_ollama_model_executor_maps_model_ref_and_input_text() -> None:
    client = FakeAsyncClient(response=GenerateResponse(response="answer"))
    executor = OllamaModelExecutor(provider_ref="provider:ollama", client=client)
    request = ModelExecutionRequest(
        resource=resource(model_ref="model:llama3"), input_text="  hello world  "
    )

    await executor.execute(request)

    assert client.call_count == 1
    assert client.calls[0] == {
        "model": "model:llama3",
        "prompt": "  hello world  ",
        "stream": False,
    }


@pytest.mark.asyncio
async def test_ollama_model_executor_returns_matching_result() -> None:
    client = FakeAsyncClient(response=GenerateResponse(response="answer"))
    executor = OllamaModelExecutor(provider_ref="provider:ollama", client=client)
    request = ModelExecutionRequest(resource=resource(), input_text="hello")

    result = await executor.execute(request)

    assert result.resource is request.resource
    assert result.output_text == "answer"


@pytest.mark.asyncio
async def test_ollama_model_executor_preserves_output_whitespace() -> None:
    client = FakeAsyncClient(response=GenerateResponse(response="  answer  \n"))
    executor = OllamaModelExecutor(provider_ref="provider:ollama", client=client)
    request = ModelExecutionRequest(resource=resource(), input_text="hello")

    result = await executor.execute(request)

    assert result.output_text == "  answer  \n"


@pytest.mark.asyncio
async def test_ollama_model_executor_does_not_leak_sdk_metadata() -> None:
    client = FakeAsyncClient(
        response=GenerateResponse(
            model="model:llama3", done=True, response="answer", total_duration=42
        )
    )
    executor = OllamaModelExecutor(provider_ref="provider:ollama", client=client)
    request = ModelExecutionRequest(resource=resource(), input_text="hello")

    result = await executor.execute(request)

    assert {field.name for field in dataclasses.fields(result)} == {
        "resource",
        "output_text",
    }


@pytest.mark.parametrize("invalid_response_text", [None, "", " ", "\t", "\n"])
@pytest.mark.asyncio
async def test_ollama_model_executor_rejects_invalid_response_text(
    invalid_response_text: str | None,
) -> None:
    client = FakeAsyncClient(response=GenerateResponse(response=invalid_response_text))
    executor = OllamaModelExecutor(provider_ref="provider:ollama", client=client)
    request = ModelExecutionRequest(resource=resource(), input_text="hello")

    with pytest.raises(ModelExecutionError, match="ollama returned an invalid response"):
        await executor.execute(request)


@pytest.mark.parametrize(
    "original_error",
    [
        ResponseError("boom"),
        RequestError("boom"),
        ConnectionError("boom"),
        RuntimeError("sentinel technical failure"),
    ],
)
@pytest.mark.asyncio
async def test_ollama_model_executor_translates_sdk_failures(
    original_error: Exception,
) -> None:
    client = FakeAsyncClient(error=original_error)
    executor = OllamaModelExecutor(provider_ref="provider:ollama", client=client)
    request = ModelExecutionRequest(resource=resource(), input_text="hello")

    with pytest.raises(ModelExecutionError, match="ollama execution failed") as raised:
        await executor.execute(request)

    assert raised.value.__cause__ is original_error
    assert client.call_count == 1


def test_infrastructure_exports_ollama_model_executor() -> None:
    assert infrastructure.__all__ == ["OllamaModelExecutor"]


def test_ollama_model_executor_does_not_inherit_model_executor() -> None:
    assert ModelExecutor not in OllamaModelExecutor.__mro__


def test_ollama_model_executor_is_structurally_compatible_with_model_executor_port() -> None:
    execute_method = OllamaModelExecutor.execute
    signature = inspect.signature(execute_method)
    assert list(signature.parameters) == ["self", "request"]


def test_ollama_model_executor_has_exact_type_hints() -> None:
    constructor_hints = get_type_hints(OllamaModelExecutor.__init__)
    execute_hints = get_type_hints(OllamaModelExecutor.execute)

    assert constructor_hints == {
        "provider_ref": str,
        "client": AsyncClient,
        "return": type(None),
    }

    assert execute_hints == {
        "request": ModelExecutionRequest,
        "return": ModelExecutionResult,
    }
