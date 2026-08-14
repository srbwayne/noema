"""Errors raised by cognitive processing budget invariants."""

from noema.shared.domain import DomainError


class InvalidCognitiveBudgetError(DomainError):
    """Raised when a cognitive resource limit is invalid."""
