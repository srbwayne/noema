from dataclasses import FrozenInstanceError, replace
from math import inf, nan

import pytest

from noema.cognition.domain.attention import AttentionFactors, AttentionPolicy, AttentionWeights
from noema.cognition.domain.errors import (
    InvalidAttentionFactorError,
    InvalidAttentionPolicyError,
    InvalidAttentionWeightsError,
)

FACTOR_NAMES = (
    "goal_relevance",
    "urgency",
    "novelty",
    "risk",
    "user_relevance",
    "emotional_salience",
    "temporal_relevance",
    "repetition_penalty",
    "noise_penalty",
    "stale_penalty",
)


def factors(value: float = 0.0) -> AttentionFactors:
    return AttentionFactors(
        goal_relevance=value,
        urgency=value,
        novelty=value,
        risk=value,
        user_relevance=value,
        emotional_salience=value,
        temporal_relevance=value,
        repetition_penalty=value,
        noise_penalty=value,
        stale_penalty=value,
    )


def weights() -> AttentionWeights:
    return AttentionWeights(
        goal_relevance=1.0,
        urgency=1.0,
        novelty=1.0,
        risk=1.0,
        user_relevance=1.0,
        emotional_salience=1.0,
        temporal_relevance=1.0,
        repetition_penalty=0.0,
        noise_penalty=0.0,
        stale_penalty=0.0,
    )


@pytest.mark.parametrize("value", [0.0, 1.0])
def test_attention_factors_accept_boundaries(value: float) -> None:
    assert factors(value).goal_relevance == value


@pytest.mark.parametrize("factor_name", FACTOR_NAMES)
@pytest.mark.parametrize("value", [-0.01, 1.01])
def test_each_attention_factor_rejects_out_of_range_value(
    factor_name: str,
    value: float,
) -> None:
    with pytest.raises(InvalidAttentionFactorError, match=factor_name):
        replace(factors(), **{factor_name: value})


@pytest.mark.parametrize("value", [nan, inf, -inf, True])
def test_attention_factor_rejects_non_finite_or_boolean_value(value: float) -> None:
    with pytest.raises(InvalidAttentionFactorError, match="urgency"):
        replace(factors(), urgency=value)


def test_attention_factors_are_immutable() -> None:
    current = factors()

    with pytest.raises(FrozenInstanceError):
        current.urgency = 1.0


def test_attention_weights_accept_zero_penalties_and_positive_signals() -> None:
    current = weights()

    assert current.goal_relevance == 1.0
    assert current.noise_penalty == 0.0


def test_attention_weights_allow_zero_for_individual_positive_weight() -> None:
    assert replace(weights(), novelty=0.0).novelty == 0.0


@pytest.mark.parametrize("value", [-0.01, nan, inf, -inf, True])
def test_attention_weights_reject_invalid_numeric_value(value: float) -> None:
    with pytest.raises(InvalidAttentionWeightsError, match="risk"):
        replace(weights(), risk=value)


def test_attention_weights_require_a_positive_signal_weight() -> None:
    with pytest.raises(InvalidAttentionWeightsError, match="at least one"):
        AttentionWeights(
            goal_relevance=0.0,
            urgency=0.0,
            novelty=0.0,
            risk=0.0,
            user_relevance=0.0,
            emotional_salience=0.0,
            temporal_relevance=0.0,
            repetition_penalty=1.0,
            noise_penalty=1.0,
            stale_penalty=1.0,
        )


def test_attention_weights_are_immutable() -> None:
    current = weights()

    with pytest.raises(FrozenInstanceError):
        current.goal_relevance = 0.0


@pytest.mark.parametrize(
    ("buffer_threshold", "activate_threshold"),
    [(0.0, 0.5), (0.5, 1.0)],
)
def test_attention_policy_accepts_valid_threshold_boundaries(
    buffer_threshold: float,
    activate_threshold: float,
) -> None:
    policy = AttentionPolicy(
        weights=weights(),
        buffer_threshold=buffer_threshold,
        activate_threshold=activate_threshold,
    )

    assert policy.buffer_threshold == buffer_threshold
    assert policy.activate_threshold == activate_threshold


@pytest.mark.parametrize(
    ("buffer_threshold", "activate_threshold"),
    [(0.5, 0.5), (0.6, 0.5), (-0.1, 0.5), (0.2, 1.1)],
)
def test_attention_policy_rejects_invalid_threshold_order_or_range(
    buffer_threshold: float,
    activate_threshold: float,
) -> None:
    with pytest.raises(InvalidAttentionPolicyError):
        AttentionPolicy(
            weights=weights(),
            buffer_threshold=buffer_threshold,
            activate_threshold=activate_threshold,
        )


@pytest.mark.parametrize("value", [nan, inf, -inf, True])
@pytest.mark.parametrize("threshold_name", ["buffer_threshold", "activate_threshold"])
def test_attention_policy_rejects_non_finite_or_boolean_threshold(
    threshold_name: str,
    value: float,
) -> None:
    policy = {
        "weights": weights(),
        "buffer_threshold": 0.3,
        "activate_threshold": 0.7,
    }
    policy[threshold_name] = value

    with pytest.raises(InvalidAttentionPolicyError, match=threshold_name):
        AttentionPolicy(**policy)


def test_attention_policy_is_immutable() -> None:
    policy = AttentionPolicy(
        weights=weights(),
        buffer_threshold=0.3,
        activate_threshold=0.7,
    )

    with pytest.raises(FrozenInstanceError):
        policy.buffer_threshold = 0.2
