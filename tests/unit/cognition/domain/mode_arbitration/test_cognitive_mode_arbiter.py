from dataclasses import replace

import pytest

from noema.cognition.domain.errors import InvalidCognitiveDemandError
from noema.cognition.domain.mode_arbitration import (
    CognitiveDemand,
    CognitiveDemandWeights,
    CognitiveModeArbiter,
    CognitiveModePolicy,
    CognitiveModeReason,
)
from noema.cognition.domain.modes import CognitiveMode


def weights(
    *,
    complexity: float = 1.0,
    novelty: float = 0.0,
    uncertainty: float = 0.0,
    risk: float = 0.0,
    user_impact: float = 0.0,
    environment_impact: float = 0.0,
    irreversibility: float = 0.0,
    unfamiliarity: float = 0.0,
    low_confidence: float = 0.0,
    low_evidence_quality: float = 0.0,
    conflict: float = 0.0,
    time_pressure_penalty: float = 0.0,
    budget_pressure_penalty: float = 0.0,
) -> CognitiveDemandWeights:
    return CognitiveDemandWeights(
        complexity=complexity,
        novelty=novelty,
        uncertainty=uncertainty,
        risk=risk,
        user_impact=user_impact,
        environment_impact=environment_impact,
        irreversibility=irreversibility,
        unfamiliarity=unfamiliarity,
        low_confidence=low_confidence,
        low_evidence_quality=low_evidence_quality,
        conflict=conflict,
        time_pressure_penalty=time_pressure_penalty,
        budget_pressure_penalty=budget_pressure_penalty,
    )


def policy(*, demand_weights: CognitiveDemandWeights | None = None) -> CognitiveModePolicy:
    return CognitiveModePolicy(
        weights=demand_weights or weights(),
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


def demand() -> CognitiveDemand:
    return CognitiveDemand(
        complexity=0.0,
        novelty=0.0,
        uncertainty=0.0,
        risk=0.0,
        user_impact=0.0,
        environment_impact=0.0,
        reversibility=1.0,
        familiarity=1.0,
        confidence=1.0,
        evidence_quality=1.0,
        conflict=0.0,
        time_pressure=0.0,
        budget_pressure=0.0,
        deterministic_path_available=True,
        requires_tools=False,
        requires_external_information=False,
        requires_deep_reasoning=False,
    )


def evaluate(
    current: CognitiveDemand,
    *,
    mode_policy: CognitiveModePolicy | None = None,
):
    return CognitiveModeArbiter(mode_policy or policy()).evaluate(current)


def test_zero_and_maximum_positive_signals_produce_zero_and_one_scores() -> None:
    low = evaluate(demand())
    high = evaluate(
        replace(
            demand(),
            complexity=1.0,
        )
    )

    assert low.intrinsic_score == 0.0
    assert low.effective_score == 0.0
    assert high.intrinsic_score == 1.0
    assert high.effective_score == 1.0


@pytest.mark.parametrize(
    ("weight_name", "demand_changes"),
    [
        ("irreversibility", {"reversibility": 0.0}),
        ("unfamiliarity", {"familiarity": 0.0}),
        ("low_confidence", {"confidence": 0.0}),
        ("low_evidence_quality", {"evidence_quality": 0.0}),
    ],
)
def test_inverse_signals_are_scored_correctly(
    weight_name: str,
    demand_changes: dict[str, float],
) -> None:
    weight_values = {
        "complexity": 0.0,
        weight_name: 1.0,
    }
    current_weights = weights(**weight_values)

    result = evaluate(
        replace(demand(), **demand_changes),
        mode_policy=policy(demand_weights=current_weights),
    )

    assert result.intrinsic_score == 1.0
    assert result.effective_score == 1.0


def test_all_positive_signals_at_maximum_produce_score_one() -> None:
    all_signal_weights = CognitiveDemandWeights(
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
    maximum = replace(
        demand(),
        complexity=1.0,
        novelty=1.0,
        uncertainty=1.0,
        risk=1.0,
        user_impact=1.0,
        environment_impact=1.0,
        reversibility=0.0,
        familiarity=0.0,
        confidence=0.0,
        evidence_quality=0.0,
        conflict=1.0,
    )

    result = evaluate(maximum, mode_policy=policy(demand_weights=all_signal_weights))

    assert result.intrinsic_score == 1.0
    assert result.effective_score == 1.0


@pytest.mark.parametrize(
    ("penalty_name", "pressure_name"),
    [
        ("time_pressure_penalty", "time_pressure"),
        ("budget_pressure_penalty", "budget_pressure"),
    ],
)
def test_each_pressure_reduces_effective_score(
    penalty_name: str,
    pressure_name: str,
) -> None:
    penalty_weights = replace(weights(), **{penalty_name: 0.5})
    pressured_demand = replace(
        demand(),
        complexity=0.8,
        **{pressure_name: 0.4},
    )

    result = evaluate(
        pressured_demand,
        mode_policy=policy(demand_weights=penalty_weights),
    )

    assert result.intrinsic_score == pytest.approx(0.8)
    assert result.effective_score == pytest.approx(0.6)


def test_pressure_penalties_reduce_only_effective_score() -> None:
    current_policy = policy(
        demand_weights=weights(
            time_pressure_penalty=0.5,
            budget_pressure_penalty=0.5,
        )
    )
    result = evaluate(
        replace(
            demand(),
            complexity=0.8,
            time_pressure=0.2,
            budget_pressure=0.2,
        ),
        mode_policy=current_policy,
    )

    assert result.intrinsic_score == pytest.approx(0.8)
    assert result.effective_score == pytest.approx(0.6)


def test_penalties_are_clamped_at_zero() -> None:
    current_policy = policy(
        demand_weights=weights(
            time_pressure_penalty=2.0,
            budget_pressure_penalty=2.0,
        )
    )
    result = evaluate(
        replace(demand(), complexity=0.1, time_pressure=1.0, budget_pressure=1.0),
        mode_policy=current_policy,
    )

    assert result.intrinsic_score == pytest.approx(0.1)
    assert result.effective_score == 0.0


@pytest.mark.parametrize(
    ("score", "expected_mode"),
    [
        (0.24, CognitiveMode.REFLEX),
        (0.25, CognitiveMode.FAST),
        (0.5, CognitiveMode.DELIBERATE),
        (0.75, CognitiveMode.DEEP),
    ],
)
def test_soft_mode_threshold_boundaries(
    score: float,
    expected_mode: CognitiveMode,
) -> None:
    result = evaluate(replace(demand(), complexity=score))

    assert result.soft_mode is expected_mode


@pytest.mark.parametrize(
    ("changes", "mode", "reason"),
    [
        (
            {"deterministic_path_available": False},
            CognitiveMode.FAST,
            CognitiveModeReason.NO_DETERMINISTIC_PATH,
        ),
        (
            {"requires_tools": True},
            CognitiveMode.DELIBERATE,
            CognitiveModeReason.TOOLS_REQUIRED,
        ),
        (
            {"requires_external_information": True},
            CognitiveMode.DELIBERATE,
            CognitiveModeReason.EXTERNAL_INFORMATION_REQUIRED,
        ),
        ({"risk": 0.6}, CognitiveMode.DELIBERATE, CognitiveModeReason.HIGH_RISK),
        ({"risk": 0.9}, CognitiveMode.DEEP, CognitiveModeReason.HIGH_RISK),
        (
            {"user_impact": 0.6},
            CognitiveMode.DELIBERATE,
            CognitiveModeReason.HIGH_IMPACT,
        ),
        ({"environment_impact": 0.9}, CognitiveMode.DEEP, CognitiveModeReason.HIGH_IMPACT),
        (
            {"conflict": 0.6},
            CognitiveMode.DELIBERATE,
            CognitiveModeReason.HIGH_CONFLICT,
        ),
        (
            {"reversibility": 0.2},
            CognitiveMode.DELIBERATE,
            CognitiveModeReason.LOW_REVERSIBILITY,
        ),
        (
            {"requires_deep_reasoning": True},
            CognitiveMode.DEEP,
            CognitiveModeReason.DEEP_REASONING_REQUIRED,
        ),
    ],
)
def test_individual_hard_gates(
    changes: dict[str, bool | float],
    mode: CognitiveMode,
    reason: CognitiveModeReason,
) -> None:
    result = evaluate(replace(demand(), **changes))

    assert result.minimum_mode is mode
    assert reason in result.reasons


def test_impact_uses_maximum_instead_of_sum() -> None:
    result = evaluate(replace(demand(), user_impact=0.4, environment_impact=0.4))

    assert result.minimum_mode is CognitiveMode.REFLEX
    assert CognitiveModeReason.HIGH_IMPACT not in result.reasons


def test_uncertainty_with_meaningful_impact_requires_deep() -> None:
    result = evaluate(replace(demand(), uncertainty=0.8, user_impact=0.6))

    assert result.minimum_mode is CognitiveMode.DEEP
    assert CognitiveModeReason.HIGH_UNCERTAINTY_WITH_IMPACT in result.reasons


def test_risk_with_low_reversibility_requires_deep() -> None:
    result = evaluate(replace(demand(), risk=0.6, reversibility=0.2))

    assert result.minimum_mode is CognitiveMode.DEEP
    assert result.reasons == (
        CognitiveModeReason.HIGH_RISK,
        CognitiveModeReason.LOW_REVERSIBILITY,
        CognitiveModeReason.RISK_WITH_LOW_REVERSIBILITY,
    )


def test_hard_floor_overrides_shallower_soft_mode() -> None:
    deliberate = evaluate(replace(demand(), requires_tools=True))
    deep = evaluate(replace(demand(), requires_deep_reasoning=True))

    assert deliberate.soft_mode is CognitiveMode.REFLEX
    assert deliberate.minimum_mode is CognitiveMode.DELIBERATE
    assert deliberate.selected_mode is CognitiveMode.DELIBERATE
    assert deep.soft_mode is CognitiveMode.REFLEX
    assert deep.selected_mode is CognitiveMode.DEEP


def test_soft_mode_can_be_deeper_than_hard_floor() -> None:
    result = evaluate(replace(demand(), complexity=0.6, deterministic_path_available=False))

    assert result.minimum_mode is CognitiveMode.FAST
    assert result.soft_mode is CognitiveMode.DELIBERATE
    assert result.selected_mode is CognitiveMode.DELIBERATE


def test_explicit_precedence_selects_deeper_mode_without_enum_values() -> None:
    hard_deeper = evaluate(replace(demand(), complexity=0.3, requires_tools=True))
    soft_deeper = evaluate(replace(demand(), complexity=0.8, deterministic_path_available=False))

    assert hard_deeper.minimum_mode is CognitiveMode.DELIBERATE
    assert hard_deeper.soft_mode is CognitiveMode.FAST
    assert hard_deeper.selected_mode is CognitiveMode.DELIBERATE
    assert soft_deeper.minimum_mode is CognitiveMode.FAST
    assert soft_deeper.soft_mode is CognitiveMode.DEEP
    assert soft_deeper.selected_mode is CognitiveMode.DEEP


def test_multiple_hard_gate_reasons_are_complete_unique_and_deterministic() -> None:
    result = evaluate(replace(demand(), requires_tools=True, risk=0.6, reversibility=0.2))

    assert result.reasons == (
        CognitiveModeReason.TOOLS_REQUIRED,
        CognitiveModeReason.HIGH_RISK,
        CognitiveModeReason.LOW_REVERSIBILITY,
        CognitiveModeReason.RISK_WITH_LOW_REVERSIBILITY,
    )
    assert len(result.reasons) == len(set(result.reasons))


def test_pressure_cannot_defeat_deep_hard_gate() -> None:
    current_policy = policy(
        demand_weights=weights(
            time_pressure_penalty=10.0,
            budget_pressure_penalty=10.0,
        )
    )
    result = evaluate(
        replace(
            demand(),
            time_pressure=1.0,
            budget_pressure=1.0,
            requires_deep_reasoning=True,
        ),
        mode_policy=current_policy,
    )

    assert result.effective_score == 0.0
    assert result.minimum_mode is CognitiveMode.DEEP
    assert result.selected_mode is CognitiveMode.DEEP


def test_evaluation_is_deterministic() -> None:
    arbiter = CognitiveModeArbiter(policy())
    current = replace(demand(), complexity=0.55, requires_tools=True)

    assert arbiter.evaluate(current) == arbiter.evaluate(current)


def test_arbiter_rejects_invalid_demand_type() -> None:
    with pytest.raises(InvalidCognitiveDemandError, match="demand"):
        CognitiveModeArbiter(policy()).evaluate("demand")
