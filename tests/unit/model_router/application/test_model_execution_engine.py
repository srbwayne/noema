import inspect
from typing import get_type_hints

import pytest

from noema.model_router.application import ModelExecutionEngine, ModelRouter
from noema.model_router.domain import (
    AmbiguousModelSelectionError,
    InvalidModelSelectionRequestError,
    ModelCapability,
    ModelCapabilityRequirements,
    ModelResource,
    ModelResourceCapabilities,
    ModelSelectionDecision,
    ModelSelectionRequest,
    ModelSelector,
    NoEligibleModelResourceError,
)
from noema.model_router.ports import (
    ModelExecutionError,
    ModelExecutionRequest,
    ModelExecutionResult,
    ModelExecutor,
)


def resource(**changes: object) -> ModelResource:
    values: dict[str, object] = {
        "resource_ref": "resource:primary",
        "provider_ref": "provider:test",
        "model_ref": "model:test-v1",
    }
    values.update(changes)
    return ModelResource(**values)


def candidate(
    *, capabilities: frozenset[ModelCapability], **resource_changes: object
) -> ModelResourceCapabilities:
    return ModelResourceCapabilities(
        resource=resource(**resource_changes), capabilities=capabilities
    )


def selection_request(
    *, required: frozenset[ModelCapability], candidates: frozenset[ModelResourceCapabilities]
) -> ModelSelectionRequest:
    return ModelSelectionRequest(
        requirements=ModelCapabilityRequirements(required_capabilities=required),
        candidates=candidates,
    )


class SpyModelRouter(ModelRouter):
    """A ModelRouter subclass recording calls and returning a fixed decision."""

    def __init__(self, result: object) -> None:
        self._result = result
        self.received_requests: list[ModelSelectionRequest] = []
        self.call_count = 0

    def route(self, request: ModelSelectionRequest) -> ModelSelectionDecision:
        self.received_requests.append(request)
        self.call_count += 1
        if isinstance(self._result, BaseException):
            raise self._result
        return self._result  # type: ignore[return-value]


class SpyModelExecutor:
    """A ModelExecutor test double recording calls and returning a fixed result."""

    def __init__(self, result: object) -> None:
        self._result = result
        self.received_requests: list[ModelExecutionRequest] = []
        self.call_count = 0

    async def execute(self, request: ModelExecutionRequest) -> ModelExecutionResult:
        self.received_requests.append(request)
        self.call_count += 1
        if isinstance(self._result, BaseException):
            raise self._result
        return self._result  # type: ignore[return-value]


def test_model_execution_engine_has_exact_slots() -> None:
    assert ModelExecutionEngine.__slots__ == ("_router", "_executor")


def test_model_execution_engine_instances_have_no_dict() -> None:
    router = SpyModelRouter(ModelSelectionDecision(selected_resource=resource()))
    executor = SpyModelExecutor(ModelExecutionResult(resource=resource(), output_text="out"))
    engine = ModelExecutionEngine(router=router, executor=executor)
    assert not hasattr(engine, "__dict__")


def test_model_execution_engine_constructor_is_keyword_only() -> None:
    router = SpyModelRouter(ModelSelectionDecision(selected_resource=resource()))
    executor = SpyModelExecutor(ModelExecutionResult(resource=resource(), output_text="out"))
    with pytest.raises(TypeError):
        ModelExecutionEngine(router, executor)  # type: ignore[misc]
    ModelExecutionEngine(router=router, executor=executor)


def test_model_execution_engine_constructor_type_hints() -> None:
    hints = get_type_hints(ModelExecutionEngine.__init__)
    assert hints["router"] is ModelRouter
    assert hints["executor"] is ModelExecutor


def test_model_execution_engine_execute_is_a_coroutine_function() -> None:
    assert inspect.iscoroutinefunction(ModelExecutionEngine.execute)


def test_model_execution_engine_execute_has_exact_public_signature() -> None:
    signature = inspect.signature(ModelExecutionEngine.execute)
    assert list(signature.parameters) == ["self", "selection_request", "input_text"]


def test_model_execution_engine_execute_type_hints() -> None:
    hints = get_type_hints(ModelExecutionEngine.execute)
    assert hints["selection_request"] is ModelSelectionRequest
    assert hints["input_text"] is str
    assert hints["return"] is ModelExecutionResult


def test_model_execution_engine_public_surface_is_only_execute() -> None:
    public_members = {name for name in vars(ModelExecutionEngine) if not name.startswith("_")}
    assert public_members == {"execute"}


def test_model_execution_engine_construction_has_no_effects() -> None:
    router = SpyModelRouter(ModelSelectionDecision(selected_resource=resource()))
    executor = SpyModelExecutor(ModelExecutionResult(resource=resource(), output_text="out"))
    ModelExecutionEngine(router=router, executor=executor)
    assert router.call_count == 0
    assert executor.call_count == 0


@pytest.mark.asyncio
async def test_model_execution_engine_passes_exact_selection_request_to_router() -> None:
    the_resource = resource()
    router = SpyModelRouter(ModelSelectionDecision(selected_resource=the_resource))
    executor = SpyModelExecutor(ModelExecutionResult(resource=the_resource, output_text="out"))
    engine = ModelExecutionEngine(router=router, executor=executor)
    the_request = selection_request(required=frozenset(), candidates=frozenset())

    await engine.execute(the_request, "hello")

    assert len(router.received_requests) == 1
    assert router.received_requests[0] is the_request


@pytest.mark.asyncio
async def test_model_execution_engine_calls_router_exactly_once() -> None:
    the_resource = resource()
    router = SpyModelRouter(ModelSelectionDecision(selected_resource=the_resource))
    executor = SpyModelExecutor(ModelExecutionResult(resource=the_resource, output_text="out"))
    engine = ModelExecutionEngine(router=router, executor=executor)

    await engine.execute(selection_request(required=frozenset(), candidates=frozenset()), "hello")

    assert router.call_count == 1


@pytest.mark.asyncio
async def test_model_execution_engine_execution_request_carries_selected_resource_identity() -> (
    None
):
    the_resource = resource()
    router = SpyModelRouter(ModelSelectionDecision(selected_resource=the_resource))
    executor = SpyModelExecutor(ModelExecutionResult(resource=the_resource, output_text="out"))
    engine = ModelExecutionEngine(router=router, executor=executor)

    await engine.execute(selection_request(required=frozenset(), candidates=frozenset()), "hello")

    assert len(executor.received_requests) == 1
    assert executor.received_requests[0].resource is the_resource


@pytest.mark.asyncio
async def test_model_execution_engine_preserves_input_text_exactly() -> None:
    the_resource = resource()
    router = SpyModelRouter(ModelSelectionDecision(selected_resource=the_resource))
    executor = SpyModelExecutor(ModelExecutionResult(resource=the_resource, output_text="out"))
    engine = ModelExecutionEngine(router=router, executor=executor)

    await engine.execute(
        selection_request(required=frozenset(), candidates=frozenset()), "  hello  "
    )

    assert executor.received_requests[0].input_text == "  hello  "


@pytest.mark.asyncio
async def test_model_execution_engine_calls_executor_exactly_once() -> None:
    the_resource = resource()
    router = SpyModelRouter(ModelSelectionDecision(selected_resource=the_resource))
    executor = SpyModelExecutor(ModelExecutionResult(resource=the_resource, output_text="out"))
    engine = ModelExecutionEngine(router=router, executor=executor)

    await engine.execute(selection_request(required=frozenset(), candidates=frozenset()), "hello")

    assert executor.call_count == 1


@pytest.mark.asyncio
async def test_model_execution_engine_executor_receives_model_execution_request() -> None:
    the_resource = resource()
    router = SpyModelRouter(ModelSelectionDecision(selected_resource=the_resource))
    executor = SpyModelExecutor(ModelExecutionResult(resource=the_resource, output_text="out"))
    engine = ModelExecutionEngine(router=router, executor=executor)

    await engine.execute(selection_request(required=frozenset(), candidates=frozenset()), "hello")

    assert isinstance(executor.received_requests[0], ModelExecutionRequest)


@pytest.mark.asyncio
async def test_model_execution_engine_returns_the_exact_result_object() -> None:
    the_resource = resource()
    router = SpyModelRouter(ModelSelectionDecision(selected_resource=the_resource))
    result = ModelExecutionResult(resource=the_resource, output_text="out")
    executor = SpyModelExecutor(result)
    engine = ModelExecutionEngine(router=router, executor=executor)

    returned = await engine.execute(
        selection_request(required=frozenset(), candidates=frozenset()), "hello"
    )

    assert returned is result


@pytest.mark.asyncio
async def test_model_execution_engine_accepts_equivalent_but_distinct_resource() -> None:
    selected_resource = resource()
    equivalent_resource = resource()
    assert equivalent_resource == selected_resource
    assert equivalent_resource is not selected_resource

    router = SpyModelRouter(ModelSelectionDecision(selected_resource=selected_resource))
    result = ModelExecutionResult(resource=equivalent_resource, output_text="out")
    executor = SpyModelExecutor(result)
    engine = ModelExecutionEngine(router=router, executor=executor)

    returned = await engine.execute(
        selection_request(required=frozenset(), candidates=frozenset()), "hello"
    )

    assert returned is result


@pytest.mark.asyncio
async def test_model_execution_engine_rejects_mismatched_resource_result() -> None:
    selected_resource = resource()
    other_resource = resource(resource_ref="resource:other")
    router = SpyModelRouter(ModelSelectionDecision(selected_resource=selected_resource))
    executor = SpyModelExecutor(ModelExecutionResult(resource=other_resource, output_text="out"))
    engine = ModelExecutionEngine(router=router, executor=executor)

    with pytest.raises(
        ModelExecutionError, match="executor result resource must match selected resource"
    ):
        await engine.execute(
            selection_request(required=frozenset(), candidates=frozenset()), "hello"
        )


@pytest.mark.parametrize(
    "invalid_result",
    [None, object(), {}, "result"],
)
@pytest.mark.asyncio
async def test_model_execution_engine_rejects_invalid_result_type(
    invalid_result: object,
) -> None:
    the_resource = resource()
    router = SpyModelRouter(ModelSelectionDecision(selected_resource=the_resource))
    executor = SpyModelExecutor(invalid_result)
    engine = ModelExecutionEngine(router=router, executor=executor)

    with pytest.raises(ModelExecutionError, match="executor must return a ModelExecutionResult"):
        await engine.execute(
            selection_request(required=frozenset(), candidates=frozenset()), "hello"
        )


@pytest.mark.asyncio
async def test_model_execution_engine_rejects_model_execution_request_as_result() -> None:
    the_resource = resource()
    router = SpyModelRouter(ModelSelectionDecision(selected_resource=the_resource))
    invalid_result = ModelExecutionRequest(resource=the_resource, input_text="not a result")
    executor = SpyModelExecutor(invalid_result)
    engine = ModelExecutionEngine(router=router, executor=executor)

    with pytest.raises(ModelExecutionError, match="executor must return a ModelExecutionResult"):
        await engine.execute(
            selection_request(required=frozenset(), candidates=frozenset()), "hello"
        )


@pytest.mark.asyncio
async def test_model_execution_engine_propagates_the_exact_execution_error_instance() -> None:
    the_resource = resource()
    router = SpyModelRouter(ModelSelectionDecision(selected_resource=the_resource))
    expected_error = ModelExecutionError("technical failure")
    executor = SpyModelExecutor(expected_error)
    engine = ModelExecutionEngine(router=router, executor=executor)

    with pytest.raises(ModelExecutionError) as raised:
        await engine.execute(
            selection_request(required=frozenset(), candidates=frozenset()), "hello"
        )

    assert raised.value is expected_error
    assert executor.call_count == 1


@pytest.mark.asyncio
async def test_model_execution_engine_propagates_invalid_selection_request_error() -> None:
    real_router = ModelRouter(selector=ModelSelector())
    executor = SpyModelExecutor(ModelExecutionResult(resource=resource(), output_text="out"))
    engine = ModelExecutionEngine(router=real_router, executor=executor)

    with pytest.raises(InvalidModelSelectionRequestError):
        await engine.execute(None, "hello")  # type: ignore[arg-type]

    assert executor.call_count == 0


@pytest.mark.asyncio
async def test_model_execution_engine_propagates_no_eligible_model_resource_error() -> None:
    real_router = ModelRouter(selector=ModelSelector())
    executor = SpyModelExecutor(ModelExecutionResult(resource=resource(), output_text="out"))
    engine = ModelExecutionEngine(router=real_router, executor=executor)
    the_request = selection_request(
        required=frozenset({ModelCapability.TEXT_GENERATION}), candidates=frozenset()
    )

    with pytest.raises(NoEligibleModelResourceError):
        await engine.execute(the_request, "hello")

    assert executor.call_count == 0


@pytest.mark.asyncio
async def test_model_execution_engine_propagates_ambiguous_model_selection_error() -> None:
    real_router = ModelRouter(selector=ModelSelector())
    executor = SpyModelExecutor(ModelExecutionResult(resource=resource(), output_text="out"))
    engine = ModelExecutionEngine(router=real_router, executor=executor)
    candidate_a = candidate(
        capabilities=frozenset({ModelCapability.TEXT_GENERATION}), resource_ref="resource:a"
    )
    candidate_b = candidate(
        capabilities=frozenset({ModelCapability.TEXT_GENERATION}), resource_ref="resource:b"
    )
    the_request = selection_request(
        required=frozenset({ModelCapability.TEXT_GENERATION}),
        candidates=frozenset({candidate_a, candidate_b}),
    )

    with pytest.raises(AmbiguousModelSelectionError):
        await engine.execute(the_request, "hello")

    assert executor.call_count == 0


@pytest.mark.asyncio
async def test_model_execution_engine_propagates_type_error_for_invalid_input_text() -> None:
    the_resource = resource()
    router = SpyModelRouter(ModelSelectionDecision(selected_resource=the_resource))
    executor = SpyModelExecutor(ModelExecutionResult(resource=the_resource, output_text="out"))
    engine = ModelExecutionEngine(router=router, executor=executor)

    with pytest.raises(TypeError, match="input_text must be a string"):
        await engine.execute(
            selection_request(required=frozenset(), candidates=frozenset()),
            None,  # type: ignore[arg-type]
        )

    assert executor.call_count == 0


@pytest.mark.parametrize("blank_text", ["", " ", "\t", "\n"])
@pytest.mark.asyncio
async def test_model_execution_engine_propagates_value_error_for_blank_input_text(
    blank_text: str,
) -> None:
    the_resource = resource()
    router = SpyModelRouter(ModelSelectionDecision(selected_resource=the_resource))
    executor = SpyModelExecutor(ModelExecutionResult(resource=the_resource, output_text="out"))
    engine = ModelExecutionEngine(router=router, executor=executor)

    with pytest.raises(ValueError, match="input_text must be a non-empty string"):
        await engine.execute(
            selection_request(required=frozenset(), candidates=frozenset()), blank_text
        )

    assert executor.call_count == 0


@pytest.mark.asyncio
async def test_model_execution_engine_does_not_retry_on_executor_failure() -> None:
    the_resource = resource()
    router = SpyModelRouter(ModelSelectionDecision(selected_resource=the_resource))
    executor = SpyModelExecutor(ModelExecutionError("boom"))
    engine = ModelExecutionEngine(router=router, executor=executor)

    with pytest.raises(ModelExecutionError):
        await engine.execute(
            selection_request(required=frozenset(), candidates=frozenset()), "hello"
        )

    assert executor.call_count == 1


@pytest.mark.asyncio
async def test_model_execution_engine_does_not_cache_across_independent_calls() -> None:
    the_resource = resource()
    router = SpyModelRouter(ModelSelectionDecision(selected_resource=the_resource))
    executor = SpyModelExecutor(ModelExecutionResult(resource=the_resource, output_text="out"))
    engine = ModelExecutionEngine(router=router, executor=executor)

    await engine.execute(selection_request(required=frozenset(), candidates=frozenset()), "hello")
    await engine.execute(selection_request(required=frozenset(), candidates=frozenset()), "hello")

    assert router.call_count == 2
    assert executor.call_count == 2


def test_model_execution_engine_application_export() -> None:
    from noema.model_router import application

    assert application.__all__ == ["ModelExecutionEngine", "ModelRouter"]
