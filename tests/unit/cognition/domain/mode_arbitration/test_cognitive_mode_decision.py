from dataclasses import FrozenInstanceError, replace
from math import inf, nan

import pytest

from noema.cognition.domain.errors import InvalidCognitiveModeDecisionError
from noema.cognition.domain.mode_arbitration import (
    CognitiveModeDecision,
    CognitiveModeReason,
)
from noema.cognition.domain.modes import CognitiveMode


def decision() -> CognitiveModeDecision:
    return CognitiveModeDecision(
        selected_mode=CognitiveMode.DELIBERATE,
        minimum_mode=CognitiveMode.FAST,
        soft_mode=CognitiveMode.DELIBERATE,
        intrinsic_score=0.6,
        effective_score=0.5,
        reasons=(CognitiveModeReason.NO_DETERMINISTIC_PATH,),
    )


@pytest.mark.parametrize("field_name", ["selected_mode", "minimum_mode", "soft_mode"])
def test_decision_rejects_invalid_mode_types(field_name: str) -> None:
    with pytest.raises(InvalidCognitiveModeDecisionError, match=field_name):
        replace(decision(), **{field_name: "fast"})


@pytest.mark.parametrize("field_name", ["intrinsic_score", "effective_score"])
@pytest.mark.parametrize("value", [-0.01, 1.01, nan, inf, -inf, True, 0, None])
def test_decision_rejects_invalid_scores(field_name: str, value: object) -> None:
    with pytest.raises(InvalidCognitiveModeDecisionError, match=field_name):
        replace(decision(), **{field_name: value})


def test_decision_rejects_invalid_or_duplicate_reasons() -> None:
    with pytest.raises(InvalidCognitiveModeDecisionError, match="tuple"):
        replace(decision(), reasons=("high_risk",))

    reason = CognitiveModeReason.HIGH_RISK
    with pytest.raises(InvalidCognitiveModeDecisionError, match="duplicates"):
        replace(decision(), reasons=(reason, reason))


def test_decision_is_immutable() -> None:
    with pytest.raises(FrozenInstanceError):
        decision().selected_mode = CognitiveMode.DEEP
