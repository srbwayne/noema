"""Structured reasons produced by cognitive hard gates."""

from enum import Enum


class CognitiveModeReason(Enum):
    """Semantic reason for a minimum cognitive mode."""

    NO_DETERMINISTIC_PATH = "no_deterministic_path"
    TOOLS_REQUIRED = "tools_required"
    EXTERNAL_INFORMATION_REQUIRED = "external_information_required"
    HIGH_RISK = "high_risk"
    HIGH_IMPACT = "high_impact"
    HIGH_CONFLICT = "high_conflict"
    LOW_REVERSIBILITY = "low_reversibility"
    DEEP_REASONING_REQUIRED = "deep_reasoning_required"
    HIGH_UNCERTAINTY_WITH_IMPACT = "high_uncertainty_with_impact"
    RISK_WITH_LOW_REVERSIBILITY = "risk_with_low_reversibility"
