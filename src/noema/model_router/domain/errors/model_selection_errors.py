"""Errors raised by model selection contract invariants."""

from noema.shared.domain import DomainError


class InvalidModelSelectionRequestError(DomainError):
    """Raised when a model selection request violates its representation."""


class InvalidModelSelectionDecisionError(DomainError):
    """Raised when a model selection decision violates its representation."""


class NoEligibleModelResourceError(DomainError):
    """Raised when no model resource candidate satisfies the selection requirements."""


class AmbiguousModelSelectionError(DomainError):
    """Raised when multiple model resource candidates satisfy the selection requirements."""
