from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from math import inf, nan
from uuid import uuid4

import pytest

from noema.cognition.domain.epistemology import (
    EpistemicClaim,
    EpistemicSource,
    EpistemicSourceType,
    EpistemicStatus,
)
from noema.cognition.domain.errors import (
    InvalidEpistemicClaimError,
    InvalidEpistemicConflictError,
)
from noema.cognition.domain.situation import SituationEntryKind


def source(
    source_type: EpistemicSourceType = EpistemicSourceType.USER,
) -> EpistemicSource:
    return EpistemicSource(source_type=source_type, source_ref=f"{source_type.value}:origin")


def claim(
    *,
    statement: str = "The current branch is main",
    status: EpistemicStatus = EpistemicStatus.OBSERVATION,
    confidence: float = 0.8,
    supporting: tuple[str, ...] = (),
    counter: tuple[str, ...] = (),
    conflicts=(),
    claim_id=None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
    claim_source: EpistemicSource | None = None,
) -> EpistemicClaim:
    created = created_at or datetime.now(UTC)
    updated = updated_at or created
    fields = {
        "statement": statement,
        "status": status,
        "confidence": confidence,
        "source": claim_source or source(),
        "supporting_evidence_refs": supporting,
        "counter_evidence_refs": counter,
        "conflicting_claim_ids": conflicts,
        "created_at": created,
        "updated_at": updated,
    }
    if claim_id is None:
        return EpistemicClaim(**fields)
    return EpistemicClaim(claim_id=claim_id, **fields)


def test_epistemic_status_has_exactly_the_official_states() -> None:
    assert tuple(EpistemicStatus.__members__) == (
        "OBSERVATION",
        "FACT",
        "INFERENCE",
        "HYPOTHESIS",
        "ASSUMPTION",
        "PREDICTION",
        "OPINION",
        "UNKNOWN",
        "CONFLICTED",
    )
    assert EpistemicStatus.PREDICTION
    assert "PREDICTION" not in SituationEntryKind.__members__


def test_epistemic_claim_is_valid_and_receives_automatic_distinct_id() -> None:
    first = claim()
    second = claim()

    assert first.claim_id
    assert first.claim_id != second.claim_id
    assert first.statement == "The current branch is main"
    assert first.status is EpistemicStatus.OBSERVATION


@pytest.mark.parametrize("statement", ["", "   ", "\t\n"])
def test_epistemic_claim_rejects_empty_statement(statement: str) -> None:
    with pytest.raises(InvalidEpistemicClaimError, match="statement"):
        claim(statement=statement)


@pytest.mark.parametrize("confidence", [0.0, 1.0])
def test_epistemic_claim_accepts_confidence_boundaries(confidence: float) -> None:
    assert claim(confidence=confidence).confidence == confidence


@pytest.mark.parametrize("confidence", [-0.01, 1.01, nan, inf, -inf, True])
def test_epistemic_claim_rejects_invalid_confidence(confidence: float) -> None:
    with pytest.raises(InvalidEpistemicClaimError, match="confidence"):
        claim(confidence=confidence)


@pytest.mark.parametrize("evidence_group", ["supporting", "counter"])
@pytest.mark.parametrize("reference", ["", "   "])
def test_epistemic_claim_rejects_empty_evidence_reference(
    evidence_group: str,
    reference: str,
) -> None:
    values = {"supporting": (), "counter": ()}
    values[evidence_group] = (reference,)

    with pytest.raises(InvalidEpistemicClaimError, match=f"{evidence_group}_evidence_refs"):
        claim(supporting=values["supporting"], counter=values["counter"])


@pytest.mark.parametrize("evidence_group", ["supporting", "counter"])
def test_epistemic_claim_rejects_duplicate_evidence_reference(
    evidence_group: str,
) -> None:
    values = {"supporting": (), "counter": ()}
    values[evidence_group] = ("evidence:1", "evidence:1")

    with pytest.raises(InvalidEpistemicClaimError, match="duplicates"):
        claim(supporting=values["supporting"], counter=values["counter"])


def test_supporting_and_counter_evidence_must_be_disjoint() -> None:
    with pytest.raises(InvalidEpistemicClaimError, match="disjoint"):
        claim(supporting=("evidence:1",), counter=("evidence:1",))


def test_counter_evidence_does_not_automatically_create_conflict() -> None:
    current = claim(
        status=EpistemicStatus.HYPOTHESIS,
        supporting=("evidence:support",),
        counter=("evidence:counter",),
    )

    assert current.status is EpistemicStatus.HYPOTHESIS
    assert current.conflicting_claim_ids == ()


def test_evidence_tuples_and_claim_are_immutable() -> None:
    current = claim(supporting=("evidence:1",))

    assert isinstance(current.supporting_evidence_refs, tuple)
    with pytest.raises(FrozenInstanceError):
        current.status = EpistemicStatus.FACT


def test_epistemic_claim_rejects_duplicate_or_self_conflicts() -> None:
    other_id = uuid4()
    with pytest.raises(InvalidEpistemicConflictError, match="duplicates"):
        claim(
            status=EpistemicStatus.CONFLICTED,
            conflicts=(other_id, other_id),
        )

    claim_id = uuid4()
    with pytest.raises(InvalidEpistemicConflictError, match="itself"):
        claim(
            claim_id=claim_id,
            status=EpistemicStatus.CONFLICTED,
            conflicts=(claim_id,),
        )


def test_conflicted_status_and_conflict_ids_are_consistent() -> None:
    with pytest.raises(InvalidEpistemicConflictError, match="requires"):
        claim(status=EpistemicStatus.CONFLICTED)

    with pytest.raises(InvalidEpistemicConflictError, match="require CONFLICTED"):
        claim(conflicts=(uuid4(),))


def test_epistemic_claim_timestamps_are_utc_and_ordered() -> None:
    current = claim()

    assert current.created_at.tzinfo is UTC
    assert current.updated_at.tzinfo is UTC


@pytest.mark.parametrize(
    "timestamp",
    [
        datetime.now(),
        datetime.now(timezone(timedelta(hours=-3))),
    ],
)
@pytest.mark.parametrize("field_name", ["created_at", "updated_at"])
def test_epistemic_claim_rejects_non_utc_timestamp(
    field_name: str,
    timestamp: datetime,
) -> None:
    now = datetime.now(UTC)
    fields = {"created_at": now, "updated_at": now}
    fields[field_name] = timestamp

    with pytest.raises(InvalidEpistemicClaimError, match="UTC"):
        claim(created_at=fields["created_at"], updated_at=fields["updated_at"])


def test_epistemic_claim_rejects_updated_at_before_created_at() -> None:
    created_at = datetime.now(UTC)

    with pytest.raises(InvalidEpistemicClaimError, match="updated_at"):
        claim(
            created_at=created_at,
            updated_at=created_at - timedelta(microseconds=1),
        )


def test_model_source_and_hypothesis_status_are_independent() -> None:
    current = claim(
        status=EpistemicStatus.HYPOTHESIS,
        claim_source=source(EpistemicSourceType.MODEL),
    )

    assert current.source.source_type is EpistemicSourceType.MODEL
    assert current.status is EpistemicStatus.HYPOTHESIS
