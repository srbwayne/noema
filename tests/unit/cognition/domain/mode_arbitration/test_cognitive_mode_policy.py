from dataclasses import FrozenInstanceError, replace
from math import inf, nan

import pytest

from noema.cognition.domain.errors import InvalidCognitiveModePolicyError
from noema.cognition.domain.mode_arbitration import (
    CognitiveDemandWeights,
    CognitiveModePolicy,
)

THRESHOLD_NAMES = (
    "fast_threshold",
    "deliberate_threshold",
    "deep_threshold",
    "deliberate_risk_threshold",
    "deep_risk_threshold",
    "deliberate_impact_threshold",
    "deep_impact_threshold",
    "deep_uncertainty_threshold",
    "deliberate_conflict_threshold",
    "low_reversibility_threshold",
)


def weights() -> CognitiveDemandWeights:
    return CognitiveDemandWeights(
        complexity=1.0,
        novelty=0.0,
        uncertainty=0.0,
        risk=0.0,
        user_impact=0.0,
        environment_impact=0.0,
        irreversibility=0.0,
        unfamiliarity=0.0,
        low_confidence=0.0,
        low_evidence_quality=0.0,
        conflict=0.0,
        time_pressure_penalty=0.0,
        budget_pressure_penalty=0.0,
    )


def policy() -> CognitiveModePolicy:
    return CognitiveModePolicy(
        weights=weights(),
        fast_threshold=0.25,
        deliberate_threshold=0.5,
        deep_threshold=0.75,
        deliberate_risk_threshold=0.6,
        deep_risk_threshold=0.9,
        deliberate_impact_threshold=0.6,
        deep_impact_threshold=0.9,
        deep_uncertainty_threshold=0.8,
        deliberate_conflict_threshold=0.6,
        low_reversibility_threshold=0.2,
    )


def test_policy_accepts_soft_threshold_boundaries() -> None:
    current = replace(
        policy(),
        fast_threshold=0.0,
        deliberate_threshold=0.5,
        deep_threshold=1.0,
    )

    assert current.fast_threshold == 0.0
    assert current.deep_threshold == 1.0


@pytest.mark.parametrize("field_name", THRESHOLD_NAMES)
@pytest.mark.parametrize("value", [-0.01, 1.01, nan, inf, -inf, True, False, 0, 1, None])
def test_policy_rejects_invalid_threshold_values(
    field_name: str,
    value: object,
) -> None:
    with pytest.raises(InvalidCognitiveModePolicyError, match=field_name):
        replace(policy(), **{field_name: value})


@pytest.mark.parametrize(
    ("fast", "deliberate", "deep"),
    [(0.5, 0.5, 0.8), (0.6, 0.5, 0.8), (0.2, 0.8, 0.8), (0.2, 0.9, 0.8)],
)
def test_policy_rejects_unordered_soft_thresholds(
    fast: float,
    deliberate: float,
    deep: float,
) -> None:
    with pytest.raises(InvalidCognitiveModePolicyError, match="soft thresholds"):
        replace(
            policy(),
            fast_threshold=fast,
            deliberate_threshold=deliberate,
            deep_threshold=deep,
        )


@pytest.mark.parametrize(("deliberate", "deep"), [(0.8, 0.8), (0.9, 0.8)])
def test_policy_rejects_unordered_risk_thresholds(
    deliberate: float,
    deep: float,
) -> None:
    with pytest.raises(InvalidCognitiveModePolicyError, match="risk"):
        replace(
            policy(),
            deliberate_risk_threshold=deliberate,
            deep_risk_threshold=deep,
        )


@pytest.mark.parametrize(("deliberate", "deep"), [(0.8, 0.8), (0.9, 0.8)])
def test_policy_rejects_unordered_impact_thresholds(
    deliberate: float,
    deep: float,
) -> None:
    with pytest.raises(InvalidCognitiveModePolicyError, match="impact"):
        replace(
            policy(),
            deliberate_impact_threshold=deliberate,
            deep_impact_threshold=deep,
        )


def test_policy_rejects_invalid_weights_type() -> None:
    with pytest.raises(InvalidCognitiveModePolicyError, match="weights"):
        replace(policy(), weights="weights")


def test_policy_is_immutable() -> None:
    with pytest.raises(FrozenInstanceError):
        policy().fast_threshold = 0.1
