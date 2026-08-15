from dataclasses import FrozenInstanceError, replace

import pytest

from noema.cognition.domain.context_composition import (
    ContextPackageZone,
    ContextSensitivity,
    ContextSlice,
    ContextSliceType,
    ContextTrustLevel,
    InstructionAuthority,
)
from noema.cognition.domain.errors import InvalidContextSliceError


def context_slice() -> ContextSlice:
    return ContextSlice(
        slice_type=ContextSliceType.SITUATION,
        content_ref="situation:123",
        zone=ContextPackageZone.COGNITIVE_STATE,
        sensitivity=ContextSensitivity.INTERNAL,
        trust=ContextTrustLevel.TRUSTED,
        instruction_authority=InstructionAuthority.COGNITIVE_CONTROL,
        provenance_ref="situation-model:7",
        token_estimate=120,
    )


@pytest.mark.parametrize(
    "field_name,value",
    [
        ("slice_type", "situation"),
        ("slice_type", None),
        ("zone", "cognitive_state"),
        ("zone", None),
        ("sensitivity", "internal"),
        ("sensitivity", None),
        ("trust", "trusted"),
        ("trust", None),
    ],
)
def test_context_slice_requires_classification_enums(field_name: str, value: object) -> None:
    with pytest.raises(InvalidContextSliceError, match=field_name):
        replace(context_slice(), **{field_name: value})


@pytest.mark.parametrize("field_name", ["content_ref", "provenance_ref"])
@pytest.mark.parametrize("value", ["", "   ", 1, True, None])
def test_context_slice_rejects_invalid_refs(field_name: str, value: object) -> None:
    with pytest.raises(InvalidContextSliceError, match=field_name):
        replace(context_slice(), **{field_name: value})


@pytest.mark.parametrize("value", [None, InstructionAuthority.EXTERNAL_DATA])
def test_context_slice_accepts_optional_instruction_authority(
    value: InstructionAuthority | None,
) -> None:
    assert replace(context_slice(), instruction_authority=value).instruction_authority is value


@pytest.mark.parametrize("value", ["external_data", 1, True])
def test_context_slice_rejects_invalid_instruction_authority(value: object) -> None:
    with pytest.raises(InvalidContextSliceError, match="instruction_authority"):
        replace(context_slice(), instruction_authority=value)


@pytest.mark.parametrize("value", [0, 1, 1000])
def test_context_slice_accepts_non_negative_token_estimate(value: int) -> None:
    assert replace(context_slice(), token_estimate=value).token_estimate == value


@pytest.mark.parametrize("value", [-1, True, False, 1.0, None])
def test_context_slice_rejects_invalid_token_estimate(value: object) -> None:
    with pytest.raises(InvalidContextSliceError, match="token_estimate"):
        replace(context_slice(), token_estimate=value)


def test_context_slice_is_immutable_and_structurally_equal() -> None:
    assert context_slice() == context_slice()
    with pytest.raises(FrozenInstanceError):
        context_slice().content_ref = "other"
