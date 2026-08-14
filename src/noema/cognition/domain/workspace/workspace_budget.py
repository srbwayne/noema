"""Capacity limits for a cognitive workspace."""

from dataclasses import dataclass

from noema.cognition.domain.errors import InvalidWorkspaceBudgetError


@dataclass(frozen=True, slots=True, kw_only=True)
class WorkspaceBudget:
    """Explicit per-region limits that keep a workspace bounded."""

    max_active_items: int
    max_working_items: int
    max_peripheral_items: int

    def __post_init__(self) -> None:
        """Require positive integer limits for every region."""
        limits = (
            ("max_active_items", self.max_active_items),
            ("max_working_items", self.max_working_items),
            ("max_peripheral_items", self.max_peripheral_items),
        )
        for name, value in limits:
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise InvalidWorkspaceBudgetError(f"{name} must be a positive integer")

    @property
    def max_total_items(self) -> int:
        """Return the total capacity derived from the region limits."""
        return self.max_active_items + self.max_working_items + self.max_peripheral_items
