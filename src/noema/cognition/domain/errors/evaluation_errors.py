"""Errors raised by evaluation contract invariants."""

from noema.shared.domain import DomainError


class InvalidEvaluationRequestError(DomainError):
    """Raised when an evaluation request violates its representation."""
