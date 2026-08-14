"""Errors raised by cognitive mode arbitration invariants."""

from noema.shared.domain import DomainError


class InvalidCognitiveDemandError(DomainError):
    """Raised when cognitive demand signals or requirements are invalid."""


class InvalidCognitiveDemandWeightsError(DomainError):
    """Raised when cognitive demand scoring weights are invalid."""


class InvalidCognitiveModePolicyError(DomainError):
    """Raised when cognitive mode policy thresholds are invalid."""


class InvalidCognitiveModeDecisionError(DomainError):
    """Raised when a cognitive mode decision violates its representation."""
