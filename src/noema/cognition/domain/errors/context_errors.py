"""Context-related cognition domain errors."""

from noema.shared.domain import DomainError


class InvalidContextVersionError(DomainError):
    """Raised when a context version is negative."""
