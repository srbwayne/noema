from dataclasses import FrozenInstanceError, fields, replace
from datetime import timedelta
from math import inf, nan

import pytest

from noema.cognition.domain.context_composition import (
    ContextCandidate,
    ContextPackageZone,
    ContextSensitivity,
    ContextSlice,
    ContextSliceType,
    ContextTrustLevel,
)
from noema.cognition.domain.errors import InvalidContextCandidateError


def context_slice() -> ContextSlice:
    return ContextSlice(
        slice_type=ContextSliceType.SITUATION,
        content_ref="situation:123",
        zone=ContextPackageZone.COGNITIVE_STATE,
        sensitivity=ContextSensitivity.INTERNAL,
        trust=ContextTrustLevel.TRUSTED,
        instruction_authority=None,
        provenance_ref="situation-model:7",
        token_estimate=120,
    )


def candidate() -> ContextCandidate:
    return ContextCandidate(context_slice=context_slice(), relevance=0.5, age=timedelta(minutes=2))


def test_context_candidate_has_exact_fields() -> None:
    assert tuple(field.name for field in fields(ContextCandidate)) == (
        "context_slice",
        "relevance",
        "age",
    )


def test_context_candidate_accepts_context_slice() -> None:
    assert candidate().context_slice == context_slice()


@pytest.mark.parametrize("value", [None, "slice", {}, ()])
def test_context_candidate_rejects_invalid_context_slice(value: object) -> None:
    with pytest.raises(InvalidContextCandidateError, match="context_slice"):
        replace(candidate(), context_slice=value)


@pytest.mark.parametrize("value", [0.0, 0.5, 1.0])
def test_context_candidate_accepts_normalized_float_relevance(value: float) -> None:
    assert replace(candidate(), relevance=value).relevance == value


@pytest.mark.parametrize("value", [-0.01, 1.01, nan, inf, -inf, True, False, 0, 1, None])
def test_context_candidate_rejects_invalid_relevance(value: object) -> None:
    with pytest.raises(InvalidContextCandidateError, match="relevance"):
        replace(candidate(), relevance=value)


@pytest.mark.parametrize(
    "value",
    [None, timedelta(0), timedelta(microseconds=1), timedelta(days=10)],
)
def test_context_candidate_accepts_valid_age(value: timedelta | None) -> None:
    assert replace(candidate(), age=value).age == value


@pytest.mark.parametrize(
    "value",
    [timedelta(microseconds=-1), -1, 0, 1.0, True, "1 day"],
)
def test_context_candidate_rejects_invalid_age(value: object) -> None:
    with pytest.raises(InvalidContextCandidateError, match="age"):
        replace(candidate(), age=value)


def test_context_candidate_is_immutable_and_structurally_equal() -> None:
    assert candidate() == candidate()
    with pytest.raises(FrozenInstanceError):
        candidate().relevance = 0.8
