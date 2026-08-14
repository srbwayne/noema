"""Immutable result of cognitive mode arbitration."""

from dataclasses import dataclass
from math import isfinite

from noema.cognition.domain.errors import InvalidCognitiveModeDecisionError
from noema.cognition.domain.mode_arbitration.cognitive_mode_reason import CognitiveModeReason
from noema.cognition.domain.modes import CognitiveMode


@dataclass(frozen=True, slots=True, kw_only=True)
class CognitiveModeDecision:
    """Hard floor, soft result, scores, and structured reasons."""

    selected_mode: CognitiveMode
    minimum_mode: CognitiveMode
    soft_mode: CognitiveMode
    intrinsic_score: float
    effective_score: float
    reasons: tuple[CognitiveModeReason, ...]

    def __post_init__(self) -> None:
        """Validate mode, score, and reason representation types."""
        modes = (
            ("selected_mode", self.selected_mode),
            ("minimum_mode", self.minimum_mode),
            ("soft_mode", self.soft_mode),
        )
        for name, mode_value in modes:
            if not isinstance(mode_value, CognitiveMode):
                raise InvalidCognitiveModeDecisionError(f"{name} must be a CognitiveMode")

        scores = (
            ("intrinsic_score", self.intrinsic_score),
            ("effective_score", self.effective_score),
        )
        for name, score_value in scores:
            if (
                not isinstance(score_value, float)
                or not isfinite(score_value)
                or not 0.0 <= score_value <= 1.0
            ):
                raise InvalidCognitiveModeDecisionError(
                    f"{name} must be a finite float between 0.0 and 1.0"
                )

        if not isinstance(self.reasons, tuple) or not all(
            isinstance(reason, CognitiveModeReason) for reason in self.reasons
        ):
            raise InvalidCognitiveModeDecisionError(
                "reasons must be a tuple of CognitiveModeReason values"
            )
        if len(self.reasons) != len(set(self.reasons)):
            raise InvalidCognitiveModeDecisionError("reasons must not contain duplicates")
