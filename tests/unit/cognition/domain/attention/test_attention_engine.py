from dataclasses import FrozenInstanceError, replace
from uuid import uuid4

import pytest

from noema.cognition.domain.attention import (
    AttentionCandidate,
    AttentionDisposition,
    AttentionEngine,
    AttentionFactors,
    AttentionPolicy,
    AttentionPriority,
    AttentionWeights,
)


def policy() -> AttentionPolicy:
    return AttentionPolicy(
        weights=AttentionWeights(
            goal_relevance=1.0,
            urgency=0.0,
            novelty=0.0,
            risk=0.0,
            user_relevance=0.0,
            emotional_salience=1.0,
            temporal_relevance=0.0,
            repetition_penalty=1.0,
            noise_penalty=1.0,
            stale_penalty=1.0,
        ),
        buffer_threshold=0.25,
        activate_threshold=0.75,
    )


def factors(
    *,
    goal_relevance: float = 0.0,
    emotional_salience: float = 0.0,
    repetition_penalty: float = 0.0,
    noise_penalty: float = 0.0,
    stale_penalty: float = 0.0,
) -> AttentionFactors:
    return AttentionFactors(
        goal_relevance=goal_relevance,
        urgency=0.0,
        novelty=0.0,
        risk=0.0,
        user_relevance=0.0,
        emotional_salience=emotional_salience,
        temporal_relevance=0.0,
        repetition_penalty=repetition_penalty,
        noise_penalty=noise_penalty,
        stale_penalty=stale_penalty,
    )


def candidate(
    *,
    priority: AttentionPriority = AttentionPriority.P3_BACKGROUND,
    attention_factors: AttentionFactors | None = None,
) -> AttentionCandidate:
    return AttentionCandidate(
        event_id=uuid4(),
        priority=priority,
        factors=attention_factors or factors(),
    )


@pytest.mark.parametrize(
    ("attention_factors", "expected_score"),
    [
        (factors(), 0.0),
        (factors(goal_relevance=1.0, emotional_salience=1.0), 1.0),
        (factors(goal_relevance=0.8, emotional_salience=0.2), 0.5),
    ],
)
def test_attention_score_matches_weighted_formula(
    attention_factors: AttentionFactors,
    expected_score: float,
) -> None:
    decision = AttentionEngine(policy()).evaluate(candidate(attention_factors=attention_factors))

    assert decision.score == pytest.approx(expected_score)


def test_penalties_reduce_attention_score() -> None:
    engine = AttentionEngine(policy())
    unpenalized = engine.evaluate(
        candidate(attention_factors=factors(goal_relevance=0.8, emotional_salience=0.2))
    )
    penalized = engine.evaluate(
        candidate(
            attention_factors=factors(
                goal_relevance=0.8,
                emotional_salience=0.2,
                repetition_penalty=0.2,
            )
        )
    )

    assert penalized.score == pytest.approx(0.4)
    assert penalized.score < unpenalized.score


def test_negative_raw_score_is_clamped_to_zero() -> None:
    decision = AttentionEngine(policy()).evaluate(
        candidate(attention_factors=factors(noise_penalty=1.0))
    )

    assert decision.score == 0.0


def test_score_never_exceeds_one() -> None:
    high_penalty_policy = replace(
        policy(),
        weights=replace(policy().weights, repetition_penalty=10.0),
    )
    decision = AttentionEngine(high_penalty_policy).evaluate(
        candidate(
            attention_factors=factors(
                goal_relevance=1.0,
                emotional_salience=1.0,
            )
        )
    )

    assert 0.0 <= decision.score <= 1.0
    assert decision.score == 1.0


@pytest.mark.parametrize(
    ("priority", "attention_factors", "expected_disposition"),
    [
        (
            AttentionPriority.P0_CRITICAL,
            factors(),
            AttentionDisposition.INTERRUPT,
        ),
        (
            AttentionPriority.P1_DIRECT,
            factors(),
            AttentionDisposition.ACTIVATE,
        ),
        (
            AttentionPriority.P2_GOAL_RELEVANT,
            factors(),
            AttentionDisposition.BUFFER,
        ),
        (
            AttentionPriority.P2_GOAL_RELEVANT,
            factors(goal_relevance=1.0),
            AttentionDisposition.BUFFER,
        ),
        (
            AttentionPriority.P2_GOAL_RELEVANT,
            factors(goal_relevance=1.0, emotional_salience=1.0),
            AttentionDisposition.ACTIVATE,
        ),
        (
            AttentionPriority.P3_BACKGROUND,
            factors(),
            AttentionDisposition.IGNORE,
        ),
        (
            AttentionPriority.P3_BACKGROUND,
            factors(goal_relevance=1.0),
            AttentionDisposition.BUFFER,
        ),
        (
            AttentionPriority.P3_BACKGROUND,
            factors(goal_relevance=1.0, emotional_salience=1.0),
            AttentionDisposition.ACTIVATE,
        ),
        (
            AttentionPriority.P4_NOISE,
            factors(goal_relevance=1.0, emotional_salience=1.0),
            AttentionDisposition.IGNORE,
        ),
    ],
)
def test_attention_priority_and_threshold_rules(
    priority: AttentionPriority,
    attention_factors: AttentionFactors,
    expected_disposition: AttentionDisposition,
) -> None:
    decision = AttentionEngine(policy()).evaluate(
        candidate(priority=priority, attention_factors=attention_factors)
    )

    assert decision.disposition is expected_disposition


def test_emotional_salience_modulates_score() -> None:
    engine = AttentionEngine(policy())
    without_emotion = engine.evaluate(candidate(attention_factors=factors()))
    with_emotion = engine.evaluate(candidate(attention_factors=factors(emotional_salience=1.0)))

    assert without_emotion.score == 0.0
    assert with_emotion.score == pytest.approx(0.5)


def test_emotional_salience_does_not_override_noise_priority() -> None:
    decision = AttentionEngine(policy()).evaluate(
        candidate(
            priority=AttentionPriority.P4_NOISE,
            attention_factors=factors(
                goal_relevance=1.0,
                emotional_salience=1.0,
            ),
        )
    )

    assert decision.score == 1.0
    assert decision.disposition is AttentionDisposition.IGNORE


@pytest.mark.parametrize("emotional_salience", [0.0, 1.0])
def test_emotional_salience_does_not_override_critical_priority(
    emotional_salience: float,
) -> None:
    decision = AttentionEngine(policy()).evaluate(
        candidate(
            priority=AttentionPriority.P0_CRITICAL,
            attention_factors=factors(emotional_salience=emotional_salience),
        )
    )

    assert decision.disposition is AttentionDisposition.INTERRUPT


def test_evaluation_is_deterministic_and_traceable() -> None:
    engine = AttentionEngine(policy())
    current_candidate = candidate(
        priority=AttentionPriority.P3_BACKGROUND,
        attention_factors=factors(goal_relevance=0.8, emotional_salience=0.2),
    )

    first = engine.evaluate(current_candidate)
    second = engine.evaluate(current_candidate)

    assert first == second
    assert first.candidate_id == current_candidate.candidate_id
    assert first.event_id == current_candidate.event_id
    assert first.priority is current_candidate.priority


def test_attention_decision_is_immutable() -> None:
    decision = AttentionEngine(policy()).evaluate(candidate())

    with pytest.raises(FrozenInstanceError):
        decision.score = 1.0
