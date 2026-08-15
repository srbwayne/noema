from enum import Enum, IntEnum, StrEnum

from noema.cognition.domain.reasoning import ReasoningStrategy


def test_reasoning_strategy_has_exact_contract() -> None:
    assert tuple(ReasoningStrategy.__members__) == (
        "DIRECT",
        "DECOMPOSITION",
        "HYPOTHESIS_TESTING",
        "CAUSAL",
        "COMPARATIVE",
        "SEARCH",
        "COUNTERFACTUAL",
        "CRITIQUE",
        "TOOL_ASSISTED",
        "MULTI_MODEL",
    )
    assert tuple(member.value for member in ReasoningStrategy) == (
        "direct",
        "decomposition",
        "hypothesis_testing",
        "causal",
        "comparative",
        "search",
        "counterfactual",
        "critique",
        "tool_assisted",
        "multi_model",
    )
    assert len(ReasoningStrategy) == 10
    assert issubclass(ReasoningStrategy, Enum)
    assert not issubclass(ReasoningStrategy, IntEnum)
    assert not issubclass(ReasoningStrategy, StrEnum)
    assert all(not isinstance(member.value, int) for member in ReasoningStrategy)
