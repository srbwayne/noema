"""Deterministic initial cognitive mode arbitration."""

from dataclasses import dataclass

from noema.cognition.domain.errors import (
    InvalidCognitiveDemandError,
    InvalidCognitiveModePolicyError,
)
from noema.cognition.domain.mode_arbitration.cognitive_demand import CognitiveDemand
from noema.cognition.domain.mode_arbitration.cognitive_mode_decision import (
    CognitiveModeDecision,
)
from noema.cognition.domain.mode_arbitration.cognitive_mode_policy import CognitiveModePolicy
from noema.cognition.domain.mode_arbitration.cognitive_mode_reason import CognitiveModeReason
from noema.cognition.domain.modes import CognitiveMode

_MODE_PRECEDENCE = (
    CognitiveMode.REFLEX,
    CognitiveMode.FAST,
    CognitiveMode.DELIBERATE,
    CognitiveMode.DEEP,
)


@dataclass(frozen=True, slots=True)
class CognitiveModeArbiter:
    """Stateless service combining hard floors with deterministic soft scoring."""

    policy: CognitiveModePolicy

    def __post_init__(self) -> None:
        """Require an explicit cognitive mode policy."""
        if not isinstance(self.policy, CognitiveModePolicy):
            raise InvalidCognitiveModePolicyError("policy must be a CognitiveModePolicy")

    def evaluate(self, demand: CognitiveDemand) -> CognitiveModeDecision:
        """Select the least deep mode satisfying hard and soft requirements."""
        if not isinstance(demand, CognitiveDemand):
            raise InvalidCognitiveDemandError("demand must be a CognitiveDemand")

        minimum_mode, reasons = self._hard_floor(demand)
        intrinsic_score, effective_score = self._scores(demand)
        soft_mode = self._soft_mode(effective_score)
        selected_mode = self._deeper(minimum_mode, soft_mode)
        return CognitiveModeDecision(
            selected_mode=selected_mode,
            minimum_mode=minimum_mode,
            soft_mode=soft_mode,
            intrinsic_score=intrinsic_score,
            effective_score=effective_score,
            reasons=reasons,
        )

    def _hard_floor(
        self,
        demand: CognitiveDemand,
    ) -> tuple[CognitiveMode, tuple[CognitiveModeReason, ...]]:
        policy = self.policy
        impact = max(demand.user_impact, demand.environment_impact)
        reasons: list[CognitiveModeReason] = []
        minimum_mode = CognitiveMode.REFLEX

        def require(mode: CognitiveMode, reason: CognitiveModeReason) -> None:
            nonlocal minimum_mode
            minimum_mode = self._deeper(minimum_mode, mode)
            if reason not in reasons:
                reasons.append(reason)

        if not demand.deterministic_path_available:
            require(CognitiveMode.FAST, CognitiveModeReason.NO_DETERMINISTIC_PATH)
        if demand.requires_tools:
            require(CognitiveMode.DELIBERATE, CognitiveModeReason.TOOLS_REQUIRED)
        if demand.requires_external_information:
            require(
                CognitiveMode.DELIBERATE,
                CognitiveModeReason.EXTERNAL_INFORMATION_REQUIRED,
            )
        if demand.risk >= policy.deliberate_risk_threshold:
            risk_mode = (
                CognitiveMode.DEEP
                if demand.risk >= policy.deep_risk_threshold
                else CognitiveMode.DELIBERATE
            )
            require(risk_mode, CognitiveModeReason.HIGH_RISK)
        if impact >= policy.deliberate_impact_threshold:
            impact_mode = (
                CognitiveMode.DEEP
                if impact >= policy.deep_impact_threshold
                else CognitiveMode.DELIBERATE
            )
            require(impact_mode, CognitiveModeReason.HIGH_IMPACT)
        if demand.conflict >= policy.deliberate_conflict_threshold:
            require(CognitiveMode.DELIBERATE, CognitiveModeReason.HIGH_CONFLICT)
        if demand.reversibility <= policy.low_reversibility_threshold:
            require(CognitiveMode.DELIBERATE, CognitiveModeReason.LOW_REVERSIBILITY)
        if demand.requires_deep_reasoning:
            require(CognitiveMode.DEEP, CognitiveModeReason.DEEP_REASONING_REQUIRED)
        if (
            demand.uncertainty >= policy.deep_uncertainty_threshold
            and impact >= policy.deliberate_impact_threshold
        ):
            require(
                CognitiveMode.DEEP,
                CognitiveModeReason.HIGH_UNCERTAINTY_WITH_IMPACT,
            )
        if (
            demand.risk >= policy.deliberate_risk_threshold
            and demand.reversibility <= policy.low_reversibility_threshold
        ):
            require(
                CognitiveMode.DEEP,
                CognitiveModeReason.RISK_WITH_LOW_REVERSIBILITY,
            )

        return minimum_mode, tuple(reasons)

    def _scores(self, demand: CognitiveDemand) -> tuple[float, float]:
        weights = self.policy.weights
        positive_weight_sum = sum(weights._positive_weights)
        positive_signal = (
            demand.complexity * weights.complexity
            + demand.novelty * weights.novelty
            + demand.uncertainty * weights.uncertainty
            + demand.risk * weights.risk
            + demand.user_impact * weights.user_impact
            + demand.environment_impact * weights.environment_impact
            + (1.0 - demand.reversibility) * weights.irreversibility
            + (1.0 - demand.familiarity) * weights.unfamiliarity
            + (1.0 - demand.confidence) * weights.low_confidence
            + (1.0 - demand.evidence_quality) * weights.low_evidence_quality
            + demand.conflict * weights.conflict
        )
        penalty_signal = (
            demand.time_pressure * weights.time_pressure_penalty
            + demand.budget_pressure * weights.budget_pressure_penalty
        )
        intrinsic_score = positive_signal / positive_weight_sum
        effective_score = min(
            max((positive_signal - penalty_signal) / positive_weight_sum, 0.0),
            1.0,
        )
        return intrinsic_score, effective_score

    def _soft_mode(self, score: float) -> CognitiveMode:
        if score < self.policy.fast_threshold:
            return CognitiveMode.REFLEX
        if score < self.policy.deliberate_threshold:
            return CognitiveMode.FAST
        if score < self.policy.deep_threshold:
            return CognitiveMode.DELIBERATE
        return CognitiveMode.DEEP

    @staticmethod
    def _deeper(first: CognitiveMode, second: CognitiveMode) -> CognitiveMode:
        first_depth = _MODE_PRECEDENCE.index(first)
        second_depth = _MODE_PRECEDENCE.index(second)
        return first if first_depth >= second_depth else second
