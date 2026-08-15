"""Explicit requirements for selecting one reasoning strategy."""

from dataclasses import dataclass

from noema.cognition.domain.errors import InvalidReasoningStrategyDemandError

_REQUIREMENT_FIELDS = (
    "requires_decomposition",
    "requires_hypothesis_testing",
    "requires_causal_reasoning",
    "requires_comparison",
    "requires_search",
    "requires_counterfactual",
    "requires_critique",
    "requires_tool_assistance",
    "requires_multi_model",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ReasoningStrategyDemand:
    """Declare already-identified reasoning strategy requirements."""

    requires_decomposition: bool
    requires_hypothesis_testing: bool
    requires_causal_reasoning: bool
    requires_comparison: bool
    requires_search: bool
    requires_counterfactual: bool
    requires_critique: bool
    requires_tool_assistance: bool
    requires_multi_model: bool

    def __post_init__(self) -> None:
        """Require strict booleans without rejecting multiple requirements."""
        for field_name in _REQUIREMENT_FIELDS:
            if not isinstance(getattr(self, field_name), bool):
                raise InvalidReasoningStrategyDemandError(f"{field_name} must be a bool")
