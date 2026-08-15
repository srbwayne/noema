from datetime import timedelta
from decimal import Decimal
from itertools import combinations

import pytest

from noema.cognition.domain.budget import CognitiveBudget
from noema.cognition.domain.context import ContextStamp
from noema.cognition.domain.context_composition import (
    ContextPackage,
    ContextRequest,
    ContextSensitivity,
    ContextTrustLevel,
)
from noema.cognition.domain.errors import (
    AmbiguousReasoningStrategyError,
    InvalidReasoningStrategyDemandError,
)
from noema.cognition.domain.modes import CognitiveMode
from noema.cognition.domain.reasoning import (
    ReasoningRequest,
    ReasoningStrategy,
    ReasoningStrategyDecision,
    ReasoningStrategyDemand,
    ReasoningStrategyReason,
    ReasoningStrategySelector,
)

REQUIREMENTS = (
    (
        "requires_decomposition",
        ReasoningStrategy.DECOMPOSITION,
        ReasoningStrategyReason.DECOMPOSITION_REQUIRED,
    ),
    (
        "requires_hypothesis_testing",
        ReasoningStrategy.HYPOTHESIS_TESTING,
        ReasoningStrategyReason.HYPOTHESIS_TESTING_REQUIRED,
    ),
    (
        "requires_causal_reasoning",
        ReasoningStrategy.CAUSAL,
        ReasoningStrategyReason.CAUSAL_REASONING_REQUIRED,
    ),
    (
        "requires_comparison",
        ReasoningStrategy.COMPARATIVE,
        ReasoningStrategyReason.COMPARISON_REQUIRED,
    ),
    ("requires_search", ReasoningStrategy.SEARCH, ReasoningStrategyReason.SEARCH_REQUIRED),
    (
        "requires_counterfactual",
        ReasoningStrategy.COUNTERFACTUAL,
        ReasoningStrategyReason.COUNTERFACTUAL_REQUIRED,
    ),
    (
        "requires_critique",
        ReasoningStrategy.CRITIQUE,
        ReasoningStrategyReason.CRITIQUE_REQUIRED,
    ),
    (
        "requires_tool_assistance",
        ReasoningStrategy.TOOL_ASSISTED,
        ReasoningStrategyReason.TOOL_ASSISTANCE_REQUIRED,
    ),
    (
        "requires_multi_model",
        ReasoningStrategy.MULTI_MODEL,
        ReasoningStrategyReason.MULTI_MODEL_REQUIRED,
    ),
)
REQUIREMENT_FIELDS = tuple(item[0] for item in REQUIREMENTS)
PAIRWISE_REQUIREMENTS = tuple(combinations(REQUIREMENT_FIELDS, 2))


def demand(**changes: object) -> ReasoningStrategyDemand:
    values: dict[str, object] = {field_name: False for field_name in REQUIREMENT_FIELDS}
    values.update(changes)
    return ReasoningStrategyDemand(**values)


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


def test_selector_is_stateless_and_selects_direct_for_no_specialized_requirement() -> None:
    selector = ReasoningStrategySelector()
    assert selector.__slots__ == ()
    assert not hasattr(selector, "__dict__")
    assert selector.select(demand()) == ReasoningStrategyDecision(
        selected_strategy=ReasoningStrategy.DIRECT,
        reason=ReasoningStrategyReason.DIRECT_SUFFICIENT,
    )


@pytest.mark.parametrize("field_name,strategy,reason", REQUIREMENTS)
def test_selector_selects_each_one_hot_requirement(
    field_name: str,
    strategy: ReasoningStrategy,
    reason: ReasoningStrategyReason,
) -> None:
    assert ReasoningStrategySelector().select(demand(**{field_name: True})) == (
        ReasoningStrategyDecision(selected_strategy=strategy, reason=reason)
    )


@pytest.mark.parametrize(
    "first,second",
    PAIRWISE_REQUIREMENTS,
    ids=lambda value: value.removeprefix("requires_"),
)
def test_selector_rejects_every_pair_of_specialized_requirements(
    first: str,
    second: str,
) -> None:
    with pytest.raises(AmbiguousReasoningStrategyError, match="multiple"):
        ReasoningStrategySelector().select(demand(**{first: True, second: True}))


def test_selector_rejects_three_specialized_requirements() -> None:
    with pytest.raises(AmbiguousReasoningStrategyError):
        ReasoningStrategySelector().select(
            demand(
                requires_decomposition=True,
                requires_search=True,
                requires_critique=True,
            )
        )


@pytest.mark.parametrize(
    "requirements",
    [
        {"requires_causal_reasoning": True, "requires_counterfactual": True},
        {"requires_tool_assistance": True, "requires_multi_model": True},
    ],
)
def test_selector_never_uses_silent_precedence(requirements: dict[str, bool]) -> None:
    with pytest.raises(AmbiguousReasoningStrategyError):
        ReasoningStrategySelector().select(demand(**requirements))


@pytest.mark.parametrize("value", [None, {}, (), "demand"])
def test_selector_requires_reasoning_strategy_demand(value: object) -> None:
    with pytest.raises(InvalidReasoningStrategyDemandError, match="demand"):
        ReasoningStrategySelector().select(value)


def test_selector_rejects_reasoning_request_as_demand() -> None:
    with pytest.raises(InvalidReasoningStrategyDemandError, match="demand"):
        ReasoningStrategySelector().select(reasoning_request())


def test_selector_is_deterministic() -> None:
    selector = ReasoningStrategySelector()
    current_demand = demand(requires_search=True)
    assert selector.select(current_demand) == selector.select(current_demand)


def test_pairwise_ambiguity_matrix_contains_all_36_pairs() -> None:
    assert len(PAIRWISE_REQUIREMENTS) == 36
