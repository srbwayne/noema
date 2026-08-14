"""Normalized signals describing cognitive demand."""

from dataclasses import dataclass
from math import isfinite

from noema.cognition.domain.errors import InvalidCognitiveDemandError


@dataclass(frozen=True, slots=True, kw_only=True)
class CognitiveDemand:
    """Explicit signals and requirements for initial mode selection."""

    complexity: float
    novelty: float
    uncertainty: float
    risk: float
    user_impact: float
    environment_impact: float
    reversibility: float
    familiarity: float
    confidence: float
    evidence_quality: float
    conflict: float
    time_pressure: float
    budget_pressure: float
    deterministic_path_available: bool
    requires_tools: bool
    requires_external_information: bool
    requires_deep_reasoning: bool

    def __post_init__(self) -> None:
        """Validate normalized signals and strict boolean requirements."""
        signals = (
            ("complexity", self.complexity),
            ("novelty", self.novelty),
            ("uncertainty", self.uncertainty),
            ("risk", self.risk),
            ("user_impact", self.user_impact),
            ("environment_impact", self.environment_impact),
            ("reversibility", self.reversibility),
            ("familiarity", self.familiarity),
            ("confidence", self.confidence),
            ("evidence_quality", self.evidence_quality),
            ("conflict", self.conflict),
            ("time_pressure", self.time_pressure),
            ("budget_pressure", self.budget_pressure),
        )
        for name, value in signals:
            if not isinstance(value, float) or not isfinite(value) or not 0.0 <= value <= 1.0:
                raise InvalidCognitiveDemandError(
                    f"{name} must be a finite float between 0.0 and 1.0"
                )

        requirements = (
            ("deterministic_path_available", self.deterministic_path_available),
            ("requires_tools", self.requires_tools),
            ("requires_external_information", self.requires_external_information),
            ("requires_deep_reasoning", self.requires_deep_reasoning),
        )
        for name, value in requirements:
            if not isinstance(value, bool):
                raise InvalidCognitiveDemandError(f"{name} must be a bool")
