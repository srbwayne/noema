"""Common metadata for domain events."""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from noema.shared.domain.domain_error import DomainError


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    """Immutable metadata shared by events across domain boundaries."""

    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    correlation_id: UUID | None = None
    causation_id: UUID | None = None

    def __post_init__(self) -> None:
        """Ensure event timestamps are timezone-aware and expressed in UTC."""
        if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() != timedelta(0):
            raise DomainError("occurred_at must be timezone-aware and in UTC")
