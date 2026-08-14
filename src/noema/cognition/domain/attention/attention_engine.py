"""Deterministic and side-effect-free attention evaluation."""

from dataclasses import dataclass

from noema.cognition.domain.attention.attention_candidate import AttentionCandidate
from noema.cognition.domain.attention.attention_decision import AttentionDecision
from noema.cognition.domain.attention.attention_disposition import AttentionDisposition
from noema.cognition.domain.attention.attention_policy import AttentionPolicy
from noema.cognition.domain.attention.attention_priority import AttentionPriority


@dataclass(frozen=True, slots=True)
class AttentionEngine:
    """Stateless domain service applying soft score and hard priority rules."""

    policy: AttentionPolicy

    def evaluate(self, candidate: AttentionCandidate) -> AttentionDecision:
        """Evaluate a candidate without changing it or external state."""
        score = self._calculate_score(candidate)
        disposition = self._disposition(candidate.priority, score)
        return AttentionDecision(
            candidate_id=candidate.candidate_id,
            event_id=candidate.event_id,
            priority=candidate.priority,
            score=score,
            disposition=disposition,
        )

    def _calculate_score(self, candidate: AttentionCandidate) -> float:
        factors = candidate.factors
        weights = self.policy.weights

        positive_weight_sum = (
            weights.goal_relevance
            + weights.urgency
            + weights.novelty
            + weights.risk
            + weights.user_relevance
            + weights.emotional_salience
            + weights.temporal_relevance
        )
        positive_signal = (
            factors.goal_relevance * weights.goal_relevance
            + factors.urgency * weights.urgency
            + factors.novelty * weights.novelty
            + factors.risk * weights.risk
            + factors.user_relevance * weights.user_relevance
            + factors.emotional_salience * weights.emotional_salience
            + factors.temporal_relevance * weights.temporal_relevance
        )
        penalty_signal = (
            factors.repetition_penalty * weights.repetition_penalty
            + factors.noise_penalty * weights.noise_penalty
            + factors.stale_penalty * weights.stale_penalty
        )
        raw_score = (positive_signal - penalty_signal) / positive_weight_sum
        return min(max(raw_score, 0.0), 1.0)

    def _disposition(
        self,
        priority: AttentionPriority,
        score: float,
    ) -> AttentionDisposition:
        if priority is AttentionPriority.P0_CRITICAL:
            return AttentionDisposition.INTERRUPT
        if priority is AttentionPriority.P1_DIRECT:
            return AttentionDisposition.ACTIVATE
        if priority is AttentionPriority.P2_GOAL_RELEVANT:
            if score >= self.policy.activate_threshold:
                return AttentionDisposition.ACTIVATE
            return AttentionDisposition.BUFFER
        if priority is AttentionPriority.P3_BACKGROUND:
            if score >= self.policy.activate_threshold:
                return AttentionDisposition.ACTIVATE
            if score >= self.policy.buffer_threshold:
                return AttentionDisposition.BUFFER
            return AttentionDisposition.IGNORE
        return AttentionDisposition.IGNORE
