from enum import Enum, IntEnum

from noema.cognition.domain.mode_arbitration import CognitiveModeReason


def test_cognitive_mode_reason_has_exactly_the_hard_gate_reasons() -> None:
    assert tuple(CognitiveModeReason.__members__) == (
        "NO_DETERMINISTIC_PATH",
        "TOOLS_REQUIRED",
        "EXTERNAL_INFORMATION_REQUIRED",
        "HIGH_RISK",
        "HIGH_IMPACT",
        "HIGH_CONFLICT",
        "LOW_REVERSIBILITY",
        "DEEP_REASONING_REQUIRED",
        "HIGH_UNCERTAINTY_WITH_IMPACT",
        "RISK_WITH_LOW_REVERSIBILITY",
    )


def test_cognitive_mode_reason_uses_semantic_non_numeric_values() -> None:
    assert issubclass(CognitiveModeReason, Enum)
    assert not issubclass(CognitiveModeReason, IntEnum)
    assert tuple(reason.value for reason in CognitiveModeReason) == (
        "no_deterministic_path",
        "tools_required",
        "external_information_required",
        "high_risk",
        "high_impact",
        "high_conflict",
        "low_reversibility",
        "deep_reasoning_required",
        "high_uncertainty_with_impact",
        "risk_with_low_reversibility",
    )
    assert all(not isinstance(reason.value, int) for reason in CognitiveModeReason)
