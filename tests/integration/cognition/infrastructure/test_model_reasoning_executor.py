import inspect
from datetime import timedelta
from decimal import Decimal
from typing import get_type_hints

import pytest

from noema.cognition.domain.budget import CognitiveBudget
from noema.cognition.domain.context import ContextStamp
from noema.cognition.domain.context_composition import (
    ContextPackage,
    ContextPackageZone,
    ContextRequest,
    ContextSensitivity,
    ContextSlice,
    ContextSliceType,
    ContextTrustLevel,
)
from noema.cognition.domain.modes import CognitiveMode
from noema.cognition.domain.reasoning import (
    ReasoningOutcome,
    ReasoningRequest,
    ReasoningStatus,
    ReasoningStrategy,
)
from noema.cognition.infrastructure import ModelReasoningExecutor
from noema.cognition.ports import ReasoningExecutionError, ReasoningExecutor
from noema.model_router.application import ModelExecutionEngine
from noema.model_router.domain import (
    AmbiguousModelSelectionError,
    ModelCapabilityRequirements,
    ModelSelectionRequest,
    NoEligibleModelResourceError,
)
from noema.model_router.domain.model_resource import ModelResource
from noema.model_router.ports import ModelExecutionError, ModelExecutionResult

NON_DIRECT_STRATEGIES = tuple(
    strategy for strategy in ReasoningStrategy if strategy is not ReasoningStrategy.DIRECT
)


def selection_request() -> ModelSelectionRequest:
    return ModelSelectionRequest(
        requirements=ModelCapabilityRequirements(required_capabilities=frozenset()),
        candidates=frozenset(),
    )


def empty_context_package() -> ContextPackage:
    context_request = ContextRequest(
        role="reasoner",
        task_ref="task:123",
        goal_ref=None,
        mode=CognitiveMode.DELIBERATE,
        required_slice_types=(),
        forbidden_slice_types=(),
        max_sensitivity=ContextSensitivity.INTERNAL,
        minimum_trust=ContextTrustLevel.UNVERIFIED,
        allowed_authorities=(),
        max_age=None,
        max_tokens=100,
        context_stamp=ContextStamp(
            workspace_version=1,
            situation_version=1,
            identity_version=1,
            goal_version=1,
            policy_version=1,
        ),
    )
    return ContextPackage(request=context_request, slices=())


def context_package_with_one_slice() -> ContextPackage:
    context_request = ContextRequest(
        role="reasoner",
        task_ref="task:123",
        goal_ref=None,
        mode=CognitiveMode.DELIBERATE,
        required_slice_types=(ContextSliceType.TASK,),
        forbidden_slice_types=(),
        max_sensitivity=ContextSensitivity.INTERNAL,
        minimum_trust=ContextTrustLevel.UNVERIFIED,
        allowed_authorities=(),
        max_age=None,
        max_tokens=100,
        context_stamp=ContextStamp(
            workspace_version=1,
            situation_version=1,
            identity_version=1,
            goal_version=1,
            policy_version=1,
        ),
    )
    task_slice = ContextSlice(
        slice_type=ContextSliceType.TASK,
        content_ref="content:task-1",
        zone=ContextPackageZone.COGNITIVE_STATE,
        sensitivity=ContextSensitivity.INTERNAL,
        trust=ContextTrustLevel.UNVERIFIED,
        instruction_authority=None,
        provenance_ref="provenance:1",
        token_estimate=10,
    )
    return ContextPackage(request=context_request, slices=(task_slice,))


def reasoning_request(
    *,
    problem_ref: str = "problem:123",
    problem_statement: str = "Determine an answer.",
    strategy: ReasoningStrategy = ReasoningStrategy.DIRECT,
    context: ContextPackage | None = None,
) -> ReasoningRequest:
    return ReasoningRequest(
        problem_ref=problem_ref,
        problem_statement=problem_statement,
        context=context if context is not None else empty_context_package(),
        strategy=strategy,
        budget=CognitiveBudget(
            max_time=timedelta(seconds=1),
            max_steps=1,
            max_llm_calls=0,
            max_tool_calls=0,
            max_cost=Decimal("0"),
            max_tokens=0,
            max_search_depth=0,
        ),
    )


def model_resource(**changes: object) -> ModelResource:
    values: dict[str, object] = {
        "resource_ref": "resource:primary",
        "provider_ref": "provider:test",
        "model_ref": "model:test-v1",
    }
    values.update(changes)
    return ModelResource(**values)


class SpyModelExecutionEngine:
    """A ModelExecutionEngine test double recording calls and returning a fixed result."""

    def __init__(self, result: object) -> None:
        self._result = result
        self.received_selection_requests: list[ModelSelectionRequest] = []
        self.received_input_texts: list[str] = []
        self.call_count = 0

    async def execute(
        self, selection_request: ModelSelectionRequest, input_text: str
    ) -> ModelExecutionResult:
        self.received_selection_requests.append(selection_request)
        self.received_input_texts.append(input_text)
        self.call_count += 1
        if isinstance(self._result, BaseException):
            raise self._result
        return self._result  # type: ignore[return-value]


def test_model_reasoning_executor_has_exact_slots() -> None:
    assert ModelReasoningExecutor.__slots__ == ("_execution_engine", "_selection_request")


def test_model_reasoning_executor_instances_have_no_dict() -> None:
    executor = ModelReasoningExecutor(
        execution_engine=SpyModelExecutionEngine(None),  # type: ignore[arg-type]
        selection_request=selection_request(),
    )
    assert not hasattr(executor, "__dict__")


def test_model_reasoning_executor_constructor_is_keyword_only() -> None:
    engine = SpyModelExecutionEngine(None)
    with pytest.raises(TypeError):
        ModelReasoningExecutor(engine, selection_request())  # type: ignore[misc,arg-type]
    ModelReasoningExecutor(
        execution_engine=engine,  # type: ignore[arg-type]
        selection_request=selection_request(),
    )


def test_model_reasoning_executor_has_exact_type_hints() -> None:
    constructor_hints = get_type_hints(ModelReasoningExecutor.__init__)
    execute_hints = get_type_hints(ModelReasoningExecutor.execute)

    assert constructor_hints == {
        "execution_engine": ModelExecutionEngine,
        "selection_request": ModelSelectionRequest,
        "return": type(None),
    }
    assert execute_hints == {
        "request": ReasoningRequest,
        "return": ReasoningOutcome,
    }


def test_model_reasoning_executor_rejects_non_model_selection_request() -> None:
    engine = SpyModelExecutionEngine(None)
    with pytest.raises(TypeError, match="selection_request must be a ModelSelectionRequest"):
        ModelReasoningExecutor(
            execution_engine=engine,  # type: ignore[arg-type]
            selection_request=None,  # type: ignore[arg-type]
        )


def test_model_reasoning_executor_public_surface_is_only_execute() -> None:
    public_members = {name for name in vars(ModelReasoningExecutor) if not name.startswith("_")}
    assert public_members == {"execute"}


def test_model_reasoning_executor_execute_is_a_coroutine_function() -> None:
    assert inspect.iscoroutinefunction(ModelReasoningExecutor.execute)


def test_model_reasoning_executor_is_not_a_reasoning_executor_subclass() -> None:
    assert ReasoningExecutor not in ModelReasoningExecutor.__mro__


def test_model_reasoning_executor_construction_has_no_execution() -> None:
    engine = SpyModelExecutionEngine(None)
    ModelReasoningExecutor(
        execution_engine=engine,  # type: ignore[arg-type]
        selection_request=selection_request(),
    )
    assert engine.call_count == 0


@pytest.mark.asyncio
async def test_model_reasoning_executor_executes_direct_strategy_with_empty_context() -> None:
    result = ModelExecutionResult(resource=model_resource(), output_text="answer")
    engine = SpyModelExecutionEngine(result)
    executor = ModelReasoningExecutor(
        execution_engine=engine,  # type: ignore[arg-type]
        selection_request=selection_request(),
    )
    request = reasoning_request()

    outcome = await executor.execute(request)

    assert isinstance(outcome, ReasoningOutcome)
    assert engine.call_count == 1


@pytest.mark.parametrize("strategy", NON_DIRECT_STRATEGIES)
@pytest.mark.asyncio
async def test_model_reasoning_executor_rejects_every_non_direct_strategy(
    strategy: ReasoningStrategy,
) -> None:
    engine = SpyModelExecutionEngine(None)
    executor = ModelReasoningExecutor(
        execution_engine=engine,  # type: ignore[arg-type]
        selection_request=selection_request(),
    )
    request = reasoning_request(strategy=strategy)

    with pytest.raises(
        ReasoningExecutionError, match="model reasoning executor supports only DIRECT strategy"
    ):
        await executor.execute(request)

    assert engine.call_count == 0


@pytest.mark.asyncio
async def test_model_reasoning_executor_rejects_context_slices() -> None:
    engine = SpyModelExecutionEngine(None)
    executor = ModelReasoningExecutor(
        execution_engine=engine,  # type: ignore[arg-type]
        selection_request=selection_request(),
    )
    request = reasoning_request(context=context_package_with_one_slice())

    with pytest.raises(
        ReasoningExecutionError,
        match="model reasoning executor does not support context slices",
    ):
        await executor.execute(request)

    assert engine.call_count == 0


@pytest.mark.asyncio
async def test_model_reasoning_executor_passes_exact_selection_request_identity() -> None:
    the_selection_request = selection_request()
    result = ModelExecutionResult(resource=model_resource(), output_text="answer")
    engine = SpyModelExecutionEngine(result)
    executor = ModelReasoningExecutor(
        execution_engine=engine,  # type: ignore[arg-type]
        selection_request=the_selection_request,
    )
    request = reasoning_request()

    await executor.execute(request)

    assert len(engine.received_selection_requests) == 1
    assert engine.received_selection_requests[0] is the_selection_request


@pytest.mark.asyncio
async def test_model_reasoning_executor_preserves_problem_statement_exactly() -> None:
    result = ModelExecutionResult(resource=model_resource(), output_text="answer")
    engine = SpyModelExecutionEngine(result)
    executor = ModelReasoningExecutor(
        execution_engine=engine,  # type: ignore[arg-type]
        selection_request=selection_request(),
    )
    request = reasoning_request(problem_statement="  Determine an answer.  ")

    await executor.execute(request)

    assert engine.received_input_texts == ["  Determine an answer.  "]


@pytest.mark.asyncio
async def test_model_reasoning_executor_calls_engine_exactly_once() -> None:
    result = ModelExecutionResult(resource=model_resource(), output_text="answer")
    engine = SpyModelExecutionEngine(result)
    executor = ModelReasoningExecutor(
        execution_engine=engine,  # type: ignore[arg-type]
        selection_request=selection_request(),
    )

    await executor.execute(reasoning_request())

    assert engine.call_count == 1


@pytest.mark.asyncio
async def test_model_reasoning_executor_returns_expected_reasoning_outcome() -> None:
    result = ModelExecutionResult(resource=model_resource(), output_text="answer")
    engine = SpyModelExecutionEngine(result)
    executor = ModelReasoningExecutor(
        execution_engine=engine,  # type: ignore[arg-type]
        selection_request=selection_request(),
    )
    request = reasoning_request()

    outcome = await executor.execute(request)

    assert isinstance(outcome, ReasoningOutcome)
    assert outcome.problem_ref == request.problem_ref
    assert outcome.strategy is request.strategy
    assert outcome.status is ReasoningStatus.COMPLETED
    assert outcome.conclusion == "answer"
    assert outcome.reason_summary == "direct reasoning"
    assert outcome.information_needs == ()


@pytest.mark.asyncio
async def test_model_reasoning_executor_preserves_output_whitespace() -> None:
    result = ModelExecutionResult(resource=model_resource(), output_text="  answer  ")
    engine = SpyModelExecutionEngine(result)
    executor = ModelReasoningExecutor(
        execution_engine=engine,  # type: ignore[arg-type]
        selection_request=selection_request(),
    )

    outcome = await executor.execute(reasoning_request())

    assert outcome.conclusion == "  answer  "


@pytest.mark.asyncio
async def test_model_reasoning_executor_translates_model_execution_error() -> None:
    expected_error = ModelExecutionError("failure")
    engine = SpyModelExecutionEngine(expected_error)
    executor = ModelReasoningExecutor(
        execution_engine=engine,  # type: ignore[arg-type]
        selection_request=selection_request(),
    )

    with pytest.raises(ReasoningExecutionError, match="model reasoning execution failed") as raised:
        await executor.execute(reasoning_request())

    assert raised.value.__cause__ is expected_error
    assert engine.call_count == 1


@pytest.mark.asyncio
async def test_model_reasoning_executor_translates_no_eligible_model_resource_error() -> None:
    expected_error = NoEligibleModelResourceError("no eligible resource")
    engine = SpyModelExecutionEngine(expected_error)
    executor = ModelReasoningExecutor(
        execution_engine=engine,  # type: ignore[arg-type]
        selection_request=selection_request(),
    )

    with pytest.raises(ReasoningExecutionError, match="model reasoning execution failed") as raised:
        await executor.execute(reasoning_request())

    assert raised.value.__cause__ is expected_error
    assert engine.call_count == 1


@pytest.mark.asyncio
async def test_model_reasoning_executor_translates_ambiguous_model_selection_error() -> None:
    expected_error = AmbiguousModelSelectionError("ambiguous")
    engine = SpyModelExecutionEngine(expected_error)
    executor = ModelReasoningExecutor(
        execution_engine=engine,  # type: ignore[arg-type]
        selection_request=selection_request(),
    )

    with pytest.raises(ReasoningExecutionError, match="model reasoning execution failed") as raised:
        await executor.execute(reasoning_request())

    assert raised.value.__cause__ is expected_error
    assert engine.call_count == 1


@pytest.mark.asyncio
async def test_model_reasoning_executor_does_not_retry_on_translated_failure() -> None:
    engine = SpyModelExecutionEngine(ModelExecutionError("failure"))
    executor = ModelReasoningExecutor(
        execution_engine=engine,  # type: ignore[arg-type]
        selection_request=selection_request(),
    )

    with pytest.raises(ReasoningExecutionError):
        await executor.execute(reasoning_request())

    assert engine.call_count == 1


@pytest.mark.asyncio
async def test_model_reasoning_executor_does_not_mask_unexpected_errors() -> None:
    expected_error = RuntimeError("programming failure")
    engine = SpyModelExecutionEngine(expected_error)
    executor = ModelReasoningExecutor(
        execution_engine=engine,  # type: ignore[arg-type]
        selection_request=selection_request(),
    )

    with pytest.raises(RuntimeError) as raised:
        await executor.execute(reasoning_request())

    assert raised.value is expected_error


@pytest.mark.asyncio
async def test_model_reasoning_executor_is_reusable_across_independent_calls() -> None:
    result = ModelExecutionResult(resource=model_resource(), output_text="answer")
    engine = SpyModelExecutionEngine(result)
    the_selection_request = selection_request()
    executor = ModelReasoningExecutor(
        execution_engine=engine,  # type: ignore[arg-type]
        selection_request=the_selection_request,
    )

    await executor.execute(reasoning_request(problem_ref="problem:a"))
    await executor.execute(reasoning_request(problem_ref="problem:b"))

    assert engine.call_count == 2
    assert engine.received_selection_requests == [the_selection_request, the_selection_request]


def test_infrastructure_exports_model_reasoning_executor() -> None:
    from noema.cognition import infrastructure

    assert infrastructure.__all__ == ["ModelReasoningExecutor"]
