"""Errors raised by cognitive workspace invariants."""

from noema.shared.domain import DomainError


class InvalidCognitiveItemError(DomainError):
    """Raised when a cognitive item violates its invariants."""


class InvalidWorkspaceBudgetError(DomainError):
    """Raised when workspace capacity limits are invalid."""


class InvalidWorkspaceStateError(DomainError):
    """Raised when a workspace snapshot is internally inconsistent."""


class DuplicateCognitiveItemError(DomainError):
    """Raised when a workspace contains a duplicate item identifier."""


class WorkspaceCapacityExceededError(DomainError):
    """Raised when an item would exceed its region capacity."""


class CognitiveItemNotFoundError(DomainError):
    """Raised when a requested item is absent from the workspace."""


class InvalidWorkspaceFocusError(DomainError):
    """Raised when an item cannot be the workspace focus."""
