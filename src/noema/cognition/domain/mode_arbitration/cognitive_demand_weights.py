"""Weights for deterministic cognitive demand scoring."""

from dataclasses import dataclass
from math import isfinite

from noema.cognition.domain.errors import InvalidCognitiveDemandWeightsError


@dataclass(frozen=True, slots=True, kw_only=True)
class CognitiveDemandWeights:
    """Non-negative weights for demand signals and pressure penalties."""

    complexity: float
    novelty: float
    uncertainty: float
    risk: float
    user_impact: float
    environment_impact: float
    irreversibility: float
    unfamiliarity: float
    low_confidence: float
    low_evidence_quality: float
    conflict: float
    time_pressure_penalty: float
    budget_pressure_penalty: float

    def __post_init__(self) -> None:
        """Validate strict finite floats and positive signal configuration."""
        weights = (
            ("complexity", self.complexity),
            ("novelty", self.novelty),
            ("uncertainty", self.uncertainty),
            ("risk", self.risk),
            ("user_impact", self.user_impact),
            ("environment_impact", self.environment_impact),
            ("irreversibility", self.irreversibility),
            ("unfamiliarity", self.unfamiliarity),
            ("low_confidence", self.low_confidence),
            ("low_evidence_quality", self.low_evidence_quality),
            ("conflict", self.conflict),
            ("time_pressure_penalty", self.time_pressure_penalty),
            ("budget_pressure_penalty", self.budget_pressure_penalty),
        )
        for name, value in weights:
            if not isinstance(value, float) or not isfinite(value) or value < 0.0:
                raise InvalidCognitiveDemandWeightsError(
                    f"{name} must be a finite non-negative float"
                )

        if not any(weight > 0.0 for weight in self._positive_weights):
            raise InvalidCognitiveDemandWeightsError(
                "at least one positive demand signal must have a positive weight"
            )

    @property
    def _positive_weights(self) -> tuple[float, ...]:
        """Return positive signal weights in score formula order."""
        return (
            self.complexity,
            self.novelty,
            self.uncertainty,
            self.risk,
            self.user_impact,
            self.environment_impact,
            self.irreversibility,
            self.unfamiliarity,
            self.low_confidence,
            self.low_evidence_quality,
            self.conflict,
        )
