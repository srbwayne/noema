import inspect
from datetime import timedelta
from decimal import Decimal
from typing import get_type_hints

import pytest

from noema.cognition.application import ReasoningEngine
from noema.cognition.domain.budget import CognitiveBudget
from noema.cognition.domain.context import ContextStamp
from noema.cognition.domain.context_composition import (
    ContextPackage,
    ContextRequest,
    ContextSensitivity,
    ContextTrustLevel,
)
from noema.cognition.domain.modes import CognitiveMode
from noema.cognition.domain.reasoning import (
    InformationNeed,
    ReasoningOutcome,
    ReasoningRequest,
    ReasoningStatus,
    ReasoningStrategy,
)
from noema.cognition.ports import ReasoningExecutionError, ReasoningExecutor


def reasoning_request(
    *,
    problem_ref: str = "problem:123",
    strategy: ReasoningStrategy = ReasoningStrategy.DIRECT,
) -> ReasoningRequest:
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
    return ReasoningRequest(
        problem_ref=problem_ref,
        problem_statement="Determine an answer.",
        context=ContextPackage(request=context_request, slices=()),
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


def completed_outcome(
    *,
    problem_ref: str = "problem:123",
    strategy: ReasoningStrategy = ReasoningStrategy.DIRECT,
) -> ReasoningOutcome:
    return ReasoningOutcome(
        problem_ref=problem_ref,
        strategy=strategy,
        status=ReasoningStatus.COMPLETED,
        conclusion="the answer",
        reason_summary="direct reasoning",
        information_needs=(),
    )


def unresolved_outcome(
    *,
    problem_ref: str = "problem:123",
    strategy: ReasoningStrategy = ReasoningStrategy.DIRECT,
) -> ReasoningOutcome:
    return ReasoningOutcome(
        problem_ref=problem_ref,
        strategy=strategy,
        status=ReasoningStatus.UNRESOLVED,
        conclusion=None,
        reason_summary="could not resolve",
        information_needs=(),
    )


class StubReasoningExecutor:
    """Returns a fixed outcome regardless of the request received."""

    def __init__(self, outcome: ReasoningOutcome) -> None:
        self._outcome = outcome

    async def execute(self, request: ReasoningRequest) -> ReasoningOutcome:
        return self._outcome


class SpyReasoningExecutor:
    """Records every request received and returns a preconfigured result."""

    def __init__(self, result: object) -> None:
        self._result = result
        self.received_requests: list[ReasoningRequest] = []
        self.call_count = 0

    async def execute(self, request: ReasoningRequest) -> ReasoningOutcome:
        self.received_requests.append(request)
        self.call_count += 1
        if isinstance(self._result, BaseException):
            raise self._result
        return self._result  # type: ignore[return-value]


class FailingReasoningExecutor:
    """Raises a preconfigured ReasoningExecutionError instance."""

    def __init__(self, error: ReasoningExecutionError) -> None:
        self._error = error
        self.call_count = 0

    async def execute(self, request: ReasoningRequest) -> ReasoningOutcome:
        self.call_count += 1
        raise self._error


def test_reasoning_engine_has_exact_slots() -> None:
    assert ReasoningEngine.__slots__ == ("_executor",)


def test_reasoning_engine_instances_have_no_dict() -> None:
    engine = ReasoningEngine(executor=StubReasoningExecutor(completed_outcome()))
    assert not hasattr(engine, "__dict__")


def test_reasoning_engine_constructor_is_keyword_only() -> None:
    executor = StubReasoningExecutor(completed_outcome())
    with pytest.raises(TypeError):
        ReasoningEngine(executor)  # type: ignore[misc]
    ReasoningEngine(executor=executor)


def test_reasoning_engine_constructor_type_hint_is_reasoning_executor() -> None:
    hints = get_type_hints(ReasoningEngine.__init__)
    assert hints["executor"] is ReasoningExecutor


def test_reasoning_engine_reason_is_a_coroutine_function() -> None:
    assert inspect.iscoroutinefunction(ReasoningEngine.reason)


def test_reasoning_engine_reason_has_exact_public_signature() -> None:
    signature = inspect.signature(ReasoningEngine.reason)
    assert list(signature.parameters) == ["self", "request"]


def test_reasoning_engine_reason_type_hints() -> None:
    hints = get_type_hints(ReasoningEngine.reason)
    assert hints["request"] is ReasoningRequest
    assert hints["return"] is ReasoningOutcome


def test_reasoning_engine_public_surface_is_only_reason() -> None:
    public_members = {name for name in vars(ReasoningEngine) if not name.startswith("_")}
    assert public_members == {"reason"}


@pytest.mark.asyncio
async def test_reasoning_engine_delegates_exactly_once_with_the_same_request_object() -> None:
    request = reasoning_request()
    executor = SpyReasoningExecutor(completed_outcome())
    engine = ReasoningEngine(executor=executor)

    await engine.reason(request)

    assert executor.call_count == 1
    assert len(executor.received_requests) == 1
    assert executor.received_requests[0] is request


@pytest.mark.asyncio
async def test_reasoning_engine_returns_the_exact_outcome_object() -> None:
    request = reasoning_request()
    outcome = completed_outcome()
    executor = StubReasoningExecutor(outcome)
    engine = ReasoningEngine(executor=executor)

    result = await engine.reason(request)

    assert result is outcome


@pytest.mark.parametrize("invalid_request", [None, {}, (), "request"])
@pytest.mark.asyncio
async def test_reasoning_engine_rejects_non_reasoning_request_input(
    invalid_request: object,
) -> None:
    executor = SpyReasoningExecutor(completed_outcome())
    engine = ReasoningEngine(executor=executor)

    with pytest.raises(TypeError, match="ReasoningRequest"):
        await engine.reason(invalid_request)  # type: ignore[arg-type]

    assert executor.call_count == 0


@pytest.mark.asyncio
async def test_reasoning_engine_rejects_non_reasoning_outcome_return() -> None:
    request = reasoning_request()
    executor = SpyReasoningExecutor(None)
    engine = ReasoningEngine(executor=executor)

    with pytest.raises(ReasoningExecutionError, match="ReasoningOutcome"):
        await engine.reason(request)

    assert executor.call_count == 1


@pytest.mark.asyncio
async def test_reasoning_engine_rejects_mismatched_problem_ref() -> None:
    request = reasoning_request(problem_ref="problem:a")
    mismatched_outcome = completed_outcome(problem_ref="problem:b")
    executor = SpyReasoningExecutor(mismatched_outcome)
    engine = ReasoningEngine(executor=executor)

    with pytest.raises(ReasoningExecutionError, match="problem_ref"):
        await engine.reason(request)

    assert executor.call_count == 1


@pytest.mark.asyncio
async def test_reasoning_engine_rejects_mismatched_strategy() -> None:
    request = reasoning_request(strategy=ReasoningStrategy.DIRECT)
    mismatched_outcome = completed_outcome(strategy=ReasoningStrategy.CAUSAL)
    executor = SpyReasoningExecutor(mismatched_outcome)
    engine = ReasoningEngine(executor=executor)

    with pytest.raises(ReasoningExecutionError, match="strategy"):
        await engine.reason(request)

    assert executor.call_count == 1


@pytest.mark.asyncio
async def test_reasoning_engine_returns_unresolved_outcome_normally() -> None:
    request = reasoning_request()
    outcome = unresolved_outcome()
    executor = StubReasoningExecutor(outcome)
    engine = ReasoningEngine(executor=executor)

    result = await engine.reason(request)

    assert result is outcome
    assert result.status is ReasoningStatus.UNRESOLVED


@pytest.mark.asyncio
async def test_reasoning_engine_propagates_the_exact_execution_error_instance() -> None:
    request = reasoning_request()
    expected_error = ReasoningExecutionError("technical failure")
    executor = FailingReasoningExecutor(expected_error)
    engine = ReasoningEngine(executor=executor)

    with pytest.raises(ReasoningExecutionError) as raised:
        await engine.reason(request)

    assert raised.value is expected_error
    assert executor.call_count == 1


@pytest.mark.asyncio
async def test_reasoning_engine_does_not_call_executor_more_than_once() -> None:
    request = reasoning_request()
    executor = SpyReasoningExecutor(completed_outcome())
    engine = ReasoningEngine(executor=executor)

    await engine.reason(request)

    assert executor.call_count == 1


@pytest.mark.asyncio
async def test_reasoning_engine_does_not_mutate_request_or_outcome() -> None:
    request = reasoning_request()
    outcome = completed_outcome()
    executor = StubReasoningExecutor(outcome)
    engine = ReasoningEngine(executor=executor)

    result = await engine.reason(request)

    assert request == reasoning_request()
    assert result.information_needs == ()


@pytest.mark.asyncio
async def test_reasoning_engine_accepts_outcome_with_information_needs() -> None:
    request = reasoning_request()
    outcome = ReasoningOutcome(
        problem_ref=request.problem_ref,
        strategy=request.strategy,
        status=ReasoningStatus.PARTIAL,
        conclusion="partial answer",
        reason_summary="needs more data",
        information_needs=(
            InformationNeed(subject_ref="fact:missing", description="need more data"),
        ),
    )
    executor = StubReasoningExecutor(outcome)
    engine = ReasoningEngine(executor=executor)

    result = await engine.reason(request)

    assert result is outcome
