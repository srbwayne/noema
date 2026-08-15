from dataclasses import MISSING, FrozenInstanceError, fields, replace
from datetime import timedelta
from decimal import Decimal

import pytest

from noema.cognition.domain.budget import CognitiveBudget
from noema.cognition.domain.context import ContextStamp
from noema.cognition.domain.context_composition import (
    ContextPackage,
    ContextRequest,
    ContextSensitivity,
    ContextTrustLevel,
)
from noema.cognition.domain.errors import InvalidReasoningRequestError
from noema.cognition.domain.modes import CognitiveMode
from noema.cognition.domain.reasoning import ReasoningRequest, ReasoningStrategy


def context_package() -> ContextPackage:
    request = ContextRequest(
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
    return ContextPackage(request=request, slices=())


def cognitive_budget() -> CognitiveBudget:
    return CognitiveBudget(
        max_time=timedelta(seconds=10),
        max_steps=5,
        max_llm_calls=1,
        max_tool_calls=1,
        max_cost=Decimal("0.10"),
        max_tokens=1000,
        max_search_depth=2,
    )


def reasoning_request(**changes: object) -> ReasoningRequest:
    current = ReasoningRequest(
        problem_ref="problem:123",
        problem_statement="Determine the valid option.",
        context=context_package(),
        strategy=ReasoningStrategy.DIRECT,
        budget=cognitive_budget(),
    )
    return replace(current, **changes)


def test_reasoning_request_has_exact_required_fields() -> None:
    contract_fields = fields(ReasoningRequest)
    assert tuple(field.name for field in contract_fields) == (
        "problem_ref",
        "problem_statement",
        "context",
        "strategy",
        "budget",
    )
    assert all(
        field.default is MISSING and field.default_factory is MISSING for field in contract_fields
    )
    assert not {
        "mode",
        "context_stamp",
        "task_ref",
        "goal_ref",
        "confidence",
    } & {field.name for field in contract_fields}


@pytest.mark.parametrize("field_name", ["problem_ref", "problem_statement"])
@pytest.mark.parametrize("value", [None, 1, True, "", " ", "\t", "\n"])
def test_reasoning_request_rejects_invalid_strings(field_name: str, value: object) -> None:
    with pytest.raises(InvalidReasoningRequestError, match=field_name):
        reasoning_request(**{field_name: value})


@pytest.mark.parametrize("value", [None, {}, "context", ContextRequest])
def test_reasoning_request_requires_context_package(value: object) -> None:
    with pytest.raises(InvalidReasoningRequestError, match="context"):
        reasoning_request(context=value)


@pytest.mark.parametrize("value", [None, "direct", 1, CognitiveMode.FAST])
def test_reasoning_request_requires_reasoning_strategy(value: object) -> None:
    with pytest.raises(InvalidReasoningRequestError, match="strategy"):
        reasoning_request(strategy=value)


@pytest.mark.parametrize("value", [None, {}, 1, timedelta(seconds=1)])
def test_reasoning_request_requires_cognitive_budget(value: object) -> None:
    with pytest.raises(InvalidReasoningRequestError, match="budget"):
        reasoning_request(budget=value)


def test_reasoning_request_is_frozen_slotted_keyword_only_and_equal_without_mutation() -> None:
    first = reasoning_request()
    second = reasoning_request()
    assert first == second
    assert not hasattr(first, "__dict__")
    with pytest.raises(FrozenInstanceError):
        first.problem_ref = "changed"
    with pytest.raises(TypeError):
        ReasoningRequest(
            "problem:123",
            "Statement",
            context_package(),
            ReasoningStrategy.DIRECT,
            cognitive_budget(),
        )
