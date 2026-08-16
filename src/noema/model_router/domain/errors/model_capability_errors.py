"""Errors raised by model resource capability contract invariants."""

from noema.shared.domain import DomainError


class InvalidModelResourceCapabilitiesError(DomainError):
    """Raised when a model resource capabilities set violates its representation."""
