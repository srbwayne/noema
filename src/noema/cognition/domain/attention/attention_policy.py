"""Immutable configuration for attention evaluation."""

from dataclasses import dataclass
from math import isfinite

from noema.cognition.domain.attention.attention_weights import AttentionWeights
from noema.cognition.domain.errors import InvalidAttentionPolicyError


@dataclass(frozen=True, slots=True, kw_only=True)
class AttentionPolicy:
    """Weights and thresholds governing deterministic attention."""

    weights: AttentionWeights
    buffer_threshold: float
    activate_threshold: float

    def __post_init__(self) -> None:
        """Validate finite, ordered thresholds within the normalized range."""
        thresholds = (
            ("buffer_threshold", self.buffer_threshold),
            ("activate_threshold", self.activate_threshold),
        )
        for name, value in thresholds:
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not isfinite(value)
                or not 0.0 <= value <= 1.0
            ):
                raise InvalidAttentionPolicyError(
                    f"{name} must be a finite number between 0.0 and 1.0"
                )
        if self.buffer_threshold >= self.activate_threshold:
            raise InvalidAttentionPolicyError(
                "buffer_threshold must be lower than activate_threshold"
            )
