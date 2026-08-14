"""Normalized signals used by the attention score."""

from dataclasses import dataclass
from math import isfinite

from noema.cognition.domain.errors import InvalidAttentionFactorError


@dataclass(frozen=True, slots=True, kw_only=True)
class AttentionFactors:
    """Explicit positive signals and penalties for one candidate."""

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
        """Require every normalized factor to be finite and within [0, 1]."""
        factors = (
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
        for name, value in factors:
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not isfinite(value)
                or not 0.0 <= value <= 1.0
            ):
                raise InvalidAttentionFactorError(
                    f"{name} must be a finite number between 0.0 and 1.0"
                )
