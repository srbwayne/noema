"""A bounded composition of the reasoning strategies a demand requires."""

from dataclasses import dataclass

from noema.cognition.domain.errors import InvalidReasoningCoordinationPlanError

from .reasoning_strategy import ReasoningStrategy
from .reasoning_strategy_decision import ReasoningStrategyDecision


@dataclass(frozen=True, slots=True, kw_only=True)
class ReasoningCoordinationPlan:
    """Represent which strategies are required, never in what order.

    ``strategy_decisions`` is a frozenset because this plan expresses
    cognitive composition, not execution order. It carries no sequence,
    stage, priority, or precedence between the strategies it contains.
    """

    strategy_decisions: frozenset[ReasoningStrategyDecision]

    def __post_init__(self) -> None:
        """Validate strict frozenset membership, non-emptiness, and DIRECT exclusivity."""
        if type(self.strategy_decisions) is not frozenset:
            raise InvalidReasoningCoordinationPlanError("strategy_decisions must be a frozenset")
        if not self.strategy_decisions:
            raise InvalidReasoningCoordinationPlanError("strategy_decisions must not be empty")
        for decision in self.strategy_decisions:
            if not isinstance(decision, ReasoningStrategyDecision):
                raise InvalidReasoningCoordinationPlanError(
                    "strategy_decisions must contain only ReasoningStrategyDecision"
                )

        selected_strategies = tuple(
            decision.selected_strategy for decision in self.strategy_decisions
        )
        if len(set(selected_strategies)) != len(selected_strategies):
            raise InvalidReasoningCoordinationPlanError(
                "strategy_decisions must not repeat a selected_strategy"
            )

        if ReasoningStrategy.DIRECT in selected_strategies and len(selected_strategies) != 1:
            raise InvalidReasoningCoordinationPlanError(
                "DIRECT must be the only decision when present"
            )
