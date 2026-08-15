from dataclasses import MISSING, FrozenInstanceError, fields

import pytest

from noema.cognition.domain.errors import InvalidReasoningStrategyDecisionError
from noema.cognition.domain.modes import CognitiveMode
from noema.cognition.domain.reasoning import (
    ReasoningStrategy,
    ReasoningStrategyDecision,
    ReasoningStrategyReason,
)

VALID_PAIRS = (
    (ReasoningStrategy.DIRECT, ReasoningStrategyReason.DIRECT_SUFFICIENT),
    (ReasoningStrategy.DECOMPOSITION, ReasoningStrategyReason.DECOMPOSITION_REQUIRED),
    (
        ReasoningStrategy.HYPOTHESIS_TESTING,
        ReasoningStrategyReason.HYPOTHESIS_TESTING_REQUIRED,
    ),
    (ReasoningStrategy.CAUSAL, ReasoningStrategyReason.CAUSAL_REASONING_REQUIRED),
    (ReasoningStrategy.COMPARATIVE, ReasoningStrategyReason.COMPARISON_REQUIRED),
    (ReasoningStrategy.SEARCH, ReasoningStrategyReason.SEARCH_REQUIRED),
    (
        ReasoningStrategy.COUNTERFACTUAL,
        ReasoningStrategyReason.COUNTERFACTUAL_REQUIRED,
    ),
    (ReasoningStrategy.CRITIQUE, ReasoningStrategyReason.CRITIQUE_REQUIRED),
    (
        ReasoningStrategy.TOOL_ASSISTED,
        ReasoningStrategyReason.TOOL_ASSISTANCE_REQUIRED,
    ),
    (ReasoningStrategy.MULTI_MODEL, ReasoningStrategyReason.MULTI_MODEL_REQUIRED),
)


def test_reasoning_strategy_decision_has_exact_required_fields() -> None:
    contract_fields = fields(ReasoningStrategyDecision)
    assert tuple(field.name for field in contract_fields) == ("selected_strategy", "reason")
    assert all(
        field.default is MISSING and field.default_factory is MISSING for field in contract_fields
    )


@pytest.mark.parametrize("strategy,reason", VALID_PAIRS)
def test_reasoning_strategy_decision_accepts_all_exact_correspondences(
    strategy: ReasoningStrategy,
    reason: ReasoningStrategyReason,
) -> None:
    decision = ReasoningStrategyDecision(selected_strategy=strategy, reason=reason)
    assert decision.selected_strategy is strategy
    assert decision.reason is reason


def test_each_strategy_accepts_exactly_one_reason() -> None:
    expected = dict(VALID_PAIRS)
    for strategy in ReasoningStrategy:
        for reason in ReasoningStrategyReason:
            if expected[strategy] is reason:
                ReasoningStrategyDecision(selected_strategy=strategy, reason=reason)
            else:
                with pytest.raises(InvalidReasoningStrategyDecisionError, match="incompatible"):
                    ReasoningStrategyDecision(selected_strategy=strategy, reason=reason)


@pytest.mark.parametrize("value", [None, "direct", 1, CognitiveMode.FAST])
def test_reasoning_strategy_decision_requires_reasoning_strategy(value: object) -> None:
    with pytest.raises(InvalidReasoningStrategyDecisionError, match="selected_strategy"):
        ReasoningStrategyDecision(
            selected_strategy=value,
            reason=ReasoningStrategyReason.DIRECT_SUFFICIENT,
        )


@pytest.mark.parametrize("value", [None, "direct_sufficient", 1, ReasoningStrategy.DIRECT])
def test_reasoning_strategy_decision_requires_reason(value: object) -> None:
    with pytest.raises(InvalidReasoningStrategyDecisionError, match="reason"):
        ReasoningStrategyDecision(selected_strategy=ReasoningStrategy.DIRECT, reason=value)


@pytest.mark.parametrize(
    "strategy,reason",
    [
        (ReasoningStrategy.DIRECT, ReasoningStrategyReason.DECOMPOSITION_REQUIRED),
        (ReasoningStrategy.CAUSAL, ReasoningStrategyReason.SEARCH_REQUIRED),
        (ReasoningStrategy.MULTI_MODEL, ReasoningStrategyReason.TOOL_ASSISTANCE_REQUIRED),
    ],
)
def test_reasoning_strategy_decision_rejects_crossed_pairs(
    strategy: ReasoningStrategy,
    reason: ReasoningStrategyReason,
) -> None:
    with pytest.raises(InvalidReasoningStrategyDecisionError, match="incompatible"):
        ReasoningStrategyDecision(selected_strategy=strategy, reason=reason)


def test_reasoning_strategy_decision_is_frozen_slotted_keyword_only_and_equal() -> None:
    first = ReasoningStrategyDecision(
        selected_strategy=ReasoningStrategy.DIRECT,
        reason=ReasoningStrategyReason.DIRECT_SUFFICIENT,
    )
    second = ReasoningStrategyDecision(
        selected_strategy=ReasoningStrategy.DIRECT,
        reason=ReasoningStrategyReason.DIRECT_SUFFICIENT,
    )
    assert first == second
    assert not hasattr(first, "__dict__")
    with pytest.raises(FrozenInstanceError):
        first.reason = ReasoningStrategyReason.SEARCH_REQUIRED
    with pytest.raises(TypeError):
        ReasoningStrategyDecision(
            ReasoningStrategy.DIRECT, ReasoningStrategyReason.DIRECT_SUFFICIENT
        )
