"""Errors raised by context composition contracts."""

from noema.shared.domain import DomainError


class InvalidContextRequestError(DomainError):
    """Raised when a context request violates its invariants."""


class InvalidContextSliceError(DomainError):
    """Raised when a context slice violates its invariants."""
