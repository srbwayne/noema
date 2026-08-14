from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from noema.cognition.domain.attention import (
    AttentionCandidate,
    AttentionFactors,
    AttentionPriority,
)


def factors() -> AttentionFactors:
    return AttentionFactors(
        goal_relevance=0.0,
        urgency=0.0,
        novelty=0.0,
        risk=0.0,
        user_relevance=0.0,
        emotional_salience=0.0,
        temporal_relevance=0.0,
        repetition_penalty=0.0,
        noise_penalty=0.0,
        stale_penalty=0.0,
    )


def test_attention_candidate_has_automatic_distinct_id_and_event_reference() -> None:
    event_id = uuid4()
    first = AttentionCandidate(
        event_id=event_id,
        priority=AttentionPriority.P3_BACKGROUND,
        factors=factors(),
    )
    second = AttentionCandidate(
        event_id=event_id,
        priority=AttentionPriority.P3_BACKGROUND,
        factors=factors(),
    )

    assert first.candidate_id
    assert first.candidate_id != second.candidate_id
    assert first.event_id == event_id


def test_attention_candidate_is_immutable() -> None:
    candidate = AttentionCandidate(
        event_id=uuid4(),
        priority=AttentionPriority.P3_BACKGROUND,
        factors=factors(),
    )

    with pytest.raises(FrozenInstanceError):
        candidate.priority = AttentionPriority.P0_CRITICAL
