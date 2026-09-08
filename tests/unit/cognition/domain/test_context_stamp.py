from dataclasses import FrozenInstanceError

import pytest

from noema.cognition.domain.context import ContextStamp, ContextVersionMarker
from noema.cognition.domain.errors import InvalidContextVersionError

VERSION_FIELDS = (
    "workspace_version",
    "situation_version",
    "identity_version",
    "goal_version",
    "policy_version",
)

OBSERVED_ONLY_FIELDS = (
    "workspace_version",
    "situation_version",
)

MARKER_ELIGIBLE_FIELDS = (
    "identity_version",
    "goal_version",
    "policy_version",
)


def context_stamp(**overrides: int | ContextVersionMarker) -> ContextStamp:
    versions: dict[str, int | ContextVersionMarker] = dict.fromkeys(VERSION_FIELDS, 0)
    versions.update(overrides)
    return ContextStamp(
        workspace_version=versions["workspace_version"],
        situation_version=versions["situation_version"],
        identity_version=versions["identity_version"],
        goal_version=versions["goal_version"],
        policy_version=versions["policy_version"],
    )


def test_context_stamp_accepts_zero_versions() -> None:
    assert context_stamp() == ContextStamp(0, 0, 0, 0, 0)


def test_context_stamp_accepts_positive_versions() -> None:
    stamp = ContextStamp(1, 2, 3, 4, 5)

    assert stamp.workspace_version == 1
    assert stamp.policy_version == 5


@pytest.mark.parametrize("field_name", VERSION_FIELDS)
@pytest.mark.parametrize("value", [0, 1, 10])
def test_context_stamp_accepts_each_valid_version(field_name: str, value: int) -> None:
    stamp = context_stamp(**{field_name: value})

    assert getattr(stamp, field_name) == value


@pytest.mark.parametrize("field_name", VERSION_FIELDS)
def test_context_stamp_rejects_each_negative_version(field_name: str) -> None:
    with pytest.raises(InvalidContextVersionError, match=field_name):
        context_stamp(**{field_name: -1})


@pytest.mark.parametrize("field_name", VERSION_FIELDS)
@pytest.mark.parametrize("value", [-1, True, False, 0.0, 1.0, 1.5, "1", None])
def test_context_stamp_rejects_each_invalid_runtime_type(
    field_name: str,
    value: object,
) -> None:
    with pytest.raises(InvalidContextVersionError, match=field_name):
        context_stamp(**{field_name: value})  # type: ignore[arg-type]


def test_context_stamp_is_immutable() -> None:
    stamp = context_stamp()

    with pytest.raises(FrozenInstanceError):
        stamp.workspace_version = 1


def test_context_stamp_has_structural_equality() -> None:
    assert ContextStamp(1, 2, 3, 4, 5) == ContextStamp(1, 2, 3, 4, 5)
    assert ContextStamp(1, 2, 3, 4, 5) != ContextStamp(1, 2, 3, 4, 6)


@pytest.mark.parametrize("field_name", MARKER_ELIGIBLE_FIELDS)
def test_context_stamp_accepts_unmaterialized_for_marker_eligible_fields(
    field_name: str,
) -> None:
    stamp = context_stamp(**{field_name: ContextVersionMarker.UNMATERIALIZED})

    assert getattr(stamp, field_name) is ContextVersionMarker.UNMATERIALIZED


def test_context_stamp_accepts_unmaterialized_independently_per_field() -> None:
    stamp = context_stamp(
        identity_version=ContextVersionMarker.UNMATERIALIZED,
        goal_version=0,
        policy_version=ContextVersionMarker.UNMATERIALIZED,
    )

    assert stamp.identity_version is ContextVersionMarker.UNMATERIALIZED
    assert stamp.goal_version == 0
    assert stamp.policy_version is ContextVersionMarker.UNMATERIALIZED


def test_context_stamp_accepts_unmaterialized_for_all_marker_eligible_fields() -> None:
    stamp = ContextStamp(
        workspace_version=0,
        situation_version=0,
        identity_version=ContextVersionMarker.UNMATERIALIZED,
        goal_version=ContextVersionMarker.UNMATERIALIZED,
        policy_version=ContextVersionMarker.UNMATERIALIZED,
    )

    assert stamp.workspace_version == 0
    assert stamp.situation_version == 0
    assert stamp.identity_version is ContextVersionMarker.UNMATERIALIZED
    assert stamp.goal_version is ContextVersionMarker.UNMATERIALIZED
    assert stamp.policy_version is ContextVersionMarker.UNMATERIALIZED


@pytest.mark.parametrize("field_name", OBSERVED_ONLY_FIELDS)
def test_context_stamp_rejects_unmaterialized_for_observed_only_fields(
    field_name: str,
) -> None:
    with pytest.raises(InvalidContextVersionError, match=field_name):
        context_stamp(**{field_name: ContextVersionMarker.UNMATERIALIZED})


@pytest.mark.parametrize("observed_value", [0, 1, -1])
def test_context_version_marker_unmaterialized_is_not_an_integer(
    observed_value: int,
) -> None:
    assert observed_value != ContextVersionMarker.UNMATERIALIZED
    assert not isinstance(ContextVersionMarker.UNMATERIALIZED, int)


def test_context_stamp_marker_state_has_structural_equality() -> None:
    marker_stamp = context_stamp(
        identity_version=ContextVersionMarker.UNMATERIALIZED,
        goal_version=ContextVersionMarker.UNMATERIALIZED,
        policy_version=ContextVersionMarker.UNMATERIALIZED,
    )
    same_marker_stamp = context_stamp(
        identity_version=ContextVersionMarker.UNMATERIALIZED,
        goal_version=ContextVersionMarker.UNMATERIALIZED,
        policy_version=ContextVersionMarker.UNMATERIALIZED,
    )
    observed_stamp = context_stamp(identity_version=0, goal_version=0, policy_version=0)

    assert marker_stamp == same_marker_stamp
    assert marker_stamp != observed_stamp
