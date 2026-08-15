from dataclasses import FrozenInstanceError, replace
from datetime import timedelta

import pytest

from noema.cognition.domain.context import ContextStamp
from noema.cognition.domain.context_composition import (
    ContextRequest,
    ContextSensitivity,
    ContextSliceType,
    ContextTrustLevel,
    InstructionAuthority,
)
from noema.cognition.domain.errors import InvalidContextRequestError
from noema.cognition.domain.modes import CognitiveMode


def request() -> ContextRequest:
    return ContextRequest(
        role="reasoner",
        task_ref="task:123",
        goal_ref="goal:456",
        mode=CognitiveMode.DELIBERATE,
        required_slice_types=(ContextSliceType.TASK, ContextSliceType.SITUATION),
        forbidden_slice_types=(ContextSliceType.HISTORY,),
        max_sensitivity=ContextSensitivity.PRIVATE,
        minimum_trust=ContextTrustLevel.UNVERIFIED,
        allowed_authorities=(
            InstructionAuthority.SYSTEM_POLICY,
            InstructionAuthority.USER_EXPLICIT,
        ),
        max_age=timedelta(minutes=5),
        max_tokens=2048,
        context_stamp=ContextStamp(
            workspace_version=1,
            situation_version=2,
            identity_version=3,
            goal_version=4,
            policy_version=5,
        ),
    )


@pytest.mark.parametrize("field_name", ["role", "task_ref"])
@pytest.mark.parametrize("value", ["", "   ", 1, True, None])
def test_context_request_rejects_invalid_required_refs(field_name: str, value: object) -> None:
    with pytest.raises(InvalidContextRequestError, match=field_name):
        replace(request(), **{field_name: value})


@pytest.mark.parametrize("value", [None, "goal:123"])
def test_context_request_accepts_valid_goal_ref(value: str | None) -> None:
    assert replace(request(), goal_ref=value).goal_ref == value


@pytest.mark.parametrize("value", ["", "   ", 1, True])
def test_context_request_rejects_invalid_goal_ref(value: object) -> None:
    with pytest.raises(InvalidContextRequestError, match="goal_ref"):
        replace(request(), goal_ref=value)


@pytest.mark.parametrize("value", ["fast", 1, None])
def test_context_request_requires_cognitive_mode(value: object) -> None:
    with pytest.raises(InvalidContextRequestError, match="mode"):
        replace(request(), mode=value)


@pytest.mark.parametrize("field_name", ["required_slice_types", "forbidden_slice_types"])
@pytest.mark.parametrize(
    "value",
    [
        [ContextSliceType.TASK],
        ("task",),
        (ContextSensitivity.PUBLIC,),
        (ContextSliceType.TASK, ContextSliceType.TASK),
    ],
)
def test_context_request_rejects_invalid_slice_type_tuples(field_name: str, value: object) -> None:
    with pytest.raises(InvalidContextRequestError, match=field_name):
        replace(request(), **{field_name: value})


def test_context_request_accepts_empty_slice_type_tuples() -> None:
    current = replace(request(), required_slice_types=(), forbidden_slice_types=())
    assert current.required_slice_types == ()
    assert current.forbidden_slice_types == ()


def test_context_request_rejects_required_forbidden_intersection() -> None:
    with pytest.raises(InvalidContextRequestError, match="disjoint"):
        replace(request(), forbidden_slice_types=(ContextSliceType.TASK,))


@pytest.mark.parametrize(
    "field_name,value",
    [
        ("max_sensitivity", "private"),
        ("max_sensitivity", None),
        ("minimum_trust", "trusted"),
        ("minimum_trust", None),
    ],
)
def test_context_request_requires_classification_enums(field_name: str, value: object) -> None:
    with pytest.raises(InvalidContextRequestError, match=field_name):
        replace(request(), **{field_name: value})


@pytest.mark.parametrize(
    "value",
    [
        [],
        ("system_policy",),
        (ContextSensitivity.PUBLIC,),
        (InstructionAuthority.SYSTEM_POLICY, InstructionAuthority.SYSTEM_POLICY),
        None,
    ],
)
def test_context_request_rejects_invalid_allowed_authorities(value: object) -> None:
    with pytest.raises(InvalidContextRequestError, match="allowed_authorities"):
        replace(request(), allowed_authorities=value)


def test_context_request_accepts_empty_allowed_authorities() -> None:
    assert replace(request(), allowed_authorities=()).allowed_authorities == ()


@pytest.mark.parametrize("value", [None, timedelta(microseconds=1), timedelta(seconds=60)])
def test_context_request_accepts_valid_max_age(value: timedelta | None) -> None:
    assert replace(request(), max_age=value).max_age == value


@pytest.mark.parametrize(
    "value", [timedelta(0), timedelta(seconds=-1), 0, 1, 1.0, True, "60", object()]
)
def test_context_request_rejects_invalid_max_age(value: object) -> None:
    with pytest.raises(InvalidContextRequestError, match="max_age"):
        replace(request(), max_age=value)


@pytest.mark.parametrize("value", [1, 5000])
def test_context_request_accepts_positive_max_tokens(value: int) -> None:
    assert replace(request(), max_tokens=value).max_tokens == value


@pytest.mark.parametrize("value", [0, -1, True, False, 1.0, None])
def test_context_request_rejects_invalid_max_tokens(value: object) -> None:
    with pytest.raises(InvalidContextRequestError, match="max_tokens"):
        replace(request(), max_tokens=value)


@pytest.mark.parametrize("value", [(), {}, None])
def test_context_request_requires_context_stamp(value: object) -> None:
    with pytest.raises(InvalidContextRequestError, match="context_stamp"):
        replace(request(), context_stamp=value)


def test_context_request_is_immutable_and_structurally_equal() -> None:
    assert request() == request()
    with pytest.raises(FrozenInstanceError):
        request().role = "planner"
