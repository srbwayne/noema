"""Errors raised by reasoning contract invariants."""

from noema.shared.domain import DomainError


class AmbiguousReasoningStrategyError(DomainError):
    """Raised when single-strategy selection would discard requirements."""


class InvalidInformationNeedError(DomainError):
    """Raised when an information need violates its representation."""


class InvalidReasoningRequestError(DomainError):
    """Raised when a reasoning request violates its representation."""


class InvalidReasoningOutcomeError(DomainError):
    """Raised when a reasoning outcome violates its representation."""


class InvalidReasoningStrategyDecisionError(DomainError):
    """Raised when a strategy decision violates its representation."""


class InvalidReasoningStrategyDemandError(DomainError):
    """Raised when a strategy demand violates its representation."""
