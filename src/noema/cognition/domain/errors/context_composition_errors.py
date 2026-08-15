"""Errors raised by context composition contracts."""

from noema.shared.domain import DomainError


class ContextCompositionUnsatisfiedError(DomainError):
    """Raised when valid composition inputs cannot satisfy a request."""


class InvalidContextCandidateError(DomainError):
    """Raised when a context candidate violates its invariants."""


class InvalidContextComposerError(DomainError):
    """Raised when a context composer receives invalid inputs."""


class InvalidContextCompositionPolicyError(DomainError):
    """Raised when a context composition policy violates its invariants."""


class InvalidContextPackageError(DomainError):
    """Raised when a context package violates its invariants."""


class InvalidContextRequestError(DomainError):
    """Raised when a context request violates its invariants."""


class InvalidContextSliceError(DomainError):
    """Raised when a context slice violates its invariants."""
