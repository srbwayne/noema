from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from noema.cognition.domain.errors import (
    DuplicateSituationEntryError,
    InvalidSituationDeltaError,
    InvalidSituationStateError,
    SituationEntryKindMismatchError,
    SituationEntryNotFoundError,
    StaleSituationDeltaError,
)
from noema.cognition.domain.situation import (
    SituationDelta,
    SituationEntry,
    SituationEntryKind,
    SituationModel,
)


def entry(
    kind: SituationEntryKind = SituationEntryKind.OBSERVATION,
    *,
    entry_id: UUID | None = None,
    content_ref: str | None = None,
) -> SituationEntry:
    fields = {
        "kind": kind,
        "content_ref": content_ref or f"{kind.value}:{uuid4()}",
    }
    if entry_id is None:
        return SituationEntry(**fields)
    return SituationEntry(**fields, entry_id=entry_id)


def delta(
    model: SituationModel,
    *,
    added: tuple[SituationEntry, ...] = (),
    updated: tuple[SituationEntry, ...] = (),
    removed_entry_ids: tuple[UUID, ...] = (),
    resolved_unknown_ids: tuple[UUID, ...] = (),
) -> SituationDelta:
    return SituationDelta(
        base_version=model.version,
        added=added,
        updated=updated,
        removed_entry_ids=removed_entry_ids,
        resolved_unknown_ids=resolved_unknown_ids,
        occurred_at=model.updated_at + timedelta(microseconds=1),
    )


def test_empty_situation_model_is_valid() -> None:
    model = SituationModel()

    assert model.version == 0
    assert model.entries == ()
    assert isinstance(model.entries, tuple)
    assert model.created_at.tzinfo is UTC
    assert model.updated_at.tzinfo is UTC
    assert model.updated_at >= model.created_at


def test_situation_model_is_immutable() -> None:
    model = SituationModel()

    with pytest.raises(FrozenInstanceError):
        model.version = 1


def test_apply_adds_entry_and_preserves_original_snapshot() -> None:
    original = SituationModel()
    observation = entry()

    changed = original.apply(delta(original, added=(observation,)))

    assert original.entries == ()
    assert original.version == 0
    assert changed.entries == (observation,)
    assert changed.version == 1
    assert changed.situation_id == original.situation_id
    assert changed.created_at == original.created_at
    assert changed.updated_at == original.updated_at + timedelta(microseconds=1)


def test_apply_updates_existing_entry_without_upsert() -> None:
    original_entry = entry(content_ref="observation:old")
    base = SituationModel()
    model = base.apply(delta(base, added=(original_entry,)))
    replacement = entry(
        entry_id=original_entry.entry_id,
        kind=original_entry.kind,
        content_ref="observation:new",
    )

    changed = model.apply(delta(model, updated=(replacement,)))

    assert changed.entries == (replacement,)
    assert model.entries == (original_entry,)


def test_update_requires_existing_entry() -> None:
    model = SituationModel()

    with pytest.raises(SituationEntryNotFoundError):
        model.apply(delta(model, updated=(entry(),)))


def test_update_preserves_entry_kind() -> None:
    original = entry(SituationEntryKind.ACTOR)
    base = SituationModel(entries=(original,))
    replacement = entry(
        SituationEntryKind.RESOURCE,
        entry_id=original.entry_id,
    )

    with pytest.raises(SituationEntryKindMismatchError):
        base.apply(delta(base, updated=(replacement,)))


def test_remove_requires_and_removes_existing_entry() -> None:
    current = entry()
    base = SituationModel(entries=(current,))

    changed = base.apply(delta(base, removed_entry_ids=(current.entry_id,)))

    assert changed.entries == ()
    assert base.entries == (current,)

    with pytest.raises(SituationEntryNotFoundError):
        changed.apply(delta(changed, removed_entry_ids=(current.entry_id,)))


def test_resolve_unknown_removes_it_and_allows_replacement_information() -> None:
    unknown = entry(SituationEntryKind.UNKNOWN)
    base = SituationModel(entries=(unknown,))
    resolved = entry(SituationEntryKind.RESOURCE, content_ref="resource:known")

    changed = base.apply(
        delta(
            base,
            added=(resolved,),
            resolved_unknown_ids=(unknown.entry_id,),
        )
    )

    assert unknown not in changed.entries
    assert resolved in changed.entries
    assert base.entries == (unknown,)


def test_resolve_unknown_requires_existing_entry() -> None:
    model = SituationModel()

    with pytest.raises(SituationEntryNotFoundError):
        model.apply(delta(model, resolved_unknown_ids=(uuid4(),)))


def test_resolve_unknown_rejects_non_unknown_entry() -> None:
    resource = entry(SituationEntryKind.RESOURCE)
    model = SituationModel(entries=(resource,))

    with pytest.raises(SituationEntryKindMismatchError):
        model.apply(delta(model, resolved_unknown_ids=(resource.entry_id,)))


def test_empty_delta_is_no_op_but_still_requires_current_base_version() -> None:
    model = SituationModel()
    empty = SituationDelta(
        base_version=model.version,
        occurred_at=model.updated_at,
    )

    assert model.apply(empty) is model

    with pytest.raises(StaleSituationDeltaError):
        model.apply(
            SituationDelta(
                base_version=model.version + 1,
                occurred_at=model.updated_at,
            )
        )


@pytest.mark.parametrize("base_version", [0, 2])
def test_stale_delta_rejects_lower_or_higher_version(base_version: int) -> None:
    current = entry()
    model = SituationModel(version=1, entries=(current,))

    with pytest.raises(StaleSituationDeltaError):
        model.apply(
            SituationDelta(
                base_version=base_version,
                added=(entry(),),
                occurred_at=model.updated_at,
            )
        )

    assert model.version == 1
    assert model.entries == (current,)


def test_delta_timestamp_cannot_regress() -> None:
    model = SituationModel()

    with pytest.raises(InvalidSituationDeltaError, match="occurred_at"):
        model.apply(
            SituationDelta(
                base_version=0,
                added=(entry(),),
                occurred_at=model.updated_at - timedelta(microseconds=1),
            )
        )


def test_entries_of_kind_returns_derived_tuple() -> None:
    observation = entry(SituationEntryKind.OBSERVATION)
    resource = entry(SituationEntryKind.RESOURCE)
    model = SituationModel(entries=(observation, resource))

    assert model.entries_of_kind(SituationEntryKind.OBSERVATION) == (observation,)
    assert isinstance(model.entries_of_kind(SituationEntryKind.OBSERVATION), tuple)


def test_direct_construction_rejects_duplicate_entry_ids() -> None:
    current = entry()

    with pytest.raises(DuplicateSituationEntryError):
        SituationModel(entries=(current, current))


@pytest.mark.parametrize("version", [-1, True])
def test_direct_construction_rejects_invalid_version(version: int) -> None:
    with pytest.raises(InvalidSituationStateError, match="version"):
        SituationModel(version=version)


@pytest.mark.parametrize("timestamp_name", ["created_at", "updated_at"])
def test_direct_construction_rejects_naive_timestamps(timestamp_name: str) -> None:
    utc_time = datetime.now(UTC)
    if timestamp_name == "created_at":
        with pytest.raises(InvalidSituationStateError):
            SituationModel(created_at=datetime.now(), updated_at=utc_time)
    else:
        with pytest.raises(InvalidSituationStateError):
            SituationModel(created_at=utc_time, updated_at=datetime.now())


def test_direct_construction_rejects_temporal_regression() -> None:
    created_at = datetime.now(UTC)

    with pytest.raises(InvalidSituationStateError, match="updated_at"):
        SituationModel(
            created_at=created_at,
            updated_at=created_at - timedelta(microseconds=1),
        )


def test_situation_lineage_is_monotonic_and_immutable() -> None:
    observation = entry(
        SituationEntryKind.OBSERVATION,
        content_ref="observation:branch requested",
    )
    unknown = entry(
        SituationEntryKind.UNKNOWN,
        content_ref="unknown:current branch",
    )
    resolved_resource = entry(
        SituationEntryKind.RESOURCE,
        content_ref="resource:branch main",
    )

    s0 = SituationModel()
    s1 = s0.apply(delta(s0, added=(observation,)))
    s2 = s1.apply(delta(s1, added=(unknown,)))
    s3 = s2.apply(
        delta(
            s2,
            added=(resolved_resource,),
            resolved_unknown_ids=(unknown.entry_id,),
        )
    )
    updated_observation = entry(
        SituationEntryKind.OBSERVATION,
        entry_id=observation.entry_id,
        content_ref="observation:branch confirmed",
    )
    s4 = s3.apply(delta(s3, updated=(updated_observation,)))

    assert (s0.version, s1.version, s2.version, s3.version, s4.version) == (0, 1, 2, 3, 4)
    assert len({snapshot.situation_id for snapshot in (s0, s1, s2, s3, s4)}) == 1
    assert len({snapshot.created_at for snapshot in (s0, s1, s2, s3, s4)}) == 1
    assert s0.entries == ()
    assert s1.entries == (observation,)
    assert unknown in s2.entries
    assert unknown not in s3.entries
    assert unknown not in s4.entries
    assert updated_observation in s4.entries
    assert observation in s3.entries


def test_competing_deltas_protect_against_stale_commit() -> None:
    base = SituationModel()
    delta_a = delta(base, added=(entry(content_ref="observation:a"),))
    delta_b = delta(base, added=(entry(content_ref="observation:b"),))

    s1 = base.apply(delta_a)

    with pytest.raises(StaleSituationDeltaError):
        s1.apply(delta_b)

    assert s1.version == 1
    assert len(s1.entries) == 1
