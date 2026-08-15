"""Stateless coordination of the reasoning strategies a demand requires."""

from noema.cognition.domain.errors import InvalidReasoningStrategyDemandError

from ._reasoning_strategy_requirements import specialized_strategy_decisions
from .reasoning_coordination_plan import ReasoningCoordinationPlan
from .reasoning_strategy import ReasoningStrategy
from .reasoning_strategy_decision import ReasoningStrategyDecision
from .reasoning_strategy_demand import ReasoningStrategyDemand
from .reasoning_strategy_reason import ReasoningStrategyReason


class ReasoningCoordinator:
    """Preserve every specialized strategy a demand requires, without ordering."""

    __slots__ = ()

    def coordinate(self, demand: ReasoningStrategyDemand) -> ReasoningCoordinationPlan:
        """Return a plan composing all required strategies, never a single winner."""
        if not isinstance(demand, ReasoningStrategyDemand):
            raise InvalidReasoningStrategyDemandError("demand must be a ReasoningStrategyDemand")

        matches = specialized_strategy_decisions(demand)
        if not matches:
            matches = (
                ReasoningStrategyDecision(
                    selected_strategy=ReasoningStrategy.DIRECT,
                    reason=ReasoningStrategyReason.DIRECT_SUFFICIENT,
                ),
            )

        return ReasoningCoordinationPlan(strategy_decisions=frozenset(matches))
