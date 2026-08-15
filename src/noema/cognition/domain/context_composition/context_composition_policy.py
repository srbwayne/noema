"""Guardrails for future context composition."""

from dataclasses import dataclass
from math import isfinite

from noema.cognition.domain.errors import InvalidContextCompositionPolicyError


@dataclass(frozen=True, slots=True, kw_only=True)
class ContextCompositionPolicy:
    """Declare explicit structural limits for context composition."""

    minimum_relevance: float
    max_slices: int

    def __post_init__(self) -> None:
        """Validate policy limits without applying composition behavior."""
        if (
            not isinstance(self.minimum_relevance, float)
            or not isfinite(self.minimum_relevance)
            or not 0.0 <= self.minimum_relevance <= 1.0
        ):
            raise InvalidContextCompositionPolicyError(
                "minimum_relevance must be a finite float between 0.0 and 1.0"
            )
        if (
            isinstance(self.max_slices, bool)
            or not isinstance(self.max_slices, int)
            or self.max_slices <= 0
        ):
            raise InvalidContextCompositionPolicyError("max_slices must be a positive int")
