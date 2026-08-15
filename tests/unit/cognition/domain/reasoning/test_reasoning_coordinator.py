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
from noema.cognition.domain.errors import InvalidReasoningStrategyDemandError
from noema.cognition.domain.modes import CognitiveMode
from noema.cognition.domain.reasoning import (
    ReasoningCoordinationPlan,
    ReasoningCoordinator,
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


def test_coordinator_is_stateless() -> None:
    coordinator = ReasoningCoordinator()
    assert coordinator.__slots__ == ()
    assert not hasattr(coordinator, "__dict__")


def test_coordinator_is_deterministic_across_repeated_calls() -> None:
    coordinator = ReasoningCoordinator()
    current_demand = demand(requires_causal_reasoning=True, requires_counterfactual=True)
    assert coordinator.coordinate(current_demand) == coordinator.coordinate(current_demand)


def test_coordinator_returns_direct_for_zero_requirements() -> None:
    plan = ReasoningCoordinator().coordinate(demand())
    assert plan == ReasoningCoordinationPlan(
        strategy_decisions=frozenset(
            (
                ReasoningStrategyDecision(
                    selected_strategy=ReasoningStrategy.DIRECT,
                    reason=ReasoningStrategyReason.DIRECT_SUFFICIENT,
                ),
            )
        )
    )
    assert len(plan.strategy_decisions) == 1


@pytest.mark.parametrize("field_name,strategy,reason", REQUIREMENTS)
def test_coordinator_one_hot_matches_selector_decision(
    field_name: str,
    strategy: ReasoningStrategy,
    reason: ReasoningStrategyReason,
) -> None:
    one_hot_demand = demand(**{field_name: True})

    plan = ReasoningCoordinator().coordinate(one_hot_demand)
    selector_decision = ReasoningStrategySelector().select(one_hot_demand)

    assert len(plan.strategy_decisions) == 1
    (coordinator_decision,) = plan.strategy_decisions
    assert coordinator_decision == selector_decision
    assert coordinator_decision == ReasoningStrategyDecision(
        selected_strategy=strategy, reason=reason
    )


@pytest.mark.parametrize(
    "first,second",
    PAIRWISE_REQUIREMENTS,
    ids=lambda value: value.removeprefix("requires_"),
)
def test_coordinator_coordinates_every_pair_the_selector_rejects_as_ambiguous(
    first: str,
    second: str,
) -> None:
    pairwise_demand = demand(**{first: True, second: True})
    field_to_strategy_reason = {item[0]: (item[1], item[2]) for item in REQUIREMENTS}
    expected_decisions = frozenset(
        ReasoningStrategyDecision(selected_strategy=strategy, reason=reason)
        for strategy, reason in (
            field_to_strategy_reason[first],
            field_to_strategy_reason[second],
        )
    )

    plan = ReasoningCoordinator().coordinate(pairwise_demand)

    assert plan.strategy_decisions == expected_decisions
    assert len(plan.strategy_decisions) == 2
    assert ReasoningStrategy.DIRECT not in {
        decision.selected_strategy for decision in plan.strategy_decisions
    }


def test_pairwise_requirements_contains_all_36_pairs() -> None:
    assert len(PAIRWISE_REQUIREMENTS) == 36


def test_coordinator_coordinates_a_triple_without_ambiguity() -> None:
    triple_demand = demand(
        requires_decomposition=True,
        requires_search=True,
        requires_critique=True,
    )

    plan = ReasoningCoordinator().coordinate(triple_demand)

    assert len(plan.strategy_decisions) == 3
    assert plan.strategy_decisions == frozenset(
        (
            ReasoningStrategyDecision(
                selected_strategy=ReasoningStrategy.DECOMPOSITION,
                reason=ReasoningStrategyReason.DECOMPOSITION_REQUIRED,
            ),
            ReasoningStrategyDecision(
                selected_strategy=ReasoningStrategy.SEARCH,
                reason=ReasoningStrategyReason.SEARCH_REQUIRED,
            ),
            ReasoningStrategyDecision(
                selected_strategy=ReasoningStrategy.CRITIQUE,
                reason=ReasoningStrategyReason.CRITIQUE_REQUIRED,
            ),
        )
    )


def test_coordinator_coordinates_all_nine_specialized_requirements() -> None:
    all_true_demand = demand(**{field_name: True for field_name in REQUIREMENT_FIELDS})

    plan = ReasoningCoordinator().coordinate(all_true_demand)

    assert len(plan.strategy_decisions) == 9
    selected_strategies = {decision.selected_strategy for decision in plan.strategy_decisions}
    assert selected_strategies == {
        ReasoningStrategy.DECOMPOSITION,
        ReasoningStrategy.HYPOTHESIS_TESTING,
        ReasoningStrategy.CAUSAL,
        ReasoningStrategy.COMPARATIVE,
        ReasoningStrategy.SEARCH,
        ReasoningStrategy.COUNTERFACTUAL,
        ReasoningStrategy.CRITIQUE,
        ReasoningStrategy.TOOL_ASSISTED,
        ReasoningStrategy.MULTI_MODEL,
    }
    assert ReasoningStrategy.DIRECT not in selected_strategies


def test_coordinator_plan_equality_is_independent_of_frozenset_construction_order() -> None:
    causal_and_counterfactual = demand(requires_causal_reasoning=True, requires_counterfactual=True)

    plan_one = ReasoningCoordinator().coordinate(causal_and_counterfactual)
    reordered_decisions = frozenset(reversed(tuple(plan_one.strategy_decisions)))
    plan_two = ReasoningCoordinationPlan(strategy_decisions=reordered_decisions)

    assert plan_one == plan_two


@pytest.mark.parametrize("value", [None, {}, (), "demand"])
def test_coordinator_requires_reasoning_strategy_demand(value: object) -> None:
    with pytest.raises(InvalidReasoningStrategyDemandError, match="demand"):
        ReasoningCoordinator().coordinate(value)


def test_coordinator_rejects_reasoning_request_as_demand() -> None:
    with pytest.raises(InvalidReasoningStrategyDemandError, match="demand"):
        ReasoningCoordinator().coordinate(reasoning_request())
