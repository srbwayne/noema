from dataclasses import FrozenInstanceError, replace
from math import inf, nan

import pytest

from noema.cognition.domain.errors import InvalidCognitiveDemandError
from noema.cognition.domain.mode_arbitration import CognitiveDemand

SIGNAL_NAMES = (
    "complexity",
    "novelty",
    "uncertainty",
    "risk",
    "user_impact",
    "environment_impact",
    "reversibility",
    "familiarity",
    "confidence",
    "evidence_quality",
    "conflict",
    "time_pressure",
    "budget_pressure",
)
REQUIREMENT_NAMES = (
    "deterministic_path_available",
    "requires_tools",
    "requires_external_information",
    "requires_deep_reasoning",
)


def demand() -> CognitiveDemand:
    return CognitiveDemand(
        complexity=0.5,
        novelty=0.5,
        uncertainty=0.5,
        risk=0.5,
        user_impact=0.5,
        environment_impact=0.5,
        reversibility=0.5,
        familiarity=0.5,
        confidence=0.5,
        evidence_quality=0.5,
        conflict=0.5,
        time_pressure=0.5,
        budget_pressure=0.5,
        deterministic_path_available=True,
        requires_tools=False,
        requires_external_information=False,
        requires_deep_reasoning=False,
    )


@pytest.mark.parametrize("field_name", SIGNAL_NAMES)
@pytest.mark.parametrize("value", [0.0, 0.5, 1.0])
def test_cognitive_demand_accepts_normalized_float_signals(
    field_name: str,
    value: float,
) -> None:
    current = replace(demand(), **{field_name: value})

    assert getattr(current, field_name) == value


@pytest.mark.parametrize("field_name", SIGNAL_NAMES)
@pytest.mark.parametrize("value", [-0.01, 1.01, nan, inf, -inf, True, False, 0, 1, None])
def test_cognitive_demand_rejects_invalid_signals(
    field_name: str,
    value: object,
) -> None:
    with pytest.raises(InvalidCognitiveDemandError, match=field_name):
        replace(demand(), **{field_name: value})


@pytest.mark.parametrize("field_name", REQUIREMENT_NAMES)
@pytest.mark.parametrize("value", [True, False])
def test_cognitive_demand_accepts_boolean_requirements(
    field_name: str,
    value: bool,
) -> None:
    current = replace(demand(), **{field_name: value})

    assert getattr(current, field_name) is value


@pytest.mark.parametrize("field_name", REQUIREMENT_NAMES)
@pytest.mark.parametrize("value", [0, 1, "true", None])
def test_cognitive_demand_rejects_invalid_boolean_requirements(
    field_name: str,
    value: object,
) -> None:
    with pytest.raises(InvalidCognitiveDemandError, match=field_name):
        replace(demand(), **{field_name: value})


def test_cognitive_demand_is_immutable() -> None:
    with pytest.raises(FrozenInstanceError):
        demand().complexity = 0.8
