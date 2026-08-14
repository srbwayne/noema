"""An immutable proposal to change a specific epistemic version."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from noema.cognition.domain.epistemology.epistemic_claim import EpistemicClaim
from noema.cognition.domain.errors import InvalidEpistemicDeltaError


@dataclass(frozen=True, slots=True, kw_only=True)
class EpistemicDelta:
    """Explicit additions, updates, and removals of epistemic claims."""

    base_version: int
    added: tuple[EpistemicClaim, ...] = ()
    updated: tuple[EpistemicClaim, ...] = ()
    removed_claim_ids: tuple[UUID, ...] = ()
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        """Validate version, immutable operations, time, duplicates, and conflicts."""
        if (
            isinstance(self.base_version, bool)
            or not isinstance(self.base_version, int)
            or self.base_version < 0
        ):
            raise InvalidEpistemicDeltaError("base_version must be a non-negative integer")
        if self.occurred_at.tzinfo is not UTC:
            raise InvalidEpistemicDeltaError("occurred_at must be timezone-aware and in UTC")
        if not isinstance(self.added, tuple) or not all(
            isinstance(claim, EpistemicClaim) for claim in self.added
        ):
            raise InvalidEpistemicDeltaError("added must be a tuple of EpistemicClaim values")
        if not isinstance(self.updated, tuple) or not all(
            isinstance(claim, EpistemicClaim) for claim in self.updated
        ):
            raise InvalidEpistemicDeltaError("updated must be a tuple of EpistemicClaim values")
        if not isinstance(self.removed_claim_ids, tuple) or not all(
            isinstance(claim_id, UUID) for claim_id in self.removed_claim_ids
        ):
            raise InvalidEpistemicDeltaError("removed_claim_ids must be a tuple of UUID values")

        operation_ids = {
            "added": tuple(claim.claim_id for claim in self.added),
            "updated": tuple(claim.claim_id for claim in self.updated),
            "removed": self.removed_claim_ids,
        }
        for operation, claim_ids in operation_ids.items():
            if len(claim_ids) != len(set(claim_ids)):
                raise InvalidEpistemicDeltaError(
                    f"{operation} contains duplicate claim identifiers"
                )

        operations = tuple(operation_ids.items())
        for index, (left_name, left_ids) in enumerate(operations):
            for right_name, right_ids in operations[index + 1 :]:
                if set(left_ids).intersection(right_ids):
                    raise InvalidEpistemicDeltaError(
                        f"{left_name} and {right_name} contain conflicting claim identifiers"
                    )

    @property
    def is_empty(self) -> bool:
        """Return whether the delta proposes no epistemic change."""
        return not (self.added or self.updated or self.removed_claim_ids)
