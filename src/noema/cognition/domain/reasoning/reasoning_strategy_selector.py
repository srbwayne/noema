"""Deterministic selection of one reasoning strategy from explicit demand."""

from noema.cognition.domain.errors import (
    AmbiguousReasoningStrategyError,
    InvalidReasoningStrategyDemandError,
)

from ._reasoning_strategy_requirements import specialized_strategy_decisions
from .reasoning_strategy import ReasoningStrategy
from .reasoning_strategy_decision import ReasoningStrategyDecision
from .reasoning_strategy_demand import ReasoningStrategyDemand
from .reasoning_strategy_reason import ReasoningStrategyReason


class ReasoningStrategySelector:
    """Select one strategy only when explicit requirements are unambiguous."""

    __slots__ = ()

    def select(self, demand: ReasoningStrategyDemand) -> ReasoningStrategyDecision:
        """Return DIRECT, a one-hot strategy, or reject ambiguous demand."""
        if not isinstance(demand, ReasoningStrategyDemand):
            raise InvalidReasoningStrategyDemandError("demand must be a ReasoningStrategyDemand")

        matches = specialized_strategy_decisions(demand)
        if not matches:
            return ReasoningStrategyDecision(
                selected_strategy=ReasoningStrategy.DIRECT,
                reason=ReasoningStrategyReason.DIRECT_SUFFICIENT,
            )
        if len(matches) > 1:
            raise AmbiguousReasoningStrategyError(
                "multiple specialized reasoning strategies are required"
            )

        return matches[0]
