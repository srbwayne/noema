"""Errors raised by model resource contract invariants."""

from noema.shared.domain import DomainError


class InvalidModelResourceError(DomainError):
    """Raised when a model resource violates its representation."""
