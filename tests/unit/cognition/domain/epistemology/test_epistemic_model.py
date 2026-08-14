from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from noema.cognition.domain.epistemology import (
    EpistemicClaim,
    EpistemicDelta,
    EpistemicModel,
    EpistemicSource,
    EpistemicSourceType,
    EpistemicStatus,
)
from noema.cognition.domain.errors import (
    DuplicateEpistemicClaimError,
    EpistemicClaimImmutableFieldError,
    EpistemicClaimNotFoundError,
    InvalidEpistemicConflictError,
    InvalidEpistemicDeltaError,
    InvalidEpistemicStateError,
    StaleEpistemicDeltaError,
)

BASE_TIME = datetime(2026, 1, 1, tzinfo=UTC)


def source(
    source_type: EpistemicSourceType = EpistemicSourceType.USER,
    source_ref: str = "user:operator",
) -> EpistemicSource:
    return EpistemicSource(source_type=source_type, source_ref=source_ref)


def claim(
    *,
    claim_id: UUID | None = None,
    statement: str = "The current branch is main",
    status: EpistemicStatus = EpistemicStatus.HYPOTHESIS,
    confidence: float = 0.4,
    claim_source: EpistemicSource | None = None,
    supporting: tuple[str, ...] = (),
    counter: tuple[str, ...] = (),
    conflicts: tuple[UUID, ...] = (),
    created_at: datetime = BASE_TIME,
    updated_at: datetime = BASE_TIME,
) -> EpistemicClaim:
    fields = {
        "statement": statement,
        "status": status,
        "confidence": confidence,
        "source": claim_source or source(),
        "supporting_evidence_refs": supporting,
        "counter_evidence_refs": counter,
        "conflicting_claim_ids": conflicts,
        "created_at": created_at,
        "updated_at": updated_at,
    }
    if claim_id is None:
        return EpistemicClaim(**fields)
    return EpistemicClaim(claim_id=claim_id, **fields)


def model(*claims: EpistemicClaim, version: int = 0) -> EpistemicModel:
    return EpistemicModel(
        version=version,
        claims=claims,
        created_at=BASE_TIME,
        updated_at=BASE_TIME,
    )


def next_time(current: EpistemicModel) -> datetime:
    return current.updated_at + timedelta(microseconds=1)


def test_empty_epistemic_model_is_valid() -> None:
    current = EpistemicModel()

    assert current.version == 0
    assert current.claims == ()
    assert isinstance(current.claims, tuple)
    assert current.created_at.tzinfo is UTC
    assert current.updated_at.tzinfo is UTC
    assert current.updated_at >= current.created_at


def test_epistemic_model_is_immutable() -> None:
    current = model()

    with pytest.raises(FrozenInstanceError):
        current.version = 1


def test_apply_adds_claim_and_preserves_original_snapshot() -> None:
    original = model()
    added = claim()
    occurred_at = next_time(original)

    changed = original.apply(
        EpistemicDelta(
            base_version=0,
            added=(added,),
            occurred_at=occurred_at,
        )
    )

    assert original.claims == ()
    assert original.version == 0
    assert changed.claims == (added,)
    assert changed.version == 1
    assert changed.model_id == original.model_id
    assert changed.created_at == original.created_at
    assert changed.updated_at == occurred_at


def test_apply_rejects_duplicate_add() -> None:
    existing = claim()
    current = model(existing)

    with pytest.raises(DuplicateEpistemicClaimError):
        current.apply(
            EpistemicDelta(
                base_version=0,
                added=(existing,),
                occurred_at=next_time(current),
            )
        )


def test_update_changes_only_mutable_epistemic_dimensions() -> None:
    original_claim = claim()
    current = model(original_claim)
    occurred_at = next_time(current)
    updated_claim = replace(
        original_claim,
        status=EpistemicStatus.INFERENCE,
        confidence=0.7,
        supporting_evidence_refs=("evidence:build-output",),
        counter_evidence_refs=("evidence:stale-cache",),
        updated_at=occurred_at,
    )

    changed = current.apply(
        EpistemicDelta(
            base_version=0,
            updated=(updated_claim,),
            occurred_at=occurred_at,
        )
    )

    assert changed.claims == (updated_claim,)
    assert updated_claim.claim_id == original_claim.claim_id
    assert updated_claim.statement == original_claim.statement
    assert updated_claim.source == original_claim.source
    assert updated_claim.created_at == original_claim.created_at
    assert current.claims == (original_claim,)


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("statement", "A different statement"),
        ("source", source(EpistemicSourceType.TOOL, "tool:git-status")),
        ("created_at", BASE_TIME - timedelta(microseconds=1)),
    ],
)
def test_update_rejects_changes_to_immutable_fields(
    field_name: str,
    field_value,
) -> None:
    original_claim = claim()
    current = model(original_claim)
    occurred_at = next_time(current)
    proposed = replace(
        original_claim,
        updated_at=occurred_at,
        **{field_name: field_value},
    )

    with pytest.raises(EpistemicClaimImmutableFieldError, match=field_name):
        current.apply(
            EpistemicDelta(
                base_version=0,
                updated=(proposed,),
                occurred_at=occurred_at,
            )
        )


def test_update_requires_timestamp_equal_to_delta() -> None:
    original_claim = claim()
    current = model(original_claim)
    occurred_at = next_time(current)
    proposed = replace(
        original_claim,
        confidence=0.5,
        updated_at=occurred_at + timedelta(microseconds=1),
    )

    with pytest.raises(InvalidEpistemicDeltaError, match="timestamp"):
        current.apply(
            EpistemicDelta(
                base_version=0,
                updated=(proposed,),
                occurred_at=occurred_at,
            )
        )


def test_update_does_not_upsert_missing_claim() -> None:
    current = model()
    occurred_at = next_time(current)
    missing = claim(updated_at=occurred_at)

    with pytest.raises(EpistemicClaimNotFoundError):
        current.apply(
            EpistemicDelta(
                base_version=0,
                updated=(missing,),
                occurred_at=occurred_at,
            )
        )


def test_remove_requires_and_removes_existing_claim() -> None:
    existing = claim()
    current = model(existing)
    changed = current.apply(
        EpistemicDelta(
            base_version=0,
            removed_claim_ids=(existing.claim_id,),
            occurred_at=next_time(current),
        )
    )

    assert changed.claims == ()
    assert current.claims == (existing,)

    with pytest.raises(EpistemicClaimNotFoundError):
        changed.apply(
            EpistemicDelta(
                base_version=1,
                removed_claim_ids=(existing.claim_id,),
                occurred_at=next_time(changed),
            )
        )


def test_empty_delta_is_no_op_and_requires_current_version() -> None:
    current = model()
    empty = EpistemicDelta(base_version=0, occurred_at=current.updated_at)

    assert current.apply(empty) is current

    with pytest.raises(StaleEpistemicDeltaError):
        current.apply(EpistemicDelta(base_version=1, occurred_at=current.updated_at))


@pytest.mark.parametrize("base_version", [0, 2])
def test_stale_delta_rejects_lower_or_higher_version(base_version: int) -> None:
    existing = claim()
    current = model(existing, version=1)

    with pytest.raises(StaleEpistemicDeltaError):
        current.apply(
            EpistemicDelta(
                base_version=base_version,
                removed_claim_ids=(existing.claim_id,),
                occurred_at=next_time(current),
            )
        )

    assert current.version == 1
    assert current.claims == (existing,)


def test_delta_timestamp_cannot_regress() -> None:
    current = model()

    with pytest.raises(InvalidEpistemicDeltaError, match="occurred_at"):
        current.apply(
            EpistemicDelta(
                base_version=0,
                added=(claim(),),
                occurred_at=current.updated_at - timedelta(microseconds=1),
            )
        )


def test_hypothesis_transitions_are_explicit_and_versioned() -> None:
    hypothesis = claim(status=EpistemicStatus.HYPOTHESIS, confidence=0.4)
    e0 = model(hypothesis)

    t1 = next_time(e0)
    inference = replace(
        hypothesis,
        status=EpistemicStatus.INFERENCE,
        confidence=0.7,
        supporting_evidence_refs=("evidence:test-result",),
        updated_at=t1,
    )
    e1 = e0.apply(EpistemicDelta(base_version=0, updated=(inference,), occurred_at=t1))

    t2 = next_time(e1)
    fact = replace(
        inference,
        status=EpistemicStatus.FACT,
        confidence=0.9,
        updated_at=t2,
    )
    e2 = e1.apply(EpistemicDelta(base_version=1, updated=(fact,), occurred_at=t2))

    assert (e0.version, e1.version, e2.version) == (0, 1, 2)
    assert e0.claims[0].status is EpistemicStatus.HYPOTHESIS
    assert e0.claims[0].confidence == 0.4
    assert e1.claims[0].status is EpistemicStatus.INFERENCE
    assert e1.claims[0].confidence == 0.7
    assert e2.claims[0].status is EpistemicStatus.FACT
    assert e2.claims[0].confidence == 0.9


def test_conflict_is_accepted_only_when_target_exists_in_final_state() -> None:
    claim_a = claim(status=EpistemicStatus.FACT, confidence=0.9)
    claim_b = claim(
        statement="The current branch is develop",
        status=EpistemicStatus.INFERENCE,
        confidence=0.7,
    )
    current = model(claim_a, claim_b)
    occurred_at = next_time(current)
    conflicted_a = replace(
        claim_a,
        status=EpistemicStatus.CONFLICTED,
        conflicting_claim_ids=(claim_b.claim_id,),
        updated_at=occurred_at,
    )

    changed = current.apply(
        EpistemicDelta(
            base_version=0,
            updated=(conflicted_a,),
            occurred_at=occurred_at,
        )
    )

    assert changed.claims[0] == conflicted_a
    assert changed.claims[1] == claim_b


def test_direct_model_rejects_nonexistent_conflict_target() -> None:
    conflicted = claim(
        status=EpistemicStatus.CONFLICTED,
        conflicts=(uuid4(),),
    )

    with pytest.raises(InvalidEpistemicConflictError, match="nonexistent"):
        model(conflicted)


def test_removing_conflict_target_requires_updating_or_removing_referrer() -> None:
    claim_b = claim(statement="Alternative claim")
    claim_a = claim(
        status=EpistemicStatus.CONFLICTED,
        conflicts=(claim_b.claim_id,),
    )
    current = model(claim_a, claim_b)

    with pytest.raises(InvalidEpistemicConflictError):
        current.apply(
            EpistemicDelta(
                base_version=0,
                removed_claim_ids=(claim_b.claim_id,),
                occurred_at=next_time(current),
            )
        )

    assert current.claims == (claim_a, claim_b)


def test_direct_construction_rejects_duplicate_claim_ids() -> None:
    existing = claim()

    with pytest.raises(DuplicateEpistemicClaimError):
        model(existing, existing)


@pytest.mark.parametrize("version", [-1, True])
def test_direct_construction_rejects_invalid_version(version: int) -> None:
    with pytest.raises(InvalidEpistemicStateError, match="version"):
        model(version=version)


def test_direct_construction_rejects_invalid_timestamps() -> None:
    with pytest.raises(InvalidEpistemicStateError, match="UTC"):
        EpistemicModel(created_at=datetime.now(), updated_at=datetime.now())

    with pytest.raises(InvalidEpistemicStateError, match="updated_at"):
        EpistemicModel(
            created_at=BASE_TIME,
            updated_at=BASE_TIME - timedelta(microseconds=1),
        )


def test_competing_deltas_protect_against_stale_commit() -> None:
    base = model()
    delta_a = EpistemicDelta(
        base_version=0,
        added=(claim(statement="Claim A"),),
        occurred_at=next_time(base),
    )
    delta_b = EpistemicDelta(
        base_version=0,
        added=(claim(statement="Claim B"),),
        occurred_at=next_time(base),
    )

    m1 = base.apply(delta_a)

    with pytest.raises(StaleEpistemicDeltaError):
        m1.apply(delta_b)

    assert m1.version == 1
    assert len(m1.claims) == 1
