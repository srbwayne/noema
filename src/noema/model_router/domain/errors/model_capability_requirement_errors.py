"""Errors raised by model capability requirement contract invariants."""

from noema.shared.domain import DomainError


class InvalidModelCapabilityRequirementsError(DomainError):
    """Raised when a model capability requirements set violates its representation."""
