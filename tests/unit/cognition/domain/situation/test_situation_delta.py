from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from noema.cognition.domain.errors import InvalidSituationDeltaError
from noema.cognition.domain.situation import (
    SituationDelta,
    SituationEntry,
    SituationEntryKind,
)


def entry(
    kind: SituationEntryKind = SituationEntryKind.ENTITY,
    *,
    entry_id=None,
) -> SituationEntry:
    if entry_id is None:
        return SituationEntry(kind=kind, content_ref=f"{kind.value}:current")
    return SituationEntry(
        entry_id=entry_id,
        kind=kind,
        content_ref=f"{kind.value}:current",
    )


def test_situation_delta_accepts_valid_and_empty_operations() -> None:
    added = entry()
    delta = SituationDelta(base_version=0, added=(added,))
    empty = SituationDelta(base_version=0)

    assert delta.base_version == 0
    assert delta.added == (added,)
    assert empty.is_empty
    assert empty.added == ()
    assert empty.updated == ()
    assert empty.removed_entry_ids == ()
    assert empty.resolved_unknown_ids == ()


@pytest.mark.parametrize("base_version", [-1, True])
def test_situation_delta_rejects_invalid_base_version(base_version: int) -> None:
    with pytest.raises(InvalidSituationDeltaError, match="base_version"):
        SituationDelta(base_version=base_version)


def test_situation_delta_timestamp_is_utc() -> None:
    assert SituationDelta(base_version=0).occurred_at.tzinfo is UTC


def test_situation_delta_rejects_naive_timestamp() -> None:
    with pytest.raises(InvalidSituationDeltaError, match="occurred_at"):
        SituationDelta(base_version=0, occurred_at=datetime.now())


@pytest.mark.parametrize(
    "operation",
    ["added", "updated", "removed_entry_ids", "resolved_unknown_ids"],
)
def test_situation_delta_rejects_duplicate_ids_within_operation(operation: str) -> None:
    current = entry(kind=SituationEntryKind.UNKNOWN)
    operations = {
        "added": (),
        "updated": (),
        "removed_entry_ids": (),
        "resolved_unknown_ids": (),
    }
    if operation in {"added", "updated"}:
        operations[operation] = (current, current)
    else:
        operations[operation] = (current.entry_id, current.entry_id)

    with pytest.raises(InvalidSituationDeltaError, match="duplicate"):
        SituationDelta(base_version=0, **operations)


@pytest.mark.parametrize(
    ("left_operation", "right_operation"),
    [
        ("added", "updated"),
        ("added", "removed_entry_ids"),
        ("updated", "removed_entry_ids"),
        ("updated", "resolved_unknown_ids"),
    ],
)
def test_situation_delta_rejects_conflicting_operations(
    left_operation: str,
    right_operation: str,
) -> None:
    entry_id = uuid4()
    current = entry(kind=SituationEntryKind.UNKNOWN, entry_id=entry_id)
    operations = {
        "added": (),
        "updated": (),
        "removed_entry_ids": (),
        "resolved_unknown_ids": (),
    }
    for operation in (left_operation, right_operation):
        if operation in {"added", "updated"}:
            operations[operation] = (current,)
        else:
            operations[operation] = (entry_id,)

    with pytest.raises(InvalidSituationDeltaError, match="conflicting"):
        SituationDelta(base_version=0, **operations)


def test_situation_delta_derives_new_observations_and_unknowns() -> None:
    observation = entry(SituationEntryKind.OBSERVATION)
    unknown = entry(SituationEntryKind.UNKNOWN)
    resource = entry(SituationEntryKind.RESOURCE)

    delta = SituationDelta(base_version=0, added=(observation, unknown, resource))

    assert delta.new_observations == (observation,)
    assert delta.new_unknowns == (unknown,)


def test_situation_delta_is_immutable() -> None:
    delta = SituationDelta(base_version=0)

    with pytest.raises(FrozenInstanceError):
        delta.base_version = 1
