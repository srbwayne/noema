"""An immutable reference to cognitively active information."""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from noema.cognition.domain.errors import InvalidCognitiveItemError
from noema.cognition.domain.workspace.cognitive_item_kind import CognitiveItemKind
from noema.cognition.domain.workspace.workspace_region import WorkspaceRegion


@dataclass(frozen=True, slots=True, kw_only=True)
class CognitiveItem:
    """A bounded workspace reference to information active in cognition."""

    kind: CognitiveItemKind
    content_ref: str
    region: WorkspaceRegion
    relevance: float
    salience: float
    activation: float
    item_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        """Validate the item's domain invariants."""
        if not self.content_ref.strip():
            raise InvalidCognitiveItemError("content_ref must not be empty")

        weights = (
            ("relevance", self.relevance),
            ("salience", self.salience),
            ("activation", self.activation),
        )
        for name, value in weights:
            if not 0.0 <= value <= 1.0:
                raise InvalidCognitiveItemError(f"{name} must be between 0.0 and 1.0")

        if self.created_at.tzinfo is None or self.created_at.utcoffset() != timedelta(0):
            raise InvalidCognitiveItemError("created_at must be timezone-aware and in UTC")
