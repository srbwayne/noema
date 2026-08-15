"""A context slice available for future composition."""

from dataclasses import dataclass
from datetime import timedelta
from math import isfinite

from noema.cognition.domain.errors import InvalidContextCandidateError

from .context_slice import ContextSlice


@dataclass(frozen=True, slots=True, kw_only=True)
class ContextCandidate:
    """Associate a projectable slice with explicit selection signals."""

    context_slice: ContextSlice
    relevance: float
    age: timedelta | None

    def __post_init__(self) -> None:
        """Validate candidate metadata without deriving or coercing values."""
        if not isinstance(self.context_slice, ContextSlice):
            raise InvalidContextCandidateError("context_slice must be a ContextSlice")
        if (
            not isinstance(self.relevance, float)
            or not isfinite(self.relevance)
            or not 0.0 <= self.relevance <= 1.0
        ):
            raise InvalidContextCandidateError(
                "relevance must be a finite float between 0.0 and 1.0"
            )
        if self.age is not None and (
            not isinstance(self.age, timedelta) or self.age < timedelta(0)
        ):
            raise InvalidContextCandidateError("age must be None or a non-negative timedelta")
