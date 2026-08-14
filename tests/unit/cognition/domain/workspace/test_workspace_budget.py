from dataclasses import FrozenInstanceError

import pytest

from noema.cognition.domain.errors import InvalidWorkspaceBudgetError
from noema.cognition.domain.workspace import WorkspaceBudget


def workspace_budget(
    *,
    active: int = 2,
    working: int = 3,
    peripheral: int = 4,
) -> WorkspaceBudget:
    return WorkspaceBudget(
        max_active_items=active,
        max_working_items=working,
        max_peripheral_items=peripheral,
    )


def test_workspace_budget_accepts_positive_limits() -> None:
    budget = workspace_budget()

    assert budget.max_active_items == 2
    assert budget.max_working_items == 3
    assert budget.max_peripheral_items == 4
    assert budget.max_total_items == 9


@pytest.mark.parametrize("value", [0, -1])
@pytest.mark.parametrize("limit_name", ["active", "working", "peripheral"])
def test_workspace_budget_rejects_non_positive_limits(limit_name: str, value: int) -> None:
    limits = {"active": 1, "working": 1, "peripheral": 1}
    limits[limit_name] = value

    with pytest.raises(InvalidWorkspaceBudgetError):
        workspace_budget(
            active=limits["active"],
            working=limits["working"],
            peripheral=limits["peripheral"],
        )


def test_workspace_budget_rejects_boolean_limits() -> None:
    with pytest.raises(InvalidWorkspaceBudgetError, match="max_active_items"):
        workspace_budget(active=True)


def test_workspace_budget_is_immutable() -> None:
    budget = workspace_budget()

    with pytest.raises(FrozenInstanceError):
        budget.max_active_items = 10
