from enum import Enum, IntEnum, StrEnum

from noema.cognition.domain.reasoning import ReasoningStrategyReason


def test_reasoning_strategy_reason_has_exact_contract() -> None:
    assert tuple(ReasoningStrategyReason.__members__) == (
        "DIRECT_SUFFICIENT",
        "DECOMPOSITION_REQUIRED",
        "HYPOTHESIS_TESTING_REQUIRED",
        "CAUSAL_REASONING_REQUIRED",
        "COMPARISON_REQUIRED",
        "SEARCH_REQUIRED",
        "COUNTERFACTUAL_REQUIRED",
        "CRITIQUE_REQUIRED",
        "TOOL_ASSISTANCE_REQUIRED",
        "MULTI_MODEL_REQUIRED",
    )
    assert tuple(member.value for member in ReasoningStrategyReason) == (
        "direct_sufficient",
        "decomposition_required",
        "hypothesis_testing_required",
        "causal_reasoning_required",
        "comparison_required",
        "search_required",
        "counterfactual_required",
        "critique_required",
        "tool_assistance_required",
        "multi_model_required",
    )
    assert len(ReasoningStrategyReason) == 10
    assert issubclass(ReasoningStrategyReason, Enum)
    assert not issubclass(ReasoningStrategyReason, IntEnum)
    assert not issubclass(ReasoningStrategyReason, StrEnum)
    assert all(not isinstance(member.value, int) for member in ReasoningStrategyReason)
