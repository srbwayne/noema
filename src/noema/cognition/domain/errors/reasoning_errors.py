"""Errors raised by reasoning contract invariants."""

from noema.shared.domain import DomainError


class InvalidInformationNeedError(DomainError):
    """Raised when an information need violates its representation."""


class InvalidReasoningRequestError(DomainError):
    """Raised when a reasoning request violates its representation."""


class InvalidReasoningOutcomeError(DomainError):
    """Raised when a reasoning outcome violates its representation."""
