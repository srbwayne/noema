import inspect
from datetime import timedelta
from decimal import Decimal
from typing import Protocol, get_type_hints

import pytest

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
from noema.cognition.ports import PlanningExecutor


class StubPlanningExecutor:
    """Local test double documenting the Protocol's structural intent.

    Deliberately does NOT inherit from PlanningExecutor: the port is a
    structural typing contract, not a base class adapters must extend.
    """

    async def execute(self, request: PlanningRequest) -> Plan:
        return Plan(goal_ref=request.goal_ref, steps=frozenset())


def planning_request() -> PlanningRequest:
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
        goal_ref="goal:123",
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


def test_planning_executor_is_a_protocol() -> None:
    assert issubclass(PlanningExecutor, Protocol)


def test_planning_executor_is_not_runtime_checkable() -> None:
    executor = StubPlanningExecutor()
    try:
        isinstance(executor, PlanningExecutor)
    except TypeError as error:
        assert "runtime_checkable" in str(error) or "instance" in str(error).lower()
    else:
        raise AssertionError(
            "PlanningExecutor must not be @runtime_checkable; "
            "isinstance() checks are not part of its supported API."
        )


def test_planning_executor_is_not_an_abc() -> None:
    abstract_methods = getattr(PlanningExecutor, "__abstractmethods__", frozenset())
    assert not abstract_methods


def test_planning_executor_declares_execute() -> None:
    assert hasattr(PlanningExecutor, "execute")


def test_planning_executor_execute_is_a_coroutine_function() -> None:
    assert inspect.iscoroutinefunction(PlanningExecutor.execute)


def test_planning_executor_execute_has_exact_public_signature() -> None:
    signature = inspect.signature(PlanningExecutor.execute)
    assert list(signature.parameters) == ["self", "request"]


def test_planning_executor_execute_type_hints_are_request_and_plan() -> None:
    hints = get_type_hints(PlanningExecutor.execute)
    assert hints["request"] is PlanningRequest
    assert hints["return"] is Plan


def test_planning_executor_public_surface_is_only_execute() -> None:
    public_members = {
        name for name, value in vars(PlanningExecutor).items() if not name.startswith("_")
    }
    assert public_members == {"execute"}


def test_planning_executor_does_not_expose_model_or_provider_metadata() -> None:
    forbidden = {
        "supports",
        "supports_strategy",
        "score",
        "rank",
        "route",
        "select_model",
        "select_provider",
        "capabilities",
        "cost",
        "latency",
        "availability",
        "privacy",
        "provider",
        "provider_id",
        "provider_ref",
        "model",
        "model_id",
        "model_ref",
        "model_name",
        "endpoint",
        "api_key",
        "base_url",
        "temperature",
        "top_p",
        "tokenizer",
        "prompt",
        "system_prompt",
        "generate",
    }
    declared_members = set(vars(PlanningExecutor))
    assert declared_members.isdisjoint(forbidden)


def test_planning_executor_does_not_expose_planning_behavior_api() -> None:
    forbidden = {
        "plan",
        "create_plan",
        "generate_plan",
        "build_plan",
        "decompose",
        "schedule",
        "ready_steps",
        "next_step",
        "execution_order",
        "topological_sort",
        "execute_sync",
        "run",
        "invoke",
        "call",
    }
    declared_members = set(vars(PlanningExecutor))
    assert declared_members.isdisjoint(forbidden)


@pytest.mark.asyncio
async def test_stub_executor_satisfies_the_protocol_structurally() -> None:
    request = planning_request()
    result = await StubPlanningExecutor().execute(request)
    assert isinstance(result, Plan)
    assert result.goal_ref == request.goal_ref


def test_stub_planning_executor_does_not_inherit_planning_executor() -> None:
    assert PlanningExecutor not in StubPlanningExecutor.__mro__
