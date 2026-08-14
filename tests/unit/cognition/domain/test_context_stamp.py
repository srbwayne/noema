from dataclasses import FrozenInstanceError

import pytest

from noema.cognition.domain.context import ContextStamp
from noema.cognition.domain.errors import InvalidContextVersionError

VERSION_FIELDS = (
    "workspace_version",
    "situation_version",
    "identity_version",
    "goal_version",
    "policy_version",
)


def context_stamp(**overrides: int) -> ContextStamp:
    versions = dict.fromkeys(VERSION_FIELDS, 0)
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
def test_context_stamp_rejects_each_negative_version(field_name: str) -> None:
    with pytest.raises(InvalidContextVersionError, match=field_name):
        context_stamp(**{field_name: -1})


def test_context_stamp_is_immutable() -> None:
    stamp = context_stamp()

    with pytest.raises(FrozenInstanceError):
        stamp.workspace_version = 1


def test_context_stamp_has_structural_equality() -> None:
    assert ContextStamp(1, 2, 3, 4, 5) == ContextStamp(1, 2, 3, 4, 5)
    assert ContextStamp(1, 2, 3, 4, 5) != ContextStamp(1, 2, 3, 4, 6)
