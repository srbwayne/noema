"""Immutable snapshots of current epistemic state."""

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from noema.cognition.domain.epistemology.epistemic_claim import EpistemicClaim
from noema.cognition.domain.epistemology.epistemic_delta import EpistemicDelta
from noema.cognition.domain.errors import (
    DuplicateEpistemicClaimError,
    EpistemicClaimImmutableFieldError,
    EpistemicClaimNotFoundError,
    InvalidEpistemicConflictError,
    InvalidEpistemicDeltaError,
    InvalidEpistemicStateError,
    StaleEpistemicDeltaError,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class EpistemicModel:
    """Versioned snapshot of claims and their current epistemic authority."""

    model_id: UUID = field(default_factory=uuid4)
    version: int = 0
    claims: tuple[EpistemicClaim, ...] = ()
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        """Validate direct construction invariants and conflict targets."""
        if isinstance(self.version, bool) or not isinstance(self.version, int) or self.version < 0:
            raise InvalidEpistemicStateError("version must be a non-negative integer")
        if not isinstance(self.claims, tuple) or not all(
            isinstance(claim, EpistemicClaim) for claim in self.claims
        ):
            raise InvalidEpistemicStateError("claims must be a tuple of EpistemicClaim values")
        claim_ids = tuple(claim.claim_id for claim in self.claims)
        if len(claim_ids) != len(set(claim_ids)):
            raise DuplicateEpistemicClaimError("epistemic claim identifiers must be unique")
        if self.created_at.tzinfo is not UTC or self.updated_at.tzinfo is not UTC:
            raise InvalidEpistemicStateError(
                "created_at and updated_at must be timezone-aware and in UTC"
            )
        if self.updated_at < self.created_at:
            raise InvalidEpistemicStateError("updated_at must not precede created_at")
        existing_ids = set(claim_ids)
        for claim in self.claims:
            missing_targets = set(claim.conflicting_claim_ids).difference(existing_ids)
            if missing_targets:
                raise InvalidEpistemicConflictError(
                    f"claim {claim.claim_id} references a nonexistent conflict target"
                )

    def apply(self, delta: EpistemicDelta) -> "EpistemicModel":
        """Validate and atomically apply a delta to a new snapshot."""
        if delta.base_version != self.version:
            raise StaleEpistemicDeltaError(
                f"delta targets version {delta.base_version}, current version is {self.version}"
            )
        if delta.is_empty:
            return self
        if delta.occurred_at < self.updated_at:
            raise InvalidEpistemicDeltaError("delta occurred_at must not precede model updated_at")

        claims_by_id = {claim.claim_id: claim for claim in self.claims}
        self._validate_added(delta, claims_by_id)
        self._validate_updated(delta, claims_by_id)
        self._validate_removed(delta, claims_by_id)

        removed_ids = set(delta.removed_claim_ids)
        updated_by_id = {claim.claim_id: claim for claim in delta.updated}
        retained_claims = tuple(
            updated_by_id.get(claim.claim_id, claim)
            for claim in self.claims
            if claim.claim_id not in removed_ids
        )
        return replace(
            self,
            version=self.version + 1,
            claims=(*retained_claims, *delta.added),
            updated_at=delta.occurred_at,
        )

    def _validate_added(
        self,
        delta: EpistemicDelta,
        claims_by_id: dict[UUID, EpistemicClaim],
    ) -> None:
        for claim in delta.added:
            if claim.claim_id in claims_by_id:
                raise DuplicateEpistemicClaimError(f"claim {claim.claim_id} already exists")

    def _validate_updated(
        self,
        delta: EpistemicDelta,
        claims_by_id: dict[UUID, EpistemicClaim],
    ) -> None:
        for claim in delta.updated:
            current = claims_by_id.get(claim.claim_id)
            if current is None:
                raise EpistemicClaimNotFoundError(
                    f"claim {claim.claim_id} does not exist for update"
                )
            immutable_fields = (
                ("statement", claim.statement, current.statement),
                ("source", claim.source, current.source),
                ("created_at", claim.created_at, current.created_at),
            )
            for name, proposed, existing in immutable_fields:
                if proposed != existing:
                    raise EpistemicClaimImmutableFieldError(
                        f"{name} cannot change during claim update"
                    )
            if claim.updated_at != delta.occurred_at:
                raise InvalidEpistemicDeltaError(
                    "updated claim timestamp must equal delta occurred_at"
                )

    def _validate_removed(
        self,
        delta: EpistemicDelta,
        claims_by_id: dict[UUID, EpistemicClaim],
    ) -> None:
        for claim_id in delta.removed_claim_ids:
            if claim_id not in claims_by_id:
                raise EpistemicClaimNotFoundError(f"claim {claim_id} does not exist for removal")
