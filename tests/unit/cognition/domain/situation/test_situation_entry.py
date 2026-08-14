from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from uuid import uuid4

import pytest

from noema.cognition.domain.errors import InvalidSituationEntryError
from noema.cognition.domain.situation import SituationEntry, SituationEntryKind


def test_situation_entry_is_valid_and_receives_automatic_id() -> None:
    entry = SituationEntry(
        kind=SituationEntryKind.ACTOR,
        content_ref="actor:operator",
    )

    assert entry.entry_id
    assert entry.kind is SituationEntryKind.ACTOR
    assert entry.content_ref == "actor:operator"


def test_situation_entries_receive_distinct_ids() -> None:
    first = SituationEntry(kind=SituationEntryKind.ENTITY, content_ref="entity:first")
    second = SituationEntry(kind=SituationEntryKind.ENTITY, content_ref="entity:second")

    assert first.entry_id != second.entry_id


@pytest.mark.parametrize("content_ref", ["", "   ", "\t\n"])
def test_situation_entry_rejects_empty_content_reference(content_ref: str) -> None:
    with pytest.raises(InvalidSituationEntryError, match="content_ref"):
        SituationEntry(kind=SituationEntryKind.OBSERVATION, content_ref=content_ref)


def test_situation_entry_timestamp_is_utc() -> None:
    entry = SituationEntry(
        kind=SituationEntryKind.OBSERVATION,
        content_ref="observation:current",
    )

    assert entry.created_at.tzinfo is UTC


@pytest.mark.parametrize(
    "created_at",
    [
        datetime.now(),
        datetime.now(timezone(timedelta(hours=-3))),
    ],
)
def test_situation_entry_rejects_non_utc_timestamp(created_at: datetime) -> None:
    with pytest.raises(InvalidSituationEntryError, match="created_at"):
        SituationEntry(
            kind=SituationEntryKind.OBSERVATION,
            content_ref="observation:current",
            created_at=created_at,
        )


def test_situation_entry_is_immutable() -> None:
    entry = SituationEntry(kind=SituationEntryKind.RESOURCE, content_ref="resource:cpu")

    with pytest.raises(FrozenInstanceError):
        entry.content_ref = "resource:memory"


def test_situation_entry_has_structural_equality() -> None:
    entry_id = uuid4()
    created_at = datetime.now(UTC)

    first = SituationEntry(
        entry_id=entry_id,
        kind=SituationEntryKind.GOAL,
        content_ref="goal:ship",
        created_at=created_at,
    )
    second = SituationEntry(
        entry_id=entry_id,
        kind=SituationEntryKind.GOAL,
        content_ref="goal:ship",
        created_at=created_at,
    )

    assert first == second


def test_prediction_is_not_a_situation_entry_kind() -> None:
    assert "PREDICTION" not in SituationEntryKind.__members__
