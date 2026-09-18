import inspect
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

import pytest

from noema.cognition.application import CognitiveBudgetAdmittingReasoningExecutor
from noema.cognition.domain.budget import CognitiveBudget
from noema.cognition.domain.context import ContextStamp
from noema.cognition.domain.context_composition import (
    ContextPackage,
    ContextRequest,
    ContextSensitivity,
    ContextTrustLevel,
)
from noema.cognition.domain.errors import CognitiveBudgetExhaustedError
from noema.cognition.domain.modes import CognitiveMode
from noema.cognition.domain.reasoning import (
    ReasoningOutcome,
    ReasoningRequest,
    ReasoningStatus,
    ReasoningStrategy,
)
from noema.cognition.ports import ReasoningExecutionError


def _budget(*, max_llm_calls: int) -> CognitiveBudget:
    return CognitiveBudget(
        max_time=timedelta(seconds=1),
        max_steps=1,
        max_llm_calls=max_llm_calls,
        max_tool_calls=0,
        max_cost=Decimal("0"),
        max_tokens=0,
        max_search_depth=0,
    )


def _reasoning_request(
    *,
    problem_ref: str = "problem:123",
    strategy: ReasoningStrategy = ReasoningStrategy.DIRECT,
    max_llm_calls: int = 1,
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
        max_total_content_size=100,
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
        budget=_budget(max_llm_calls=max_llm_calls),
    )


def _completed_outcome(
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


# --- constructor / structural shape -------------------------------------------


def test_admitting_executor_has_exact_slots() -> None:
    assert CognitiveBudgetAdmittingReasoningExecutor.__slots__ == ("_inner_executor",)


def test_admitting_executor_instances_have_no_dict() -> None:
    executor = CognitiveBudgetAdmittingReasoningExecutor(
        inner_executor=SpyReasoningExecutor(_completed_outcome())
    )
    assert not hasattr(executor, "__dict__")


def test_admitting_executor_constructor_is_keyword_only() -> None:
    inner = SpyReasoningExecutor(_completed_outcome())
    with pytest.raises(TypeError):
        CognitiveBudgetAdmittingReasoningExecutor(inner)  # type: ignore[misc]
    CognitiveBudgetAdmittingReasoningExecutor(inner_executor=inner)


def test_admitting_executor_retains_exact_inner_executor() -> None:
    inner = SpyReasoningExecutor(_completed_outcome())
    executor = CognitiveBudgetAdmittingReasoningExecutor(inner_executor=inner)
    assert executor._inner_executor is inner  # noqa: SLF001


def test_admitting_executor_execute_is_a_coroutine_function() -> None:
    assert inspect.iscoroutinefunction(CognitiveBudgetAdmittingReasoningExecutor.execute)


def test_admitting_executor_public_surface_is_only_execute() -> None:
    public_members = {
        name for name in vars(CognitiveBudgetAdmittingReasoningExecutor) if not name.startswith("_")
    }
    assert public_members == {"execute"}


# --- input validation ----------------------------------------------------------


@pytest.mark.parametrize("invalid_request", [None, {}, (), "request"])
@pytest.mark.asyncio
async def test_admitting_executor_rejects_non_reasoning_request(invalid_request: object) -> None:
    inner = SpyReasoningExecutor(_completed_outcome())
    executor = CognitiveBudgetAdmittingReasoningExecutor(inner_executor=inner)

    with pytest.raises(TypeError, match="ReasoningRequest"):
        await executor.execute(invalid_request)  # type: ignore[arg-type]

    assert inner.call_count == 0


# --- DIRECT denial ---------------------------------------------------------------


@pytest.mark.asyncio
async def test_direct_with_zero_max_llm_calls_is_denied() -> None:
    inner = SpyReasoningExecutor(_completed_outcome())
    executor = CognitiveBudgetAdmittingReasoningExecutor(inner_executor=inner)
    request = _reasoning_request(strategy=ReasoningStrategy.DIRECT, max_llm_calls=0)

    with pytest.raises(CognitiveBudgetExhaustedError):
        await executor.execute(request)


@pytest.mark.asyncio
async def test_direct_with_zero_max_llm_calls_never_calls_inner_executor() -> None:
    inner = SpyReasoningExecutor(_completed_outcome())
    executor = CognitiveBudgetAdmittingReasoningExecutor(inner_executor=inner)
    request = _reasoning_request(strategy=ReasoningStrategy.DIRECT, max_llm_calls=0)

    with pytest.raises(CognitiveBudgetExhaustedError):
        await executor.execute(request)

    assert inner.call_count == 0
    assert inner.received_requests == []


@pytest.mark.asyncio
async def test_denial_error_message_identifies_strategy_and_budget_facts() -> None:
    inner = SpyReasoningExecutor(_completed_outcome())
    executor = CognitiveBudgetAdmittingReasoningExecutor(inner_executor=inner)
    request = _reasoning_request(strategy=ReasoningStrategy.DIRECT, max_llm_calls=0)

    with pytest.raises(CognitiveBudgetExhaustedError) as raised:
        await executor.execute(request)

    message = str(raised.value)
    assert "DIRECT" in message
    assert "max_llm_calls" in message
    assert "1" in message
    assert "0" in message


@pytest.mark.asyncio
async def test_denial_error_message_excludes_problem_and_content() -> None:
    inner = SpyReasoningExecutor(_completed_outcome())
    executor = CognitiveBudgetAdmittingReasoningExecutor(inner_executor=inner)
    request = _reasoning_request(strategy=ReasoningStrategy.DIRECT, max_llm_calls=0)

    with pytest.raises(CognitiveBudgetExhaustedError) as raised:
        await executor.execute(request)

    message = str(raised.value)
    assert request.problem_statement not in message
    assert request.problem_ref not in message


# --- DIRECT admission ------------------------------------------------------------


@pytest.mark.asyncio
async def test_direct_with_max_llm_calls_one_delegates_exactly_once() -> None:
    inner = SpyReasoningExecutor(_completed_outcome())
    executor = CognitiveBudgetAdmittingReasoningExecutor(inner_executor=inner)
    request = _reasoning_request(strategy=ReasoningStrategy.DIRECT, max_llm_calls=1)

    await executor.execute(request)

    assert inner.call_count == 1


@pytest.mark.asyncio
async def test_direct_with_max_llm_calls_above_one_delegates_exactly_once() -> None:
    inner = SpyReasoningExecutor(_completed_outcome())
    executor = CognitiveBudgetAdmittingReasoningExecutor(inner_executor=inner)
    request = _reasoning_request(strategy=ReasoningStrategy.DIRECT, max_llm_calls=5)

    await executor.execute(request)

    assert inner.call_count == 1


@pytest.mark.asyncio
async def test_exact_request_identity_forwarded() -> None:
    inner = SpyReasoningExecutor(_completed_outcome())
    executor = CognitiveBudgetAdmittingReasoningExecutor(inner_executor=inner)
    request = _reasoning_request(strategy=ReasoningStrategy.DIRECT, max_llm_calls=1)

    await executor.execute(request)

    assert len(inner.received_requests) == 1
    assert inner.received_requests[0] is request


@pytest.mark.asyncio
async def test_exact_returned_outcome_identity_retained() -> None:
    outcome = _completed_outcome()
    inner = SpyReasoningExecutor(outcome)
    executor = CognitiveBudgetAdmittingReasoningExecutor(inner_executor=inner)
    request = _reasoning_request(strategy=ReasoningStrategy.DIRECT, max_llm_calls=1)

    result = await executor.execute(request)

    assert result is outcome


@pytest.mark.asyncio
async def test_inner_exception_propagates_unchanged() -> None:
    expected_error = ReasoningExecutionError("technical failure")
    inner = SpyReasoningExecutor(expected_error)
    executor = CognitiveBudgetAdmittingReasoningExecutor(inner_executor=inner)
    request = _reasoning_request(strategy=ReasoningStrategy.DIRECT, max_llm_calls=1)

    with pytest.raises(ReasoningExecutionError) as raised:
        await executor.execute(request)

    assert raised.value is expected_error


# --- non-DIRECT pass-through -----------------------------------------------------


@pytest.mark.asyncio
async def test_non_direct_request_with_zero_max_llm_calls_delegates_unchanged() -> None:
    inner = SpyReasoningExecutor(
        ReasoningOutcome(
            problem_ref="problem:123",
            strategy=ReasoningStrategy.CAUSAL,
            status=ReasoningStatus.COMPLETED,
            conclusion="the answer",
            reason_summary="causal reasoning",
            information_needs=(),
        )
    )
    executor = CognitiveBudgetAdmittingReasoningExecutor(inner_executor=inner)
    request = _reasoning_request(strategy=ReasoningStrategy.CAUSAL, max_llm_calls=0)

    result = await executor.execute(request)

    assert inner.call_count == 1
    assert inner.received_requests[0] is request
    assert result.strategy is ReasoningStrategy.CAUSAL


# --- budget object purity --------------------------------------------------------


@pytest.mark.asyncio
async def test_budget_object_remains_unmodified() -> None:
    inner = SpyReasoningExecutor(_completed_outcome())
    executor = CognitiveBudgetAdmittingReasoningExecutor(inner_executor=inner)
    request = _reasoning_request(strategy=ReasoningStrategy.DIRECT, max_llm_calls=1)
    budget_before = replace(request.budget)

    await executor.execute(request)

    assert request.budget == budget_before


@pytest.mark.asyncio
async def test_two_independent_calls_with_the_same_budget_object_each_admit_independently() -> None:
    inner = SpyReasoningExecutor(_completed_outcome())
    executor = CognitiveBudgetAdmittingReasoningExecutor(inner_executor=inner)
    shared_budget = _budget(max_llm_calls=1)

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
        max_total_content_size=100,
        context_stamp=ContextStamp(
            workspace_version=1,
            situation_version=1,
            identity_version=1,
            goal_version=1,
            policy_version=1,
        ),
    )
    context = ContextPackage(request=context_request, slices=())

    first_request = ReasoningRequest(
        problem_ref="problem:a",
        problem_statement="First.",
        context=context,
        strategy=ReasoningStrategy.DIRECT,
        budget=shared_budget,
    )
    second_request = ReasoningRequest(
        problem_ref="problem:b",
        problem_statement="Second.",
        context=context,
        strategy=ReasoningStrategy.DIRECT,
        budget=shared_budget,
    )

    await executor.execute(first_request)
    await executor.execute(second_request)

    assert inner.call_count == 2
    assert shared_budget.max_llm_calls == 1


# --- export ------------------------------------------------------------------


def test_application_package_exports_admitting_executor() -> None:
    from noema.cognition import application

    assert "CognitiveBudgetAdmittingReasoningExecutor" in application.__all__
