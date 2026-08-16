"""Errors raised by model selection contract invariants."""

from noema.shared.domain import DomainError


class InvalidModelSelectionRequestError(DomainError):
    """Raised when a model selection request violates its representation."""


class InvalidModelSelectionDecisionError(DomainError):
    """Raised when a model selection decision violates its representation."""
