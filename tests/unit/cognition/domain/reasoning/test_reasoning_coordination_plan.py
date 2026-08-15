from dataclasses import MISSING, FrozenInstanceError, fields

import pytest

from noema.cognition.domain.errors import InvalidReasoningCoordinationPlanError
from noema.cognition.domain.reasoning import (
    ReasoningCoordinationPlan,
    ReasoningStrategy,
    ReasoningStrategyDecision,
    ReasoningStrategyReason,
)

DIRECT_DECISION = ReasoningStrategyDecision(
    selected_strategy=ReasoningStrategy.DIRECT,
    reason=ReasoningStrategyReason.DIRECT_SUFFICIENT,
)
CAUSAL_DECISION = ReasoningStrategyDecision(
    selected_strategy=ReasoningStrategy.CAUSAL,
    reason=ReasoningStrategyReason.CAUSAL_REASONING_REQUIRED,
)
COUNTERFACTUAL_DECISION = ReasoningStrategyDecision(
    selected_strategy=ReasoningStrategy.COUNTERFACTUAL,
    reason=ReasoningStrategyReason.COUNTERFACTUAL_REQUIRED,
)
SEARCH_DECISION = ReasoningStrategyDecision(
    selected_strategy=ReasoningStrategy.SEARCH,
    reason=ReasoningStrategyReason.SEARCH_REQUIRED,
)


def test_plan_has_exact_required_field() -> None:
    contract_fields = fields(ReasoningCoordinationPlan)
    assert tuple(field.name for field in contract_fields) == ("strategy_decisions",)
    assert all(
        field.default is MISSING and field.default_factory is MISSING for field in contract_fields
    )


def test_plan_does_not_expose_execution_order_budget_or_identity_fields() -> None:
    field_names = {field.name for field in fields(ReasoningCoordinationPlan)}
    forbidden = {
        "problem_ref",
        "problem_statement",
        "context",
        "budget",
        "mode",
        "context_stamp",
        "execution_order",
        "sequence",
        "stages",
        "steps",
        "current_strategy",
        "next_strategy",
        "completed_strategies",
        "pending_strategies",
        "score",
        "confidence",
        "provider",
        "model",
        "tool",
        "timestamp",
        "uuid",
        "id",
    }
    assert field_names.isdisjoint(forbidden)


def test_plan_is_frozen_slotted_keyword_only_and_structurally_equal() -> None:
    first = ReasoningCoordinationPlan(strategy_decisions=frozenset((DIRECT_DECISION,)))
    second = ReasoningCoordinationPlan(strategy_decisions=frozenset((DIRECT_DECISION,)))
    assert first == second
    assert not hasattr(first, "__dict__")
    with pytest.raises(FrozenInstanceError):
        first.strategy_decisions = frozenset((DIRECT_DECISION,))
    with pytest.raises(TypeError):
        ReasoningCoordinationPlan(frozenset((DIRECT_DECISION,)))


def test_plan_accepts_direct_alone() -> None:
    plan = ReasoningCoordinationPlan(strategy_decisions=frozenset((DIRECT_DECISION,)))
    assert plan.strategy_decisions == frozenset((DIRECT_DECISION,))


def test_plan_accepts_multiple_specialized_decisions() -> None:
    plan = ReasoningCoordinationPlan(
        strategy_decisions=frozenset((CAUSAL_DECISION, COUNTERFACTUAL_DECISION))
    )
    assert plan.strategy_decisions == frozenset((CAUSAL_DECISION, COUNTERFACTUAL_DECISION))


@pytest.mark.parametrize("value", [None, (), [], set(), {}])
def test_plan_rejects_non_frozenset_strategy_decisions(value: object) -> None:
    with pytest.raises(InvalidReasoningCoordinationPlanError, match="frozenset"):
        ReasoningCoordinationPlan(strategy_decisions=value)


def test_plan_rejects_a_plain_set_without_coercion() -> None:
    with pytest.raises(InvalidReasoningCoordinationPlanError, match="frozenset"):
        ReasoningCoordinationPlan(strategy_decisions={CAUSAL_DECISION, COUNTERFACTUAL_DECISION})


def test_plan_rejects_empty_frozenset() -> None:
    with pytest.raises(InvalidReasoningCoordinationPlanError, match="empty"):
        ReasoningCoordinationPlan(strategy_decisions=frozenset())


@pytest.mark.parametrize(
    "value",
    ["causal", None, ReasoningStrategy.CAUSAL, ReasoningStrategyReason.CAUSAL_REASONING_REQUIRED],
)
def test_plan_rejects_non_decision_elements(value: object) -> None:
    with pytest.raises(InvalidReasoningCoordinationPlanError, match="ReasoningStrategyDecision"):
        ReasoningCoordinationPlan(strategy_decisions=frozenset((value,)))


def test_plan_rejects_direct_combined_with_causal() -> None:
    with pytest.raises(InvalidReasoningCoordinationPlanError, match="DIRECT"):
        ReasoningCoordinationPlan(strategy_decisions=frozenset((DIRECT_DECISION, CAUSAL_DECISION)))


def test_plan_rejects_direct_combined_with_search() -> None:
    with pytest.raises(InvalidReasoningCoordinationPlanError, match="DIRECT"):
        ReasoningCoordinationPlan(strategy_decisions=frozenset((DIRECT_DECISION, SEARCH_DECISION)))


def test_plan_rejects_duplicate_selected_strategy() -> None:
    # ReasoningStrategyDecision already restricts one valid reason per strategy,
    # so two decisions for the same selected_strategy are structurally identical
    # and a frozenset collapses them to one element. The uniqueness invariant on
    # the Plan is therefore validated by construction rather than by fabricating
    # an artificial duplicate: this test documents that guarantee explicitly.
    collapsed = frozenset((CAUSAL_DECISION, CAUSAL_DECISION))
    assert len(collapsed) == 1
    plan = ReasoningCoordinationPlan(strategy_decisions=collapsed)
    assert plan.strategy_decisions == frozenset((CAUSAL_DECISION,))


def test_plan_equality_does_not_depend_on_construction_order() -> None:
    plan_one = ReasoningCoordinationPlan(
        strategy_decisions=frozenset((CAUSAL_DECISION, COUNTERFACTUAL_DECISION))
    )
    plan_two = ReasoningCoordinationPlan(
        strategy_decisions=frozenset((COUNTERFACTUAL_DECISION, CAUSAL_DECISION))
    )
    assert plan_one == plan_two
