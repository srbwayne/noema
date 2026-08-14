"""Errors raised by epistemic domain invariants."""

from noema.shared.domain import DomainError


class InvalidEpistemicSourceError(DomainError):
    """Raised when epistemic provenance is invalid."""


class InvalidEpistemicClaimError(DomainError):
    """Raised when an epistemic claim violates its invariants."""


class InvalidEpistemicDeltaError(DomainError):
    """Raised when an epistemic delta is structurally invalid."""


class InvalidEpistemicStateError(DomainError):
    """Raised when an epistemic snapshot is internally inconsistent."""


class DuplicateEpistemicClaimError(DomainError):
    """Raised when epistemic claim identifiers are duplicated."""


class EpistemicClaimNotFoundError(DomainError):
    """Raised when a delta references a claim absent from the model."""


class EpistemicClaimImmutableFieldError(DomainError):
    """Raised when an update changes an immutable claim field."""


class StaleEpistemicDeltaError(DomainError):
    """Raised when a delta targets a different epistemic version."""


class InvalidEpistemicConflictError(DomainError):
    """Raised when explicit claim conflicts are inconsistent."""
