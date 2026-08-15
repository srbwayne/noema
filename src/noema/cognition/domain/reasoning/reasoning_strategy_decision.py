"""A validated single-strategy reasoning decision."""

from dataclasses import dataclass

from noema.cognition.domain.errors import InvalidReasoningStrategyDecisionError

from .reasoning_strategy import ReasoningStrategy
from .reasoning_strategy_reason import ReasoningStrategyReason

_VALID_STRATEGY_REASONS = (
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


@dataclass(frozen=True, slots=True, kw_only=True)
class ReasoningStrategyDecision:
    """Pair one strategy with its exact structured selection reason."""

    selected_strategy: ReasoningStrategy
    reason: ReasoningStrategyReason

    def __post_init__(self) -> None:
        """Validate strict types and their semantic correspondence."""
        if not isinstance(self.selected_strategy, ReasoningStrategy):
            raise InvalidReasoningStrategyDecisionError(
                "selected_strategy must be a ReasoningStrategy"
            )
        if not isinstance(self.reason, ReasoningStrategyReason):
            raise InvalidReasoningStrategyDecisionError("reason must be a ReasoningStrategyReason")
        if (self.selected_strategy, self.reason) not in _VALID_STRATEGY_REASONS:
            raise InvalidReasoningStrategyDecisionError(
                "selected_strategy and reason are semantically incompatible"
            )
