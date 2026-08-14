"""Immutable policy for cognitive mode arbitration."""

from dataclasses import dataclass
from math import isfinite

from noema.cognition.domain.errors import InvalidCognitiveModePolicyError
from noema.cognition.domain.mode_arbitration.cognitive_demand_weights import (
    CognitiveDemandWeights,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class CognitiveModePolicy:
    """Weights and explicit soft and hard arbitration thresholds."""

    weights: CognitiveDemandWeights
    fast_threshold: float
    deliberate_threshold: float
    deep_threshold: float
    deliberate_risk_threshold: float
    deep_risk_threshold: float
    deliberate_impact_threshold: float
    deep_impact_threshold: float
    deep_uncertainty_threshold: float
    deliberate_conflict_threshold: float
    low_reversibility_threshold: float

    def __post_init__(self) -> None:
        """Validate policy types, normalized thresholds, and ordering."""
        if not isinstance(self.weights, CognitiveDemandWeights):
            raise InvalidCognitiveModePolicyError("weights must be CognitiveDemandWeights")

        thresholds = (
            ("fast_threshold", self.fast_threshold),
            ("deliberate_threshold", self.deliberate_threshold),
            ("deep_threshold", self.deep_threshold),
            ("deliberate_risk_threshold", self.deliberate_risk_threshold),
            ("deep_risk_threshold", self.deep_risk_threshold),
            ("deliberate_impact_threshold", self.deliberate_impact_threshold),
            ("deep_impact_threshold", self.deep_impact_threshold),
            ("deep_uncertainty_threshold", self.deep_uncertainty_threshold),
            ("deliberate_conflict_threshold", self.deliberate_conflict_threshold),
            ("low_reversibility_threshold", self.low_reversibility_threshold),
        )
        for name, value in thresholds:
            if not isinstance(value, float) or not isfinite(value) or not 0.0 <= value <= 1.0:
                raise InvalidCognitiveModePolicyError(
                    f"{name} must be a finite float between 0.0 and 1.0"
                )

        if not self.fast_threshold < self.deliberate_threshold < self.deep_threshold:
            raise InvalidCognitiveModePolicyError(
                "soft thresholds must satisfy fast < deliberate < deep"
            )
        if self.deliberate_risk_threshold >= self.deep_risk_threshold:
            raise InvalidCognitiveModePolicyError(
                "deliberate_risk_threshold must be lower than deep_risk_threshold"
            )
        if self.deliberate_impact_threshold >= self.deep_impact_threshold:
            raise InvalidCognitiveModePolicyError(
                "deliberate_impact_threshold must be lower than deep_impact_threshold"
            )
