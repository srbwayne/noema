"""Immutable, bounded snapshots of cognitively active state."""

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from noema.cognition.domain.errors import (
    CognitiveItemNotFoundError,
    DuplicateCognitiveItemError,
    InvalidWorkspaceFocusError,
    InvalidWorkspaceStateError,
    WorkspaceCapacityExceededError,
)
from noema.cognition.domain.workspace.cognitive_item import CognitiveItem
from noema.cognition.domain.workspace.workspace_budget import WorkspaceBudget
from noema.cognition.domain.workspace.workspace_region import WorkspaceRegion


@dataclass(frozen=True, slots=True, kw_only=True)
class CognitiveWorkspace:
    """A limited, structured, and versioned snapshot of active cognition."""

    budget: WorkspaceBudget
    workspace_id: UUID = field(default_factory=uuid4)
    version: int = 0
    items: tuple[CognitiveItem, ...] = ()
    focus_item_id: UUID | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        """Validate all invariants, including those for direct construction."""
        if isinstance(self.version, bool) or not isinstance(self.version, int) or self.version < 0:
            raise InvalidWorkspaceStateError("version must be greater than or equal to zero")
        if not isinstance(self.items, tuple) or not all(
            isinstance(item, CognitiveItem) for item in self.items
        ):
            raise InvalidWorkspaceStateError("items must be a tuple of CognitiveItem values")
        self._validate_timestamps()
        self._validate_unique_items()
        self._validate_capacity()
        self._validate_focus()

    def add_item(self, item: CognitiveItem) -> "CognitiveWorkspace":
        """Return a new snapshot containing an additional item."""
        if any(existing.item_id == item.item_id for existing in self.items):
            raise DuplicateCognitiveItemError(f"item {item.item_id} already exists")
        self._ensure_region_has_capacity(item.region)
        return replace(
            self,
            version=self.version + 1,
            items=(*self.items, item),
            updated_at=self._next_updated_at(),
        )

    def remove_item(self, item_id: UUID) -> "CognitiveWorkspace":
        """Return a new snapshot without the requested item."""
        if not any(item.item_id == item_id for item in self.items):
            raise CognitiveItemNotFoundError(f"item {item_id} does not exist")
        return replace(
            self,
            version=self.version + 1,
            items=tuple(item for item in self.items if item.item_id != item_id),
            focus_item_id=None if self.focus_item_id == item_id else self.focus_item_id,
            updated_at=self._next_updated_at(),
        )

    def set_focus(self, item_id: UUID) -> "CognitiveWorkspace":
        """Return a new snapshot focused on an active, non-peripheral item."""
        item = self._item(item_id)
        if item.region is WorkspaceRegion.PERIPHERAL_BUFFER:
            raise InvalidWorkspaceFocusError("a peripheral item cannot become focus")
        if self.focus_item_id == item_id:
            return self
        return replace(
            self,
            version=self.version + 1,
            focus_item_id=item_id,
            updated_at=self._next_updated_at(),
        )

    def clear_focus(self) -> "CognitiveWorkspace":
        """Return an unfocused snapshot, or this instance when already clear."""
        if self.focus_item_id is None:
            return self
        return replace(
            self,
            version=self.version + 1,
            focus_item_id=None,
            updated_at=self._next_updated_at(),
        )

    def _item(self, item_id: UUID) -> CognitiveItem:
        for item in self.items:
            if item.item_id == item_id:
                return item
        raise CognitiveItemNotFoundError(f"item {item_id} does not exist")

    def _validate_timestamps(self) -> None:
        timestamps = (("created_at", self.created_at), ("updated_at", self.updated_at))
        for name, timestamp in timestamps:
            if timestamp.tzinfo is None or timestamp.utcoffset() != timedelta(0):
                raise InvalidWorkspaceStateError(f"{name} must be timezone-aware and in UTC")
        if self.updated_at < self.created_at:
            raise InvalidWorkspaceStateError("updated_at must not precede created_at")

    def _validate_unique_items(self) -> None:
        item_ids = [item.item_id for item in self.items]
        if len(item_ids) != len(set(item_ids)):
            raise DuplicateCognitiveItemError("workspace item identifiers must be unique")

    def _validate_capacity(self) -> None:
        for region in WorkspaceRegion:
            count = sum(item.region is region for item in self.items)
            if count > self._capacity_for(region):
                raise WorkspaceCapacityExceededError(f"{region.name} capacity exceeded")

    def _validate_focus(self) -> None:
        if self.focus_item_id is None:
            return
        try:
            focused_item = self._item(self.focus_item_id)
        except CognitiveItemNotFoundError as error:
            raise InvalidWorkspaceFocusError("focus must reference an existing item") from error
        if focused_item.region is WorkspaceRegion.PERIPHERAL_BUFFER:
            raise InvalidWorkspaceFocusError("a peripheral item cannot be focus")

    def _ensure_region_has_capacity(self, region: WorkspaceRegion) -> None:
        count = sum(item.region is region for item in self.items)
        if count >= self._capacity_for(region):
            raise WorkspaceCapacityExceededError(f"{region.name} capacity exceeded")

    def _capacity_for(self, region: WorkspaceRegion) -> int:
        if region is WorkspaceRegion.ACTIVE_CONTEXT:
            return self.budget.max_active_items
        if region is WorkspaceRegion.WORKING_STATE:
            return self.budget.max_working_items
        return self.budget.max_peripheral_items

    def _next_updated_at(self) -> datetime:
        now = datetime.now(UTC)
        if now <= self.updated_at:
            return self.updated_at + timedelta(microseconds=1)
        return now
