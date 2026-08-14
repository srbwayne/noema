from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from noema.cognition.domain.epistemology import (
    EpistemicClaim,
    EpistemicDelta,
    EpistemicSource,
    EpistemicSourceType,
    EpistemicStatus,
)
from noema.cognition.domain.errors import InvalidEpistemicDeltaError


def claim(*, claim_id: UUID | None = None) -> EpistemicClaim:
    fields = {
        "statement": "A claim",
        "status": EpistemicStatus.HYPOTHESIS,
        "confidence": 0.4,
        "source": EpistemicSource(
            source_type=EpistemicSourceType.USER,
            source_ref="user:operator",
        ),
    }
    if claim_id is None:
        return EpistemicClaim(**fields)
    return EpistemicClaim(claim_id=claim_id, **fields)


def test_epistemic_delta_accepts_valid_and_empty_operations() -> None:
    added = claim()
    delta = EpistemicDelta(base_version=0, added=(added,))
    empty = EpistemicDelta(base_version=0)

    assert delta.base_version == 0
    assert delta.added == (added,)
    assert empty.is_empty
    assert empty.added == ()
    assert empty.updated == ()
    assert empty.removed_claim_ids == ()


@pytest.mark.parametrize("base_version", [-1, True])
def test_epistemic_delta_rejects_invalid_base_version(base_version: int) -> None:
    with pytest.raises(InvalidEpistemicDeltaError, match="base_version"):
        EpistemicDelta(base_version=base_version)


def test_epistemic_delta_timestamp_is_utc() -> None:
    assert EpistemicDelta(base_version=0).occurred_at.tzinfo is UTC


def test_epistemic_delta_rejects_naive_timestamp() -> None:
    with pytest.raises(InvalidEpistemicDeltaError, match="occurred_at"):
        EpistemicDelta(base_version=0, occurred_at=datetime.now())


@pytest.mark.parametrize("operation", ["added", "updated", "removed_claim_ids"])
def test_epistemic_delta_rejects_duplicate_ids(operation: str) -> None:
    current = claim()
    operations = {"added": (), "updated": (), "removed_claim_ids": ()}
    if operation in {"added", "updated"}:
        operations[operation] = (current, current)
    else:
        operations[operation] = (current.claim_id, current.claim_id)

    with pytest.raises(InvalidEpistemicDeltaError, match="duplicate"):
        EpistemicDelta(base_version=0, **operations)


@pytest.mark.parametrize(
    ("left_operation", "right_operation"),
    [
        ("added", "updated"),
        ("added", "removed_claim_ids"),
        ("updated", "removed_claim_ids"),
    ],
)
def test_epistemic_delta_rejects_conflicting_operations(
    left_operation: str,
    right_operation: str,
) -> None:
    claim_id = uuid4()
    current = claim(claim_id=claim_id)
    operations = {"added": (), "updated": (), "removed_claim_ids": ()}
    for operation in (left_operation, right_operation):
        operations[operation] = (current,) if operation in {"added", "updated"} else (claim_id,)

    with pytest.raises(InvalidEpistemicDeltaError, match="conflicting"):
        EpistemicDelta(base_version=0, **operations)


def test_epistemic_delta_is_immutable() -> None:
    delta = EpistemicDelta(base_version=0)

    with pytest.raises(FrozenInstanceError):
        delta.base_version = 1
