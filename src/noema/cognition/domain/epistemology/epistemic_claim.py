"""Immutable current epistemic representation of a claim."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from math import isfinite
from uuid import UUID, uuid4

from noema.cognition.domain.epistemology.epistemic_source import EpistemicSource
from noema.cognition.domain.epistemology.epistemic_status import EpistemicStatus
from noema.cognition.domain.errors import (
    InvalidEpistemicClaimError,
    InvalidEpistemicConflictError,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class EpistemicClaim:
    """A structured claim with explicit status, support, and conflicts."""

    statement: str
    status: EpistemicStatus
    confidence: float
    source: EpistemicSource
    claim_id: UUID = field(default_factory=uuid4)
    supporting_evidence_refs: tuple[str, ...] = ()
    counter_evidence_refs: tuple[str, ...] = ()
    conflicting_claim_ids: tuple[UUID, ...] = ()
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        """Validate claim content, confidence, references, conflicts, and time."""
        if not isinstance(self.status, EpistemicStatus):
            raise InvalidEpistemicClaimError("status must be an EpistemicStatus")
        if not isinstance(self.source, EpistemicSource):
            raise InvalidEpistemicClaimError("source must be an EpistemicSource")
        if not isinstance(self.statement, str) or not self.statement.strip():
            raise InvalidEpistemicClaimError("statement must not be empty")
        if (
            isinstance(self.confidence, bool)
            or not isinstance(self.confidence, (int, float))
            or not isfinite(self.confidence)
            or not 0.0 <= self.confidence <= 1.0
        ):
            raise InvalidEpistemicClaimError(
                "confidence must be a finite number between 0.0 and 1.0"
            )
        self._validate_evidence()
        self._validate_conflicts()
        if self.created_at.tzinfo is not UTC or self.updated_at.tzinfo is not UTC:
            raise InvalidEpistemicClaimError(
                "created_at and updated_at must be timezone-aware and in UTC"
            )
        if self.updated_at < self.created_at:
            raise InvalidEpistemicClaimError("updated_at must not precede created_at")

    def _validate_evidence(self) -> None:
        evidence_groups = (
            ("supporting_evidence_refs", self.supporting_evidence_refs),
            ("counter_evidence_refs", self.counter_evidence_refs),
        )
        for name, references in evidence_groups:
            if not isinstance(references, tuple) or any(
                not isinstance(reference, str) or not reference.strip() for reference in references
            ):
                raise InvalidEpistemicClaimError(f"{name} must contain non-empty string references")
            if len(references) != len(set(references)):
                raise InvalidEpistemicClaimError(f"{name} must not contain duplicates")
        if set(self.supporting_evidence_refs).intersection(self.counter_evidence_refs):
            raise InvalidEpistemicClaimError(
                "supporting and counter evidence references must be disjoint"
            )

    def _validate_conflicts(self) -> None:
        if not isinstance(self.conflicting_claim_ids, tuple) or not all(
            isinstance(claim_id, UUID) for claim_id in self.conflicting_claim_ids
        ):
            raise InvalidEpistemicConflictError(
                "conflicting_claim_ids must be a tuple of UUID values"
            )
        if len(self.conflicting_claim_ids) != len(set(self.conflicting_claim_ids)):
            raise InvalidEpistemicConflictError("conflicting_claim_ids must not contain duplicates")
        if self.claim_id in self.conflicting_claim_ids:
            raise InvalidEpistemicConflictError("a claim cannot conflict with itself")
        if self.status is EpistemicStatus.CONFLICTED and not self.conflicting_claim_ids:
            raise InvalidEpistemicConflictError(
                "CONFLICTED status requires at least one conflicting claim"
            )
        if self.status is not EpistemicStatus.CONFLICTED and self.conflicting_claim_ids:
            raise InvalidEpistemicConflictError(
                "conflicting claim identifiers require CONFLICTED status"
            )
