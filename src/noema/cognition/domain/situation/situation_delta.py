"""An immutable proposal to change a specific situation version."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

from noema.cognition.domain.errors import InvalidSituationDeltaError
from noema.cognition.domain.situation.situation_entry import SituationEntry
from noema.cognition.domain.situation.situation_entry_kind import SituationEntryKind


@dataclass(frozen=True, slots=True, kw_only=True)
class SituationDelta:
    """Explicit additions, updates, removals, and unknown resolutions."""

    base_version: int
    added: tuple[SituationEntry, ...] = ()
    updated: tuple[SituationEntry, ...] = ()
    removed_entry_ids: tuple[UUID, ...] = ()
    resolved_unknown_ids: tuple[UUID, ...] = ()
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        """Validate version, immutable collections, time, duplicates, and conflicts."""
        if (
            isinstance(self.base_version, bool)
            or not isinstance(self.base_version, int)
            or self.base_version < 0
        ):
            raise InvalidSituationDeltaError("base_version must be a non-negative integer")
        if self.occurred_at.tzinfo is not UTC:
            raise InvalidSituationDeltaError("occurred_at must be timezone-aware and in UTC")
        if not isinstance(self.added, tuple) or not all(
            isinstance(entry, SituationEntry) for entry in self.added
        ):
            raise InvalidSituationDeltaError("added must be a tuple of SituationEntry values")
        if not isinstance(self.updated, tuple) or not all(
            isinstance(entry, SituationEntry) for entry in self.updated
        ):
            raise InvalidSituationDeltaError("updated must be a tuple of SituationEntry values")
        if not isinstance(self.removed_entry_ids, tuple) or not isinstance(
            self.resolved_unknown_ids, tuple
        ):
            raise InvalidSituationDeltaError("removed and resolved identifiers must be tuples")

        operation_ids = {
            "added": tuple(entry.entry_id for entry in self.added),
            "updated": tuple(entry.entry_id for entry in self.updated),
            "removed": self.removed_entry_ids,
            "resolved": self.resolved_unknown_ids,
        }
        for operation, entry_ids in operation_ids.items():
            if len(entry_ids) != len(set(entry_ids)):
                raise InvalidSituationDeltaError(
                    f"{operation} contains duplicate entry identifiers"
                )

        operations = tuple(operation_ids.items())
        for index, (left_name, left_ids) in enumerate(operations):
            for right_name, right_ids in operations[index + 1 :]:
                if set(left_ids).intersection(right_ids):
                    raise InvalidSituationDeltaError(
                        f"{left_name} and {right_name} contain conflicting entry identifiers"
                    )

    @property
    def new_observations(self) -> tuple[SituationEntry, ...]:
        """Return observations derived from added entries."""
        return tuple(entry for entry in self.added if entry.kind is SituationEntryKind.OBSERVATION)

    @property
    def new_unknowns(self) -> tuple[SituationEntry, ...]:
        """Return unknowns derived from added entries."""
        return tuple(entry for entry in self.added if entry.kind is SituationEntryKind.UNKNOWN)

    @property
    def is_empty(self) -> bool:
        """Return whether the delta proposes no state change."""
        return not (
            self.added or self.updated or self.removed_entry_ids or self.resolved_unknown_ids
        )
