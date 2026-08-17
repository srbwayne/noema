import inspect
from datetime import timedelta
from decimal import Decimal
from typing import get_type_hints

import pytest

from noema.cognition.application import Planner
from noema.cognition.domain.budget import CognitiveBudget
from noema.cognition.domain.context import ContextStamp
from noema.cognition.domain.context_composition import (
    ContextPackage,
    ContextRequest,
    ContextSensitivity,
    ContextTrustLevel,
)
from noema.cognition.domain.modes import CognitiveMode
from noema.cognition.domain.planning import Plan, PlanningRequest
from noema.cognition.ports import PlanningExecutionError, PlanningExecutor


def planning_request(*, goal_ref: str = "goal:123") -> PlanningRequest:
    context_request = ContextRequest(
        role="planner",
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
    return PlanningRequest(
        goal_ref=goal_ref,
        goal_statement="Prepare release candidate.",
        context=ContextPackage(request=context_request, slices=()),
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


def plan(*, goal_ref: str = "goal:123") -> Plan:
    return Plan(goal_ref=goal_ref, steps=frozenset())


class SpyPlanningExecutor:
    """A PlanningExecutor test double recording calls and returning a fixed result."""

    def __init__(self, result: object) -> None:
        self._result = result
        self.received_requests: list[PlanningRequest] = []
        self.call_count = 0

    async def execute(self, request: PlanningRequest) -> Plan:
        self.received_requests.append(request)
        self.call_count += 1
        if isinstance(self._result, BaseException):
            raise self._result
        return self._result  # type: ignore[return-value]


def test_planner_has_exact_slots() -> None:
    assert Planner.__slots__ == ("_executor",)


def test_planner_instances_have_no_dict() -> None:
    planner = Planner(executor=SpyPlanningExecutor(plan()))
    assert not hasattr(planner, "__dict__")


def test_planner_constructor_is_keyword_only() -> None:
    executor = SpyPlanningExecutor(plan())
    with pytest.raises(TypeError):
        Planner(executor)  # type: ignore[misc]
    Planner(executor=executor)


def test_planner_constructor_type_hints() -> None:
    hints = get_type_hints(Planner.__init__)
    assert hints == {
        "executor": PlanningExecutor,
        "return": type(None),
    }


def test_planner_plan_is_a_coroutine_function() -> None:
    assert inspect.iscoroutinefunction(Planner.plan)


def test_planner_plan_has_exact_public_signature() -> None:
    signature = inspect.signature(Planner.plan)
    assert list(signature.parameters) == ["self", "request"]


def test_planner_plan_type_hints() -> None:
    hints = get_type_hints(Planner.plan)
    assert hints == {
        "request": PlanningRequest,
        "return": Plan,
    }


def test_planner_public_surface_is_only_plan() -> None:
    public_members = {name for name in vars(Planner) if not name.startswith("_")}
    assert public_members == {"plan"}


def test_planner_does_not_expose_forbidden_members() -> None:
    forbidden = {
        "execute",
        "run",
        "invoke",
        "call",
        "create_plan",
        "generate_plan",
        "build_plan",
        "decompose",
        "schedule",
        "ready_steps",
        "next_step",
        "execution_order",
        "topological_sort",
        "reason",
        "verify",
        "evaluate",
        "provider",
        "provider_ref",
        "model",
        "model_ref",
        "capabilities",
        "selection_request",
        "temperature",
        "tokens",
        "prompt",
    }
    public_members = {name for name in vars(Planner) if not name.startswith("_")}
    assert public_members.isdisjoint(forbidden)


def test_planner_does_not_call_executor_during_construction() -> None:
    executor = SpyPlanningExecutor(plan())
    Planner(executor=executor)
    assert executor.call_count == 0


@pytest.mark.asyncio
async def test_planner_delegates_exactly_once_with_the_same_request_object() -> None:
    request = planning_request()
    executor = SpyPlanningExecutor(plan(goal_ref=request.goal_ref))
    planner = Planner(executor=executor)

    await planner.plan(request)

    assert executor.call_count == 1
    assert len(executor.received_requests) == 1
    assert executor.received_requests[0] is request


@pytest.mark.asyncio
async def test_planner_returns_the_exact_plan_object() -> None:
    request = planning_request()
    expected_plan = plan(goal_ref=request.goal_ref)
    executor = SpyPlanningExecutor(expected_plan)
    planner = Planner(executor=executor)

    result = await planner.plan(request)

    assert result is expected_plan


@pytest.mark.parametrize("invalid_request", [None, {}, (), "request"])
@pytest.mark.asyncio
async def test_planner_rejects_non_planning_request_input(
    invalid_request: object,
) -> None:
    executor = SpyPlanningExecutor(plan())
    planner = Planner(executor=executor)

    with pytest.raises(TypeError, match="request must be a PlanningRequest"):
        await planner.plan(invalid_request)  # type: ignore[arg-type]

    assert executor.call_count == 0


@pytest.mark.asyncio
async def test_planner_rejects_non_plan_return_value() -> None:
    request = planning_request()
    executor = SpyPlanningExecutor(None)
    planner = Planner(executor=executor)

    with pytest.raises(PlanningExecutionError, match="executor must return a Plan"):
        await planner.plan(request)

    assert executor.call_count == 1


@pytest.mark.parametrize("invalid_result", [object(), {}, [], "plan"])
@pytest.mark.asyncio
async def test_planner_rejects_other_invalid_result_types(
    invalid_result: object,
) -> None:
    request = planning_request()
    executor = SpyPlanningExecutor(invalid_result)
    planner = Planner(executor=executor)

    with pytest.raises(PlanningExecutionError, match="executor must return a Plan"):
        await planner.plan(request)

    assert executor.call_count == 1


@pytest.mark.asyncio
async def test_planner_rejects_mismatched_goal_ref() -> None:
    request = planning_request(goal_ref="goal:a")
    mismatched_plan = plan(goal_ref="goal:b")
    executor = SpyPlanningExecutor(mismatched_plan)
    planner = Planner(executor=executor)

    with pytest.raises(
        PlanningExecutionError, match="executor plan goal_ref must match request goal_ref"
    ):
        await planner.plan(request)

    assert executor.call_count == 1


@pytest.mark.asyncio
async def test_planner_accepts_matched_goal_ref_with_empty_plan() -> None:
    request = planning_request(goal_ref="goal:123")
    expected_plan = plan(goal_ref="goal:123")
    executor = SpyPlanningExecutor(expected_plan)
    planner = Planner(executor=executor)

    result = await planner.plan(request)

    assert result is expected_plan
    assert result.steps == frozenset()


@pytest.mark.asyncio
async def test_planner_returns_empty_plan_as_the_same_object() -> None:
    request = planning_request()
    expected_plan = plan(goal_ref=request.goal_ref)
    executor = SpyPlanningExecutor(expected_plan)
    planner = Planner(executor=executor)

    result = await planner.plan(request)

    assert result is expected_plan


@pytest.mark.asyncio
async def test_planner_propagates_the_exact_execution_error_instance() -> None:
    request = planning_request()
    expected_error = PlanningExecutionError("technical failure")
    executor = SpyPlanningExecutor(expected_error)
    planner = Planner(executor=executor)

    with pytest.raises(PlanningExecutionError) as raised:
        await planner.plan(request)

    assert raised.value is expected_error
    assert executor.call_count == 1


@pytest.mark.asyncio
async def test_planner_propagates_unexpected_errors_without_wrapping() -> None:
    request = planning_request()
    expected_error = RuntimeError("unexpected failure")
    executor = SpyPlanningExecutor(expected_error)
    planner = Planner(executor=executor)

    with pytest.raises(RuntimeError) as raised:
        await planner.plan(request)

    assert raised.value is expected_error


@pytest.mark.asyncio
async def test_planner_does_not_retry_on_success() -> None:
    request = planning_request()
    executor = SpyPlanningExecutor(plan(goal_ref=request.goal_ref))
    planner = Planner(executor=executor)

    await planner.plan(request)

    assert executor.call_count == 1


@pytest.mark.asyncio
async def test_planner_does_not_retry_on_failure() -> None:
    request = planning_request()
    executor = SpyPlanningExecutor(PlanningExecutionError("boom"))
    planner = Planner(executor=executor)

    with pytest.raises(PlanningExecutionError):
        await planner.plan(request)

    assert executor.call_count == 1


@pytest.mark.asyncio
async def test_planner_does_not_mutate_request_or_plan() -> None:
    request = planning_request()
    expected_plan = plan(goal_ref=request.goal_ref)
    executor = SpyPlanningExecutor(expected_plan)
    planner = Planner(executor=executor)

    result = await planner.plan(request)

    assert request == planning_request()
    assert result.steps == frozenset()


@pytest.mark.asyncio
async def test_planner_is_reusable_across_independent_requests() -> None:
    first_request = planning_request(goal_ref="goal:a")
    second_request = planning_request(goal_ref="goal:b")

    executor_a = SpyPlanningExecutor(plan(goal_ref="goal:a"))
    planner_a = Planner(executor=executor_a)
    await planner_a.plan(first_request)

    executor_b = SpyPlanningExecutor(plan(goal_ref="goal:b"))
    planner_b = Planner(executor=executor_b)
    await planner_b.plan(second_request)

    assert executor_a.call_count == 1
    assert executor_b.call_count == 1


@pytest.mark.asyncio
async def test_planner_processes_two_sequential_requests_with_same_instance() -> None:
    request = planning_request()
    executor = SpyPlanningExecutor(plan(goal_ref=request.goal_ref))
    planner = Planner(executor=executor)

    await planner.plan(request)
    await planner.plan(request)

    assert executor.call_count == 2


def test_spy_planning_executor_does_not_inherit_planning_executor() -> None:
    assert PlanningExecutor not in SpyPlanningExecutor.__mro__


def test_planner_application_export() -> None:
    from noema.cognition import application

    assert application.__all__ == ["Planner", "ReasoningEngine"]
