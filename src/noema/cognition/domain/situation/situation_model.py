"""Immutable snapshots of the current believed situation."""

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from noema.cognition.domain.errors import (
    DuplicateSituationEntryError,
    InvalidSituationDeltaError,
    InvalidSituationStateError,
    SituationEntryKindMismatchError,
    SituationEntryNotFoundError,
    StaleSituationDeltaError,
)
from noema.cognition.domain.situation.situation_delta import SituationDelta
from noema.cognition.domain.situation.situation_entry import SituationEntry
from noema.cognition.domain.situation.situation_entry_kind import SituationEntryKind


@dataclass(frozen=True, slots=True, kw_only=True)
class SituationModel:
    """Versioned snapshot of the agent's current believed situation."""

    situation_id: UUID = field(default_factory=uuid4)
    version: int = 0
    entries: tuple[SituationEntry, ...] = ()
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        """Validate direct construction invariants."""
        if isinstance(self.version, bool) or not isinstance(self.version, int) or self.version < 0:
            raise InvalidSituationStateError("version must be a non-negative integer")
        if not isinstance(self.entries, tuple) or not all(
            isinstance(entry, SituationEntry) for entry in self.entries
        ):
            raise InvalidSituationStateError("entries must be a tuple of SituationEntry values")
        entry_ids = tuple(entry.entry_id for entry in self.entries)
        if len(entry_ids) != len(set(entry_ids)):
            raise DuplicateSituationEntryError("situation entry identifiers must be unique")
        if self.created_at.tzinfo is not UTC or self.updated_at.tzinfo is not UTC:
            raise InvalidSituationStateError(
                "created_at and updated_at must be timezone-aware and in UTC"
            )
        if self.updated_at < self.created_at:
            raise InvalidSituationStateError("updated_at must not precede created_at")

    def apply(self, delta: SituationDelta) -> "SituationModel":
        """Validate and atomically apply a delta to a new snapshot."""
        if delta.base_version != self.version:
            raise StaleSituationDeltaError(
                f"delta targets version {delta.base_version}, current version is {self.version}"
            )
        if delta.occurred_at < self.updated_at:
            raise InvalidSituationDeltaError(
                "delta occurred_at must not precede situation updated_at"
            )
        if delta.is_empty:
            return self

        entries_by_id = {entry.entry_id: entry for entry in self.entries}
        self._validate_added(delta, entries_by_id)
        self._validate_updated(delta, entries_by_id)
        self._validate_removed(delta, entries_by_id)
        self._validate_resolved_unknowns(delta, entries_by_id)

        removed_ids = set(delta.removed_entry_ids).union(delta.resolved_unknown_ids)
        updated_by_id = {entry.entry_id: entry for entry in delta.updated}
        retained_entries = tuple(
            updated_by_id.get(entry.entry_id, entry)
            for entry in self.entries
            if entry.entry_id not in removed_ids
        )
        return replace(
            self,
            version=self.version + 1,
            entries=(*retained_entries, *delta.added),
            updated_at=delta.occurred_at,
        )

    def entries_of_kind(
        self,
        kind: SituationEntryKind,
    ) -> tuple[SituationEntry, ...]:
        """Return a derived view without duplicating situation state."""
        return tuple(entry for entry in self.entries if entry.kind is kind)

    def _validate_added(
        self,
        delta: SituationDelta,
        entries_by_id: dict[UUID, SituationEntry],
    ) -> None:
        for entry in delta.added:
            if entry.entry_id in entries_by_id:
                raise DuplicateSituationEntryError(f"entry {entry.entry_id} already exists")

    def _validate_updated(
        self,
        delta: SituationDelta,
        entries_by_id: dict[UUID, SituationEntry],
    ) -> None:
        for entry in delta.updated:
            current = entries_by_id.get(entry.entry_id)
            if current is None:
                raise SituationEntryNotFoundError(
                    f"entry {entry.entry_id} does not exist for update"
                )
            if entry.kind is not current.kind:
                raise SituationEntryKindMismatchError(f"entry {entry.entry_id} cannot change kind")

    def _validate_removed(
        self,
        delta: SituationDelta,
        entries_by_id: dict[UUID, SituationEntry],
    ) -> None:
        for entry_id in delta.removed_entry_ids:
            if entry_id not in entries_by_id:
                raise SituationEntryNotFoundError(f"entry {entry_id} does not exist for removal")

    def _validate_resolved_unknowns(
        self,
        delta: SituationDelta,
        entries_by_id: dict[UUID, SituationEntry],
    ) -> None:
        for entry_id in delta.resolved_unknown_ids:
            current = entries_by_id.get(entry_id)
            if current is None:
                raise SituationEntryNotFoundError(
                    f"unknown {entry_id} does not exist for resolution"
                )
            if current.kind is not SituationEntryKind.UNKNOWN:
                raise SituationEntryKindMismatchError(f"entry {entry_id} is not an UNKNOWN")
