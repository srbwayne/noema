"""Weights controlling composition of the attention score."""

from dataclasses import dataclass
from math import isfinite

from noema.cognition.domain.errors import InvalidAttentionWeightsError


@dataclass(frozen=True, slots=True, kw_only=True)
class AttentionWeights:
    """Non-negative weights for attention signals and penalties."""

    goal_relevance: float
    urgency: float
    novelty: float
    risk: float
    user_relevance: float
    emotional_salience: float
    temporal_relevance: float
    repetition_penalty: float
    noise_penalty: float
    stale_penalty: float

    def __post_init__(self) -> None:
        """Require finite weights and at least one positive signal weight."""
        weights = (
            ("goal_relevance", self.goal_relevance),
            ("urgency", self.urgency),
            ("novelty", self.novelty),
            ("risk", self.risk),
            ("user_relevance", self.user_relevance),
            ("emotional_salience", self.emotional_salience),
            ("temporal_relevance", self.temporal_relevance),
            ("repetition_penalty", self.repetition_penalty),
            ("noise_penalty", self.noise_penalty),
            ("stale_penalty", self.stale_penalty),
        )
        for name, value in weights:
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not isfinite(value)
                or value < 0.0
            ):
                raise InvalidAttentionWeightsError(f"{name} must be a finite non-negative number")

        positive_weights = (
            self.goal_relevance,
            self.urgency,
            self.novelty,
            self.risk,
            self.user_relevance,
            self.emotional_salience,
            self.temporal_relevance,
        )
        if not any(weight > 0.0 for weight in positive_weights):
            raise InvalidAttentionWeightsError(
                "at least one positive attention factor must have a positive weight"
            )
