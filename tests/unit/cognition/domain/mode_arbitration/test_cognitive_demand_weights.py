from dataclasses import FrozenInstanceError, replace
from math import inf, nan

import pytest

from noema.cognition.domain.errors import InvalidCognitiveDemandWeightsError
from noema.cognition.domain.mode_arbitration import CognitiveDemandWeights

POSITIVE_WEIGHT_NAMES = (
    "complexity",
    "novelty",
    "uncertainty",
    "risk",
    "user_impact",
    "environment_impact",
    "irreversibility",
    "unfamiliarity",
    "low_confidence",
    "low_evidence_quality",
    "conflict",
)
WEIGHT_NAMES = POSITIVE_WEIGHT_NAMES + (
    "time_pressure_penalty",
    "budget_pressure_penalty",
)


def weights() -> CognitiveDemandWeights:
    return CognitiveDemandWeights(
        complexity=1.0,
        novelty=1.0,
        uncertainty=1.0,
        risk=1.0,
        user_impact=1.0,
        environment_impact=1.0,
        irreversibility=1.0,
        unfamiliarity=1.0,
        low_confidence=1.0,
        low_evidence_quality=1.0,
        conflict=1.0,
        time_pressure_penalty=0.0,
        budget_pressure_penalty=0.0,
    )


@pytest.mark.parametrize("field_name", WEIGHT_NAMES)
@pytest.mark.parametrize("value", [0.0, 0.5, 2.0])
def test_demand_weights_accept_non_negative_float_values(
    field_name: str,
    value: float,
) -> None:
    current = replace(weights(), **{field_name: value})

    assert getattr(current, field_name) == value


@pytest.mark.parametrize("field_name", WEIGHT_NAMES)
@pytest.mark.parametrize("value", [-0.01, nan, inf, -inf, True, False, 0, 1, None])
def test_demand_weights_reject_invalid_values(
    field_name: str,
    value: object,
) -> None:
    with pytest.raises(InvalidCognitiveDemandWeightsError, match=field_name):
        replace(weights(), **{field_name: value})


def test_demand_weights_require_one_positive_signal_weight() -> None:
    zero_positive_weights = {field_name: 0.0 for field_name in POSITIVE_WEIGHT_NAMES}

    with pytest.raises(InvalidCognitiveDemandWeightsError, match="at least one"):
        replace(weights(), **zero_positive_weights)


def test_demand_weights_allow_zero_penalties() -> None:
    current = weights()

    assert current.time_pressure_penalty == 0.0
    assert current.budget_pressure_penalty == 0.0


def test_demand_weights_are_immutable() -> None:
    with pytest.raises(FrozenInstanceError):
        weights().complexity = 2.0
