"""Errors raised by planning contract invariants."""

from noema.shared.domain import DomainError


class InvalidPlanningRequestError(DomainError):
    """Raised when a planning request violates its representation."""


class InvalidPlanStepError(DomainError):
    """Raised when a plan step violates its representation."""


class InvalidPlanError(DomainError):
    """Raised when a plan violates its representation."""
