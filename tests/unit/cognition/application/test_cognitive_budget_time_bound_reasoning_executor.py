import asyncio
import inspect
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

import pytest

from noema.cognition.application import CognitiveBudgetTimeBoundReasoningExecutor
from noema.cognition.domain.budget import CognitiveBudget, CognitiveBudgetTimeExceededError
from noema.cognition.domain.context import ContextStamp
from noema.cognition.domain.context_composition import (
    ContextPackage,
    ContextRequest,
    ContextSensitivity,
    ContextTrustLevel,
)
from noema.cognition.domain.modes import CognitiveMode
from noema.cognition.domain.reasoning import (
    ReasoningOutcome,
    ReasoningRequest,
    ReasoningStatus,
    ReasoningStrategy,
)
from noema.cognition.ports import ReasoningExecutionError


def _budget(*, max_time: timedelta = timedelta(seconds=1)) -> CognitiveBudget:
    return CognitiveBudget(
        max_time=max_time,
        max_steps=1,
        max_llm_calls=1,
        max_tool_calls=0,
        max_cost=Decimal("0"),
        max_tokens=0,
        max_search_depth=0,
    )


def _reasoning_request(
    *,
    problem_ref: str = "problem:123",
    strategy: ReasoningStrategy = ReasoningStrategy.DIRECT,
    budget: CognitiveBudget | None = None,
    max_time: timedelta = timedelta(seconds=1),
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
        budget=budget if budget is not None else _budget(max_time=max_time),
    )


def _completed_outcome(*, problem_ref: str = "problem:123") -> ReasoningOutcome:
    return ReasoningOutcome(
        problem_ref=problem_ref,
        strategy=ReasoningStrategy.DIRECT,
        status=ReasoningStatus.COMPLETED,
        conclusion="the answer",
        reason_summary="direct reasoning",
        information_needs=(),
    )


class SpyReasoningExecutor:
    """Records every request received and returns/raises a preconfigured result."""

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


class BlockingReasoningExecutor:
    """Blocks cooperatively until cancelled, recording whether it observed it."""

    def __init__(self) -> None:
        self.call_count = 0
        self.cancellation_observed = False
        self.started = asyncio.Event()

    async def execute(self, request: ReasoningRequest) -> ReasoningOutcome:
        self.call_count += 1
        self.started.set()
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            self.cancellation_observed = True
            raise
        raise AssertionError("unreachable")


class ImmediateTimeoutErrorExecutor:
    """Raises one exact, caller-supplied TimeoutError with no relation to this decorator."""

    def __init__(self, error: TimeoutError) -> None:
        self._error = error
        self.call_count = 0

    async def execute(self, request: ReasoningRequest) -> ReasoningOutcome:
        self.call_count += 1
        raise self._error


class SleepingReasoningExecutor:
    """Sleeps a fixed real duration before returning a preconfigured outcome."""

    def __init__(self, *, delay_seconds: float, outcome: ReasoningOutcome) -> None:
        self._delay_seconds = delay_seconds
        self._outcome = outcome
        self.call_count = 0

    async def execute(self, request: ReasoningRequest) -> ReasoningOutcome:
        self.call_count += 1
        await asyncio.sleep(self._delay_seconds)
        return self._outcome


# --- constructor / structural shape -------------------------------------------


def test_time_bound_executor_has_exact_slots() -> None:
    assert CognitiveBudgetTimeBoundReasoningExecutor.__slots__ == ("_inner_executor",)


def test_time_bound_executor_instances_have_no_dict() -> None:
    executor = CognitiveBudgetTimeBoundReasoningExecutor(
        inner_executor=SpyReasoningExecutor(_completed_outcome())
    )
    assert not hasattr(executor, "__dict__")


def test_time_bound_executor_constructor_is_keyword_only() -> None:
    inner = SpyReasoningExecutor(_completed_outcome())
    with pytest.raises(TypeError):
        CognitiveBudgetTimeBoundReasoningExecutor(inner)  # type: ignore[misc]
    CognitiveBudgetTimeBoundReasoningExecutor(inner_executor=inner)


def test_time_bound_executor_retains_exact_inner_executor() -> None:
    inner = SpyReasoningExecutor(_completed_outcome())
    executor = CognitiveBudgetTimeBoundReasoningExecutor(inner_executor=inner)
    assert executor._inner_executor is inner  # noqa: SLF001


def test_time_bound_executor_execute_is_a_coroutine_function() -> None:
    assert inspect.iscoroutinefunction(CognitiveBudgetTimeBoundReasoningExecutor.execute)


def test_time_bound_executor_public_surface_is_only_execute() -> None:
    public_members = {
        name for name in vars(CognitiveBudgetTimeBoundReasoningExecutor) if not name.startswith("_")
    }
    assert public_members == {"execute"}


# --- input validation ----------------------------------------------------------


@pytest.mark.parametrize("invalid_request", [None, {}, (), "request"])
@pytest.mark.asyncio
async def test_time_bound_executor_rejects_non_reasoning_request(invalid_request: object) -> None:
    inner = SpyReasoningExecutor(_completed_outcome())
    executor = CognitiveBudgetTimeBoundReasoningExecutor(inner_executor=inner)

    with pytest.raises(TypeError, match="ReasoningRequest"):
        await executor.execute(invalid_request)  # type: ignore[arg-type]

    assert inner.call_count == 0


# --- success path ----------------------------------------------------------------


@pytest.mark.asyncio
async def test_successful_execution_returns_exact_outcome_identity() -> None:
    outcome = _completed_outcome()
    inner = SpyReasoningExecutor(outcome)
    executor = CognitiveBudgetTimeBoundReasoningExecutor(inner_executor=inner)
    request = _reasoning_request()

    result = await executor.execute(request)

    assert result is outcome


@pytest.mark.asyncio
async def test_exact_request_identity_forwarded() -> None:
    inner = SpyReasoningExecutor(_completed_outcome())
    executor = CognitiveBudgetTimeBoundReasoningExecutor(inner_executor=inner)
    request = _reasoning_request()

    await executor.execute(request)

    assert len(inner.received_requests) == 1
    assert inner.received_requests[0] is request


@pytest.mark.asyncio
async def test_budget_object_remains_unmodified() -> None:
    inner = SpyReasoningExecutor(_completed_outcome())
    executor = CognitiveBudgetTimeBoundReasoningExecutor(inner_executor=inner)
    request = _reasoning_request()
    budget_before = replace(request.budget)

    await executor.execute(request)

    assert request.budget == budget_before


@pytest.mark.asyncio
async def test_inner_reasoning_execution_error_propagates_unchanged() -> None:
    expected_error = ReasoningExecutionError("technical failure")
    inner = SpyReasoningExecutor(expected_error)
    executor = CognitiveBudgetTimeBoundReasoningExecutor(inner_executor=inner)
    request = _reasoning_request()

    with pytest.raises(ReasoningExecutionError) as raised:
        await executor.execute(request)

    assert raised.value is expected_error


# --- deadline expiry ---------------------------------------------------------------


@pytest.mark.asyncio
async def test_deadline_expiry_raises_cognitive_budget_time_exceeded_error() -> None:
    inner = BlockingReasoningExecutor()
    executor = CognitiveBudgetTimeBoundReasoningExecutor(inner_executor=inner)
    request = _reasoning_request(max_time=timedelta(milliseconds=50))

    with pytest.raises(CognitiveBudgetTimeExceededError):
        await executor.execute(request)

    # Inner execution actually began before the deadline cancelled it.
    assert inner.call_count == 1
    assert inner.started.is_set()


@pytest.mark.asyncio
async def test_deadline_expiry_delivers_cancellation_to_inner_executor() -> None:
    inner = BlockingReasoningExecutor()
    executor = CognitiveBudgetTimeBoundReasoningExecutor(inner_executor=inner)
    request = _reasoning_request(max_time=timedelta(milliseconds=50))

    with pytest.raises(CognitiveBudgetTimeExceededError):
        await executor.execute(request)

    assert inner.cancellation_observed is True


@pytest.mark.asyncio
async def test_deadline_expiry_cause_is_the_original_timeout_error() -> None:
    inner = BlockingReasoningExecutor()
    executor = CognitiveBudgetTimeBoundReasoningExecutor(inner_executor=inner)
    request = _reasoning_request(max_time=timedelta(milliseconds=50))

    with pytest.raises(CognitiveBudgetTimeExceededError) as raised:
        await executor.execute(request)

    assert isinstance(raised.value.__cause__, TimeoutError)


@pytest.mark.asyncio
async def test_deadline_expiry_message_identifies_strategy_and_max_time() -> None:
    inner = BlockingReasoningExecutor()
    executor = CognitiveBudgetTimeBoundReasoningExecutor(inner_executor=inner)
    max_time = timedelta(milliseconds=50)
    request = _reasoning_request(max_time=max_time)

    with pytest.raises(CognitiveBudgetTimeExceededError) as raised:
        await executor.execute(request)

    message = str(raised.value)
    assert "DIRECT" in message
    assert str(max_time) in message


@pytest.mark.asyncio
async def test_deadline_expiry_message_excludes_problem_content() -> None:
    inner = BlockingReasoningExecutor()
    executor = CognitiveBudgetTimeBoundReasoningExecutor(inner_executor=inner)
    request = _reasoning_request(max_time=timedelta(milliseconds=50))

    with pytest.raises(CognitiveBudgetTimeExceededError) as raised:
        await executor.execute(request)

    message = str(raised.value)
    assert request.problem_statement not in message
    assert request.problem_ref not in message


# --- raw inner TimeoutError firewall (not owned by this decorator) -------------


@pytest.mark.asyncio
async def test_raw_inner_timeout_error_with_ample_max_time_propagates_unchanged() -> None:
    # A comfortably large max_time ensures this decorator's own timeout scope
    # never expires, so timeout_context.expired() is False and the exact
    # inner TimeoutError instance -- not a copy, not a re-raised equivalent --
    # must propagate untouched.
    expected_error = TimeoutError("unrelated technical timeout")
    inner = ImmediateTimeoutErrorExecutor(expected_error)
    executor = CognitiveBudgetTimeBoundReasoningExecutor(inner_executor=inner)
    request = _reasoning_request(max_time=timedelta(seconds=30))

    with pytest.raises(TimeoutError) as raised:
        await executor.execute(request)

    assert raised.value is expected_error
    assert not isinstance(raised.value, CognitiveBudgetTimeExceededError)
    assert inner.call_count == 1


# --- external cancellation -------------------------------------------------------


@pytest.mark.asyncio
async def test_external_cancellation_propagates_cancelled_error_unchanged() -> None:
    inner = BlockingReasoningExecutor()
    executor = CognitiveBudgetTimeBoundReasoningExecutor(inner_executor=inner)
    request = _reasoning_request(max_time=timedelta(seconds=30))

    task = asyncio.ensure_future(executor.execute(request))
    await inner.started.wait()
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task

    assert inner.cancellation_observed is True


# --- per-request reset / concurrent independence --------------------------------


@pytest.mark.asyncio
async def test_two_sequential_calls_with_the_same_budget_each_get_a_fresh_deadline() -> None:
    outcome = _completed_outcome()
    # Each call sleeps 120ms against a 200ms budget: individually well within
    # budget, but their sum (240ms) would exceed it if any elapsed time from
    # the first call leaked into the second's deadline.
    inner = SleepingReasoningExecutor(delay_seconds=0.12, outcome=outcome)
    executor = CognitiveBudgetTimeBoundReasoningExecutor(inner_executor=inner)
    shared_budget = _budget(max_time=timedelta(milliseconds=200))
    first_request = _reasoning_request(budget=shared_budget, problem_ref="problem:a")
    second_request = _reasoning_request(budget=shared_budget, problem_ref="problem:b")

    result_a = await executor.execute(first_request)
    result_b = await executor.execute(second_request)

    assert result_a is outcome
    assert result_b is outcome
    assert inner.call_count == 2


@pytest.mark.asyncio
async def test_two_concurrent_calls_share_no_timer_state() -> None:
    outcome_a = _completed_outcome(problem_ref="problem:a")
    outcome_b = _completed_outcome(problem_ref="problem:b")

    class _PerRequestOutcomeExecutor:
        def __init__(self) -> None:
            self.call_count = 0

        async def execute(self, request: ReasoningRequest) -> ReasoningOutcome:
            self.call_count += 1
            if request.problem_ref == "problem:a":
                await asyncio.sleep(0.12)
                return outcome_a
            await asyncio.sleep(0.02)
            return outcome_b

    inner = _PerRequestOutcomeExecutor()
    executor = CognitiveBudgetTimeBoundReasoningExecutor(inner_executor=inner)
    shared_budget = _budget(max_time=timedelta(milliseconds=200))
    request_a = _reasoning_request(budget=shared_budget, problem_ref="problem:a")
    request_b = _reasoning_request(budget=shared_budget, problem_ref="problem:b")

    result_a, result_b = await asyncio.gather(
        executor.execute(request_a), executor.execute(request_b)
    )

    assert result_a is outcome_a
    assert result_b is outcome_b
    assert inner.call_count == 2


# --- export ------------------------------------------------------------------


def test_application_package_exports_time_bound_executor() -> None:
    from noema.cognition import application

    assert "CognitiveBudgetTimeBoundReasoningExecutor" in application.__all__
