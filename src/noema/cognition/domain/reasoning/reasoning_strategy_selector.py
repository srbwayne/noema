"""Deterministic selection of one reasoning strategy from explicit demand."""

from noema.cognition.domain.errors import (
    AmbiguousReasoningStrategyError,
    InvalidReasoningStrategyDemandError,
)

from .reasoning_strategy import ReasoningStrategy
from .reasoning_strategy_decision import ReasoningStrategyDecision
from .reasoning_strategy_demand import ReasoningStrategyDemand
from .reasoning_strategy_reason import ReasoningStrategyReason

_REQUIREMENTS = (
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
    ("requires_critique", ReasoningStrategy.CRITIQUE, ReasoningStrategyReason.CRITIQUE_REQUIRED),
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


class ReasoningStrategySelector:
    """Select one strategy only when explicit requirements are unambiguous."""

    __slots__ = ()

    def select(self, demand: ReasoningStrategyDemand) -> ReasoningStrategyDecision:
        """Return DIRECT, a one-hot strategy, or reject ambiguous demand."""
        if not isinstance(demand, ReasoningStrategyDemand):
            raise InvalidReasoningStrategyDemandError("demand must be a ReasoningStrategyDemand")

        matches = tuple(
            (strategy, reason)
            for field_name, strategy, reason in _REQUIREMENTS
            if getattr(demand, field_name)
        )
        if not matches:
            return ReasoningStrategyDecision(
                selected_strategy=ReasoningStrategy.DIRECT,
                reason=ReasoningStrategyReason.DIRECT_SUFFICIENT,
            )
        if len(matches) > 1:
            raise AmbiguousReasoningStrategyError(
                "multiple specialized reasoning strategies are required"
            )

        strategy, reason = matches[0]
        return ReasoningStrategyDecision(selected_strategy=strategy, reason=reason)
