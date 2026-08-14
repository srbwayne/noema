from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from noema.cognition.domain.errors import (
    CognitiveItemNotFoundError,
    DuplicateCognitiveItemError,
    InvalidWorkspaceFocusError,
    InvalidWorkspaceStateError,
    WorkspaceCapacityExceededError,
)
from noema.cognition.domain.workspace import (
    CognitiveItem,
    CognitiveItemKind,
    CognitiveWorkspace,
    WorkspaceBudget,
    WorkspaceRegion,
)


def budget(
    *,
    active: int = 2,
    working: int = 2,
    peripheral: int = 2,
) -> WorkspaceBudget:
    return WorkspaceBudget(
        max_active_items=active,
        max_working_items=working,
        max_peripheral_items=peripheral,
    )


def item(
    region: WorkspaceRegion = WorkspaceRegion.ACTIVE_CONTEXT,
    *,
    item_id: UUID | None = None,
) -> CognitiveItem:
    fields = {
        "kind": CognitiveItemKind.TASK,
        "content_ref": f"task:{uuid4()}",
        "region": region,
        "relevance": 0.8,
        "salience": 0.7,
        "activation": 0.9,
    }
    if item_id is None:
        return CognitiveItem(**fields)
    return CognitiveItem(**fields, item_id=item_id)


def workspace(*, workspace_budget: WorkspaceBudget | None = None) -> CognitiveWorkspace:
    return CognitiveWorkspace(budget=workspace_budget or budget())


def test_empty_workspace_is_valid() -> None:
    current = workspace()

    assert current.version == 0
    assert current.items == ()
    assert current.focus_item_id is None
    assert current.created_at.tzinfo is UTC
    assert current.updated_at.tzinfo is UTC
    assert current.updated_at >= current.created_at


def test_workspace_is_immutable() -> None:
    current = workspace()

    with pytest.raises(FrozenInstanceError):
        current.version = 1


def test_add_item_returns_new_version_and_preserves_original() -> None:
    original = workspace()
    cognitive_item = item()

    changed = original.add_item(cognitive_item)

    assert original.items == ()
    assert original.version == 0
    assert changed.items == (cognitive_item,)
    assert changed.version == 1
    assert changed.workspace_id == original.workspace_id
    assert changed.created_at == original.created_at
    assert changed.updated_at > original.updated_at


@pytest.mark.parametrize(
    ("region", "limited_budget"),
    [
        (WorkspaceRegion.ACTIVE_CONTEXT, budget(active=1)),
        (WorkspaceRegion.WORKING_STATE, budget(working=1)),
        (WorkspaceRegion.PERIPHERAL_BUFFER, budget(peripheral=1)),
    ],
)
def test_add_item_enforces_each_region_capacity(
    region: WorkspaceRegion,
    limited_budget: WorkspaceBudget,
) -> None:
    full = workspace(workspace_budget=limited_budget).add_item(item(region))

    with pytest.raises(WorkspaceCapacityExceededError, match=region.name):
        full.add_item(item(region))


def test_add_item_rejects_duplicate_id() -> None:
    cognitive_item = item()
    current = workspace().add_item(cognitive_item)

    with pytest.raises(DuplicateCognitiveItemError):
        current.add_item(cognitive_item)


def test_remove_item_returns_new_version_and_preserves_original() -> None:
    cognitive_item = item()
    original = workspace().add_item(cognitive_item)

    changed = original.remove_item(cognitive_item.item_id)

    assert original.items == (cognitive_item,)
    assert changed.items == ()
    assert changed.version == original.version + 1
    assert changed.updated_at > original.updated_at


def test_remove_item_rejects_unknown_id() -> None:
    with pytest.raises(CognitiveItemNotFoundError):
        workspace().remove_item(uuid4())


def test_removing_focused_item_clears_focus() -> None:
    cognitive_item = item()
    focused = workspace().add_item(cognitive_item).set_focus(cognitive_item.item_id)

    changed = focused.remove_item(cognitive_item.item_id)

    assert changed.focus_item_id is None


@pytest.mark.parametrize(
    "region",
    [WorkspaceRegion.ACTIVE_CONTEXT, WorkspaceRegion.WORKING_STATE],
)
def test_active_or_working_item_can_be_focus(region: WorkspaceRegion) -> None:
    cognitive_item = item(region)
    current = workspace().add_item(cognitive_item)

    focused = current.set_focus(cognitive_item.item_id)

    assert focused.focus_item_id == cognitive_item.item_id
    assert focused.version == current.version + 1


def test_peripheral_item_cannot_be_focus() -> None:
    peripheral = item(WorkspaceRegion.PERIPHERAL_BUFFER)
    current = workspace().add_item(peripheral)

    with pytest.raises(InvalidWorkspaceFocusError):
        current.set_focus(peripheral.item_id)


def test_unknown_item_cannot_be_focus() -> None:
    with pytest.raises(CognitiveItemNotFoundError):
        workspace().set_focus(uuid4())


def test_set_focus_replaces_previous_focus() -> None:
    first = item()
    second = item(WorkspaceRegion.WORKING_STATE)
    current = workspace().add_item(first).add_item(second).set_focus(first.item_id)

    changed = current.set_focus(second.item_id)

    assert changed.focus_item_id == second.item_id
    assert changed.version == current.version + 1


def test_setting_same_focus_is_no_op() -> None:
    cognitive_item = item()
    focused = workspace().add_item(cognitive_item).set_focus(cognitive_item.item_id)

    assert focused.set_focus(cognitive_item.item_id) is focused


def test_clear_focus_returns_new_snapshot() -> None:
    cognitive_item = item()
    focused = workspace().add_item(cognitive_item).set_focus(cognitive_item.item_id)

    cleared = focused.clear_focus()

    assert cleared.focus_item_id is None
    assert cleared.version == focused.version + 1
    assert focused.focus_item_id == cognitive_item.item_id


def test_clear_focus_without_focus_is_no_op() -> None:
    current = workspace()

    assert current.clear_focus() is current
    assert current.version == 0


def test_direct_construction_rejects_duplicate_ids() -> None:
    cognitive_item = item()

    with pytest.raises(DuplicateCognitiveItemError):
        CognitiveWorkspace(budget=budget(), items=(cognitive_item, cognitive_item))


@pytest.mark.parametrize(
    ("region", "limited_budget"),
    [
        (WorkspaceRegion.ACTIVE_CONTEXT, budget(active=1)),
        (WorkspaceRegion.WORKING_STATE, budget(working=1)),
        (WorkspaceRegion.PERIPHERAL_BUFFER, budget(peripheral=1)),
    ],
)
def test_direct_construction_rejects_exceeded_budget(
    region: WorkspaceRegion,
    limited_budget: WorkspaceBudget,
) -> None:
    with pytest.raises(WorkspaceCapacityExceededError):
        CognitiveWorkspace(
            budget=limited_budget,
            items=(item(region), item(region)),
        )


def test_direct_construction_rejects_orphan_focus() -> None:
    with pytest.raises(InvalidWorkspaceFocusError):
        CognitiveWorkspace(budget=budget(), focus_item_id=uuid4())


def test_direct_construction_rejects_peripheral_focus() -> None:
    peripheral = item(WorkspaceRegion.PERIPHERAL_BUFFER)

    with pytest.raises(InvalidWorkspaceFocusError):
        CognitiveWorkspace(
            budget=budget(),
            items=(peripheral,),
            focus_item_id=peripheral.item_id,
        )


def test_direct_construction_rejects_non_integer_version() -> None:
    with pytest.raises(InvalidWorkspaceStateError, match="version"):
        CognitiveWorkspace(budget=budget(), version=True)


def test_direct_construction_rejects_negative_version() -> None:
    with pytest.raises(InvalidWorkspaceStateError, match="version"):
        CognitiveWorkspace(budget=budget(), version=-1)


@pytest.mark.parametrize("timestamp_name", ["created_at", "updated_at"])
def test_direct_construction_rejects_naive_timestamps(timestamp_name: str) -> None:
    timestamp = datetime.now()
    valid_timestamp = datetime.now(UTC)

    if timestamp_name == "created_at":
        with pytest.raises(InvalidWorkspaceStateError, match=timestamp_name):
            CognitiveWorkspace(
                budget=budget(),
                created_at=timestamp,
                updated_at=valid_timestamp,
            )
    else:
        with pytest.raises(InvalidWorkspaceStateError, match=timestamp_name):
            CognitiveWorkspace(
                budget=budget(),
                created_at=valid_timestamp,
                updated_at=timestamp,
            )


def test_direct_construction_rejects_updated_at_before_created_at() -> None:
    created_at = datetime.now(UTC)

    with pytest.raises(InvalidWorkspaceStateError, match="updated_at"):
        CognitiveWorkspace(
            budget=budget(),
            created_at=created_at,
            updated_at=created_at - timedelta(microseconds=1),
        )


def test_workspace_versions_are_monotonic_and_snapshots_remain_intact() -> None:
    cognitive_item = item()
    v0 = workspace()
    v1 = v0.add_item(cognitive_item)
    v2 = v1.set_focus(cognitive_item.item_id)
    v3 = v2.remove_item(cognitive_item.item_id)

    assert (v0.version, v1.version, v2.version, v3.version) == (0, 1, 2, 3)
    assert v0.items == ()
    assert v1.items == (cognitive_item,)
    assert v1.focus_item_id is None
    assert v2.items == (cognitive_item,)
    assert v2.focus_item_id == cognitive_item.item_id
    assert v3.items == ()
    assert v3.focus_item_id is None
