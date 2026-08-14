"""Errors raised by situation domain invariants."""

from noema.shared.domain import DomainError


class InvalidSituationEntryError(DomainError):
    """Raised when a situation entry is invalid."""


class InvalidSituationDeltaError(DomainError):
    """Raised when a situation delta is structurally ambiguous or invalid."""


class InvalidSituationStateError(DomainError):
    """Raised when a situation snapshot is internally inconsistent."""


class DuplicateSituationEntryError(DomainError):
    """Raised when situation entry identifiers are duplicated."""


class SituationEntryNotFoundError(DomainError):
    """Raised when a delta references an entry absent from the situation."""


class SituationEntryKindMismatchError(DomainError):
    """Raised when an operation violates an entry's semantic kind."""


class StaleSituationDeltaError(DomainError):
    """Raised when a delta targets a different situation version."""
