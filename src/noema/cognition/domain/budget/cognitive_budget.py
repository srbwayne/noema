"""Maximum resource limits for a cognitive operation."""

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from noema.cognition.domain.errors import InvalidCognitiveBudgetError


@dataclass(frozen=True, slots=True, kw_only=True)
class CognitiveBudget:
    """Immutable upper bounds for one cognitive operation."""

    max_time: timedelta
    max_steps: int
    max_llm_calls: int
    max_tool_calls: int
    max_cost: Decimal
    max_tokens: int
    max_search_depth: int

    def __post_init__(self) -> None:
        """Validate every resource limit without coercion."""
        if not isinstance(self.max_time, timedelta) or self.max_time <= timedelta(0):
            raise InvalidCognitiveBudgetError("max_time must be a positive timedelta")

        self._validate_integer_limit("max_steps", self.max_steps, positive=True)
        self._validate_integer_limit("max_llm_calls", self.max_llm_calls)
        self._validate_integer_limit("max_tool_calls", self.max_tool_calls)
        self._validate_integer_limit("max_tokens", self.max_tokens)
        self._validate_integer_limit("max_search_depth", self.max_search_depth)

        if (
            not isinstance(self.max_cost, Decimal)
            or not self.max_cost.is_finite()
            or self.max_cost < Decimal("0")
        ):
            raise InvalidCognitiveBudgetError("max_cost must be a finite non-negative Decimal")

    @staticmethod
    def _validate_integer_limit(name: str, value: int, *, positive: bool = False) -> None:
        minimum = 1 if positive else 0
        if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
            requirement = "positive" if positive else "non-negative"
            raise InvalidCognitiveBudgetError(f"{name} must be a {requirement} integer")
