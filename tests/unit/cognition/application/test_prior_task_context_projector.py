import unicodedata
from datetime import UTC, datetime

import pytest

from noema.cognition.application import (
    PriorTaskContextProjector,
    RuntimeContentReferenceAuthority,
    RuntimeContentReferenceNotFoundError,
)
from noema.cognition.domain.context_composition import (
    ContextPackageZone,
    ContextSensitivity,
    ContextSliceType,
    ContextTrustLevel,
)
from noema.cognition.domain.errors import InvalidContextCandidateError
from noema.cognition.domain.situation import SituationEntry, SituationEntryKind, SituationModel


def _authority(**payloads: str) -> RuntimeContentReferenceAuthority:
    authority = RuntimeContentReferenceAuthority()
    for content_ref, payload in payloads.items():
        authority.register(content_ref=content_ref, payload=payload)
    return authority


def _entry(
    *,
    content_ref: str,
    kind: SituationEntryKind = SituationEntryKind.TASK,
    created_at: datetime | None = None,
) -> SituationEntry:
    if created_at is None:
        return SituationEntry(kind=kind, content_ref=content_ref)
    return SituationEntry(kind=kind, content_ref=content_ref, created_at=created_at)


def _situation(
    *entries: SituationEntry,
    updated_at: datetime | None = None,
) -> SituationModel:
    if updated_at is None:
        return SituationModel(entries=entries)
    return SituationModel(entries=entries, created_at=updated_at, updated_at=updated_at)


def _projector(
    **payloads: str,
) -> tuple[PriorTaskContextProjector, RuntimeContentReferenceAuthority]:
    authority = _authority(**payloads)
    return PriorTaskContextProjector(runtime_content_authority=authority), authority


# --- zero / one / multi TASK behavior ---------------------------------------


def test_zero_task_entries_returns_empty_tuple() -> None:
    projector, _ = _projector()
    situation = _situation(_entry(content_ref="entity:1", kind=SituationEntryKind.ENTITY))
    assert projector.project(situation=situation) == ()


def test_single_current_task_only_returns_empty_tuple() -> None:
    projector, authority = _projector(**{"task:current": "current payload"})
    situation = _situation(_entry(content_ref="task:current"))
    assert projector.project(situation=situation) == ()
    with pytest.raises(RuntimeContentReferenceNotFoundError):
        authority.resolve(content_ref="task:other")


def test_multiple_prior_tasks_projected_in_canonical_order() -> None:
    projector, _ = _projector(**{"task:1": "first", "task:2": "second", "task:3": "current"})
    situation = _situation(
        _entry(content_ref="task:1"),
        _entry(content_ref="task:2"),
        _entry(content_ref="task:3"),
    )
    candidates = projector.project(situation=situation)
    assert tuple(c.context_slice.content_ref for c in candidates) == ("task:1", "task:2")


def test_interleaved_non_task_entries_are_ignored() -> None:
    projector, _ = _projector(**{"task:1": "first", "task:2": "current"})
    situation = _situation(
        _entry(content_ref="entity:a", kind=SituationEntryKind.ENTITY),
        _entry(content_ref="task:1"),
        _entry(content_ref="entity:b", kind=SituationEntryKind.ENTITY),
        _entry(content_ref="task:2"),
    )
    candidates = projector.project(situation=situation)
    assert tuple(c.context_slice.content_ref for c in candidates) == ("task:1",)


def test_latest_task_is_excluded_positionally() -> None:
    projector, _ = _projector(**{"task:1": "first", "task:2": "current"})
    situation = _situation(_entry(content_ref="task:1"), _entry(content_ref="task:2"))
    candidates = projector.project(situation=situation)
    assert "task:2" not in tuple(c.context_slice.content_ref for c in candidates)


def test_same_content_ref_as_current_task_does_not_affect_positional_exclusion() -> None:
    """Two entries may legitimately share a content_ref; exclusion of the

    current task is purely positional (last), never content_ref-based.
    """
    projector, authority = _projector()
    authority.register(content_ref="task:repeat", payload="same payload")
    situation = _situation(
        _entry(content_ref="task:repeat"),
        _entry(content_ref="task:repeat"),
    )
    candidates = projector.project(situation=situation)
    assert len(candidates) == 1
    assert candidates[0].context_slice.content_ref == "task:repeat"


# --- exact field realization -------------------------------------------------


def test_content_ref_preserved_exactly() -> None:
    projector, _ = _projector(**{"task:prior": "payload", "task:current": "current"})
    entry = _entry(content_ref="task:prior")
    situation = _situation(entry, _entry(content_ref="task:current"))
    candidate = projector.project(situation=situation)[0]
    assert candidate.context_slice.content_ref == entry.content_ref


def test_entry_id_converted_exactly_to_provenance_ref() -> None:
    projector, _ = _projector(**{"task:prior": "payload", "task:current": "current"})
    entry = _entry(content_ref="task:prior")
    situation = _situation(entry, _entry(content_ref="task:current"))
    candidate = projector.project(situation=situation)[0]
    assert candidate.context_slice.provenance_ref == str(entry.entry_id)


def test_classification_fields_are_exact() -> None:
    projector, _ = _projector(**{"task:prior": "payload", "task:current": "current"})
    situation = _situation(_entry(content_ref="task:prior"), _entry(content_ref="task:current"))
    candidate = projector.project(situation=situation)[0]
    context_slice = candidate.context_slice
    assert context_slice.slice_type is ContextSliceType.TASK
    assert context_slice.zone is ContextPackageZone.COGNITIVE_STATE
    assert context_slice.sensitivity is ContextSensitivity.SECRET
    assert context_slice.trust is ContextTrustLevel.UNVERIFIED
    assert context_slice.instruction_authority is None


def test_relevance_is_none() -> None:
    projector, _ = _projector(**{"task:prior": "payload", "task:current": "current"})
    situation = _situation(_entry(content_ref="task:prior"), _entry(content_ref="task:current"))
    candidate = projector.project(situation=situation)[0]
    assert candidate.relevance is None


def test_age_formula_is_exact() -> None:
    prior_time = datetime(2026, 1, 1, tzinfo=UTC)
    snapshot_time = datetime(2026, 1, 1, 0, 5, tzinfo=UTC)
    projector, _ = _projector(**{"task:prior": "payload", "task:current": "current"})
    prior_entry = _entry(content_ref="task:prior", created_at=prior_time)
    current_entry = _entry(content_ref="task:current", created_at=snapshot_time)
    situation = _situation(prior_entry, current_entry, updated_at=snapshot_time)
    candidate = projector.project(situation=situation)[0]
    assert candidate.age == snapshot_time - prior_time


def test_negative_age_propagates_invalid_context_candidate_error() -> None:
    late = datetime(2026, 1, 2, tzinfo=UTC)
    early = datetime(2026, 1, 1, tzinfo=UTC)
    projector, _ = _projector(**{"task:prior": "payload", "task:current": "current"})
    prior_entry = _entry(content_ref="task:prior", created_at=late)
    current_entry = _entry(content_ref="task:current", created_at=late)
    situation = _situation(prior_entry, current_entry, updated_at=early)
    with pytest.raises(InvalidContextCandidateError):
        projector.project(situation=situation)


# --- content-size measurement ------------------------------------------------


def test_content_size_is_raw_unicode_code_point_count() -> None:
    payload = "hello world"
    projector, _ = _projector(**{"task:prior": payload, "task:current": "current"})
    situation = _situation(_entry(content_ref="task:prior"), _entry(content_ref="task:current"))
    candidate = projector.project(situation=situation)[0]
    assert candidate.context_slice.content_size == len(payload)


def test_content_size_uses_no_unicode_normalization() -> None:
    combining = "é"  # "e" + combining acute accent -- NFD form
    precomposed = unicodedata.normalize("NFC", combining)
    assert len(combining) != len(precomposed)
    projector, _ = _projector(**{"task:prior": combining, "task:current": "current"})
    situation = _situation(_entry(content_ref="task:prior"), _entry(content_ref="task:current"))
    candidate = projector.project(situation=situation)[0]
    assert candidate.context_slice.content_size == len(combining)


def test_empty_registered_payload_gives_content_size_zero() -> None:
    projector, _ = _projector(**{"task:prior": "", "task:current": "current"})
    situation = _situation(_entry(content_ref="task:prior"), _entry(content_ref="task:current"))
    candidate = projector.project(situation=situation)[0]
    assert candidate.context_slice.content_size == 0


def test_missing_content_reference_propagates_not_found_error() -> None:
    projector, _ = _projector(**{"task:current": "current"})
    situation = _situation(
        _entry(content_ref="task:unregistered"),
        _entry(content_ref="task:current"),
    )
    with pytest.raises(RuntimeContentReferenceNotFoundError):
        projector.project(situation=situation)


# --- duplicate content_ref among distinct prior entries ---------------------


def test_duplicate_content_ref_among_prior_entries_creates_two_candidates() -> None:
    projector, _ = _projector(**{"task:dup": "shared payload", "task:current": "current"})
    first = _entry(content_ref="task:dup")
    second = _entry(content_ref="task:dup")
    situation = _situation(first, second, _entry(content_ref="task:current"))
    candidates = projector.project(situation=situation)
    assert len(candidates) == 2
    assert candidates[0].context_slice.content_ref == candidates[1].context_slice.content_ref
    assert candidates[0].context_slice.provenance_ref != candidates[1].context_slice.provenance_ref
    assert candidates[0].context_slice.provenance_ref == str(first.entry_id)
    assert candidates[1].context_slice.provenance_ref == str(second.entry_id)


# --- observational purity ----------------------------------------------------


def test_projection_does_not_mutate_situation_model() -> None:
    projector, _ = _projector(**{"task:prior": "payload", "task:current": "current"})
    entries = (_entry(content_ref="task:prior"), _entry(content_ref="task:current"))
    situation = _situation(*entries)
    before = situation
    projector.project(situation=situation)
    assert situation == before
    assert situation.entries == entries


def test_projection_does_not_mutate_runtime_content_authority() -> None:
    projector, authority = _projector(**{"task:prior": "payload", "task:current": "current"})
    situation = _situation(_entry(content_ref="task:prior"), _entry(content_ref="task:current"))

    projector.project(situation=situation)

    assert authority.resolve(content_ref="task:prior") == "payload"
    assert authority.resolve(content_ref="task:current") == "current"
    with pytest.raises(RuntimeContentReferenceNotFoundError):
        authority.resolve(content_ref="task:never-registered")


# --- constructor ---------------------------------------------------------


def test_constructor_rejects_invalid_runtime_content_authority() -> None:
    with pytest.raises(TypeError, match="runtime_content_authority"):
        PriorTaskContextProjector(runtime_content_authority="not-an-authority")  # type: ignore[arg-type]
