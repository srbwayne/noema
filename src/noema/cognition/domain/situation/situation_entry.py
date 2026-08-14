"""An immutable reference in the current believed situation."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from noema.cognition.domain.errors import InvalidSituationEntryError
from noema.cognition.domain.situation.situation_entry_kind import SituationEntryKind


@dataclass(frozen=True, slots=True, kw_only=True)
class SituationEntry:
    """A typed, opaque reference representing part of the current situation."""

    kind: SituationEntryKind
    content_ref: str
    entry_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        """Validate content and UTC creation time."""
        if not isinstance(self.content_ref, str) or not self.content_ref.strip():
            raise InvalidSituationEntryError("content_ref must not be empty")
        if self.created_at.tzinfo is not UTC:
            raise InvalidSituationEntryError("created_at must be timezone-aware and in UTC")
