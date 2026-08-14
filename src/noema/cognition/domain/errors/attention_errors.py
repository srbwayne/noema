"""Errors raised by attention domain invariants."""

from noema.shared.domain import DomainError


class InvalidAttentionFactorError(DomainError):
    """Raised when a normalized attention factor is invalid."""


class InvalidAttentionWeightsError(DomainError):
    """Raised when attention weights cannot produce a valid score."""


class InvalidAttentionPolicyError(DomainError):
    """Raised when attention thresholds are invalid."""
