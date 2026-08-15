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
from noema.cognition.domain.reasoning import (
    ReasoningOutcome,
    ReasoningRequest,
    ReasoningStatus,
    ReasoningStrategy,
)
from noema.cognition.ports import ReasoningExecutor


class StubReasoningExecutor:
    """Local test double documenting the Protocol's structural intent.

    Deliberately does NOT inherit from ReasoningExecutor: the port is a
    structural typing contract, not a base class adapters must extend.
    """

    async def execute(self, request: ReasoningRequest) -> ReasoningOutcome:
        return ReasoningOutcome(
            problem_ref=request.problem_ref,
            strategy=request.strategy,
            status=ReasoningStatus.COMPLETED,
            conclusion="stub conclusion",
            reason_summary="stub reasoning",
            information_needs=(),
        )


def reasoning_request() -> ReasoningRequest:
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
        problem_ref="problem:123",
        problem_statement="Determine an answer.",
        context=ContextPackage(request=context_request, slices=()),
        strategy=ReasoningStrategy.DIRECT,
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


def test_reasoning_executor_is_a_protocol() -> None:
    assert issubclass(ReasoningExecutor, Protocol)


def test_reasoning_executor_is_not_runtime_checkable() -> None:
    executor = StubReasoningExecutor()
    try:
        isinstance(executor, ReasoningExecutor)
    except TypeError as error:
        assert "runtime_checkable" in str(error) or "instance" in str(error).lower()
    else:
        raise AssertionError(
            "ReasoningExecutor must not be @runtime_checkable; "
            "isinstance() checks are not part of its supported API."
        )


def test_reasoning_executor_is_not_an_abc() -> None:
    abstract_methods = getattr(ReasoningExecutor, "__abstractmethods__", frozenset())
    assert not abstract_methods


def test_reasoning_executor_declares_execute() -> None:
    assert hasattr(ReasoningExecutor, "execute")


def test_reasoning_executor_execute_is_a_coroutine_function() -> None:
    assert inspect.iscoroutinefunction(ReasoningExecutor.execute)


def test_reasoning_executor_execute_has_exact_public_signature() -> None:
    signature = inspect.signature(ReasoningExecutor.execute)
    assert list(signature.parameters) == ["self", "request"]


def test_reasoning_executor_execute_type_hints_are_request_and_outcome() -> None:
    hints = get_type_hints(ReasoningExecutor.execute)
    assert hints["request"] is ReasoningRequest
    assert hints["return"] is ReasoningOutcome


def test_reasoning_executor_public_surface_is_only_execute() -> None:
    public_members = {
        name for name, value in vars(ReasoningExecutor).items() if not name.startswith("_")
    }
    assert public_members == {"execute"}


def test_reasoning_executor_does_not_expose_model_or_provider_metadata() -> None:
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
        "model",
        "model_id",
        "model_name",
        "endpoint",
        "api_key",
        "base_url",
        "temperature",
        "top_p",
        "tokenizer",
        "prompt",
        "system_prompt",
        "execute_sync",
        "run",
        "reason",
        "invoke",
        "call",
        "generate",
    }
    declared_members = set(vars(ReasoningExecutor))
    assert declared_members.isdisjoint(forbidden)


@pytest.mark.asyncio
async def test_stub_executor_satisfies_the_protocol_structurally() -> None:
    outcome = await StubReasoningExecutor().execute(reasoning_request())
    assert isinstance(outcome, ReasoningOutcome)
