from dataclasses import FrozenInstanceError, fields, replace
from datetime import timedelta

import pytest

from noema.cognition.domain.context import ContextStamp
from noema.cognition.domain.context_composition import (
    ContextPackage,
    ContextPackageZone,
    ContextRequest,
    ContextSensitivity,
    ContextSlice,
    ContextSliceType,
    ContextTrustLevel,
    InstructionAuthority,
)
from noema.cognition.domain.errors import InvalidContextPackageError
from noema.cognition.domain.modes import CognitiveMode


def request() -> ContextRequest:
    return ContextRequest(
        role="reasoner",
        task_ref="task:123",
        goal_ref=None,
        mode=CognitiveMode.DELIBERATE,
        required_slice_types=(),
        forbidden_slice_types=(),
        max_sensitivity=ContextSensitivity.PRIVATE,
        minimum_trust=ContextTrustLevel.UNVERIFIED,
        allowed_authorities=(InstructionAuthority.SYSTEM_POLICY,),
        max_age=timedelta(minutes=5),
        max_tokens=100,
        context_stamp=ContextStamp(
            workspace_version=1,
            situation_version=2,
            identity_version=3,
            goal_version=4,
            policy_version=5,
        ),
    )


def context_slice(
    slice_type: ContextSliceType = ContextSliceType.SITUATION,
    *,
    content_ref: str = "situation:123",
    instruction_authority: InstructionAuthority | None = None,
    token_estimate: int = 20,
    sensitivity: ContextSensitivity = ContextSensitivity.INTERNAL,
    trust: ContextTrustLevel = ContextTrustLevel.TRUSTED,
) -> ContextSlice:
    return ContextSlice(
        slice_type=slice_type,
        content_ref=content_ref,
        zone=ContextPackageZone.COGNITIVE_STATE,
        sensitivity=sensitivity,
        trust=trust,
        instruction_authority=instruction_authority,
        provenance_ref=f"source:{content_ref}",
        token_estimate=token_estimate,
    )


def test_context_package_has_exact_fields() -> None:
    assert tuple(field.name for field in fields(ContextPackage)) == ("request", "slices")


def test_context_package_accepts_empty_slices_without_required_types() -> None:
    package = ContextPackage(request=request(), slices=())
    assert package.slices == ()
    assert package.total_token_estimate == 0


def test_context_package_rejects_empty_slices_with_required_type() -> None:
    required_request = replace(request(), required_slice_types=(ContextSliceType.TASK,))
    with pytest.raises(InvalidContextPackageError, match="required"):
        ContextPackage(request=required_request, slices=())


def test_context_package_covers_multiple_required_types() -> None:
    required_request = replace(
        request(),
        required_slice_types=(ContextSliceType.TASK, ContextSliceType.SITUATION),
    )
    slices = (
        context_slice(ContextSliceType.TASK, content_ref="task:123"),
        context_slice(ContextSliceType.SITUATION),
        context_slice(ContextSliceType.EVIDENCE, content_ref="evidence:123"),
    )
    assert ContextPackage(request=required_request, slices=slices).slices == slices


def test_context_package_rejects_missing_required_type() -> None:
    required_request = replace(
        request(),
        required_slice_types=(ContextSliceType.TASK, ContextSliceType.SITUATION),
    )
    with pytest.raises(InvalidContextPackageError, match="required"):
        ContextPackage(
            request=required_request,
            slices=(context_slice(ContextSliceType.TASK, content_ref="task:123"),),
        )


def test_context_package_rejects_forbidden_slice_type() -> None:
    forbidden_request = replace(request(), forbidden_slice_types=(ContextSliceType.MEMORY,))
    with pytest.raises(InvalidContextPackageError, match="forbidden"):
        ContextPackage(
            request=forbidden_request,
            slices=(context_slice(ContextSliceType.MEMORY, content_ref="memory:123"),),
        )


def test_context_package_accepts_allowed_instruction_authority() -> None:
    context = context_slice(
        ContextSliceType.POLICY,
        content_ref="policy:123",
        instruction_authority=InstructionAuthority.SYSTEM_POLICY,
    )
    assert ContextPackage(request=request(), slices=(context,)).slices == (context,)


def test_context_package_rejects_unauthorized_instruction_authority() -> None:
    context = context_slice(
        ContextSliceType.POLICY,
        content_ref="policy:123",
        instruction_authority=InstructionAuthority.USER_EXPLICIT,
    )
    with pytest.raises(InvalidContextPackageError, match="authorit"):
        ContextPackage(request=request(), slices=(context,))


def test_context_package_accepts_data_without_authority_when_none_are_allowed() -> None:
    no_authority_request = replace(request(), allowed_authorities=())
    context = context_slice(instruction_authority=None)
    assert ContextPackage(request=no_authority_request, slices=(context,)).slices == (context,)


@pytest.mark.parametrize("token_estimate", [0, 99, 100])
def test_context_package_accepts_token_total_within_limit(token_estimate: int) -> None:
    context = context_slice(token_estimate=token_estimate)
    package = ContextPackage(request=request(), slices=(context,))
    assert package.total_token_estimate == token_estimate


def test_context_package_rejects_token_total_above_limit() -> None:
    with pytest.raises(InvalidContextPackageError, match="token"):
        ContextPackage(request=request(), slices=(context_slice(token_estimate=101),))


def test_context_package_rejects_list_slices() -> None:
    with pytest.raises(InvalidContextPackageError, match="tuple"):
        ContextPackage(request=request(), slices=[context_slice()])


@pytest.mark.parametrize("value", [None, "slice", {}, ()])
def test_context_package_rejects_non_context_slice_element(value: object) -> None:
    with pytest.raises(InvalidContextPackageError, match="ContextSlice"):
        ContextPackage(request=request(), slices=(value,))


def test_context_package_rejects_structural_duplicate_slice() -> None:
    context = context_slice()
    with pytest.raises(InvalidContextPackageError, match="duplicate"):
        ContextPackage(request=request(), slices=(context, context))


def test_context_package_preserves_slice_order() -> None:
    first = context_slice(ContextSliceType.TASK, content_ref="task:123")
    second = context_slice(ContextSliceType.SITUATION)
    package = ContextPackage(request=request(), slices=(second, first))
    assert package.slices == (second, first)


def test_context_package_derives_total_token_estimate() -> None:
    slices = (
        context_slice(ContextSliceType.TASK, content_ref="task:123", token_estimate=30),
        context_slice(ContextSliceType.SITUATION, token_estimate=40),
    )
    assert ContextPackage(request=request(), slices=slices).total_token_estimate == 70


@pytest.mark.parametrize("value", [None, "request", {}, ()])
def test_context_package_rejects_invalid_request(value: object) -> None:
    with pytest.raises(InvalidContextPackageError, match="request"):
        ContextPackage(request=value, slices=())


def test_context_package_does_not_infer_sensitivity_or_trust_ordering() -> None:
    restrictive_request = replace(
        request(),
        max_sensitivity=ContextSensitivity.PUBLIC,
        minimum_trust=ContextTrustLevel.TRUSTED,
    )
    context = context_slice(
        sensitivity=ContextSensitivity.SECRET,
        trust=ContextTrustLevel.UNTRUSTED,
    )
    assert ContextPackage(request=restrictive_request, slices=(context,)).slices == (context,)


def test_context_package_is_immutable_and_structurally_equal() -> None:
    package = ContextPackage(request=request(), slices=(context_slice(),))
    assert package == ContextPackage(request=request(), slices=(context_slice(),))
    with pytest.raises(FrozenInstanceError):
        package.slices = ()
