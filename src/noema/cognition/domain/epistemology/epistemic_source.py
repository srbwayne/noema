"""Minimal immutable provenance for an epistemic claim."""

from dataclasses import dataclass

from noema.cognition.domain.epistemology.epistemic_source_type import EpistemicSourceType
from noema.cognition.domain.errors import InvalidEpistemicSourceError


@dataclass(frozen=True, slots=True, kw_only=True)
class EpistemicSource:
    """Opaque reference to the origin of a claim."""

    source_type: EpistemicSourceType
    source_ref: str

    def __post_init__(self) -> None:
        """Require a non-empty opaque source reference."""
        if not isinstance(self.source_ref, str) or not self.source_ref.strip():
            raise InvalidEpistemicSourceError("source_ref must not be empty")
