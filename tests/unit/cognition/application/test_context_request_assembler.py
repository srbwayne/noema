import inspect
from dataclasses import replace
from datetime import timedelta
from typing import get_type_hints

import pytest

from noema.cognition.application import ContextRequestAssembler
from noema.cognition.application.cognitive_state_owner import CognitiveStateOwner
from noema.cognition.domain.context import ContextStamp, ContextVersionMarker
from noema.cognition.domain.context_composition import (
    ContextRequest,
    ContextSensitivity,
    ContextSliceType,
    ContextTrustLevel,
    InstructionAuthority,
)
from noema.cognition.domain.errors import InvalidContextRequestError
from noema.cognition.domain.modes import CognitiveMode
from noema.cognition.domain.situation import SituationModel
from noema.cognition.domain.workspace import CognitiveWorkspace, WorkspaceBudget


def _budget() -> WorkspaceBudget:
    # Fixture data only. These numbers are not a runtime WorkspaceBudget policy.
    return WorkspaceBudget(max_active_items=4, max_working_items=4, max_peripheral_items=4)


def _workspace(*, version: int = 0) -> CognitiveWorkspace:
    workspace = CognitiveWorkspace(budget=_budget())
    if version == 0:
        return workspace
    return replace(workspace, version=version)


def _situation(*, version: int = 0) -> SituationModel:
    situation = SituationModel()
    if version == 0:
        return situation
    return replace(situation, version=version)


def _owner(*, workspace_version: int = 0, situation_version: int = 0) -> CognitiveStateOwner:
    return CognitiveStateOwner(
        workspace=_workspace(version=workspace_version),
        situation=_situation(version=situation_version),
    )


def _assemble_kwargs() -> dict[str, object]:
    # Fixture policy values only; not runtime defaults.
    return {
        "role": "reasoner",
        "task_ref": "task:123",
        "goal_ref": None,
        "mode": CognitiveMode.DELIBERATE,
        "required_slice_types": (),
        "forbidden_slice_types": (),
        "max_sensitivity": ContextSensitivity.INTERNAL,
        "minimum_trust": ContextTrustLevel.UNVERIFIED,
        "allowed_authorities": (),
        "max_age": None,
        "max_tokens": 100,
    }


class _CountingStateOwner(CognitiveStateOwner):
    """A CognitiveStateOwner that records how often current_snapshots is called."""

    __slots__ = ("current_snapshots_call_count",)

    def __init__(self, *, workspace: CognitiveWorkspace, situation: SituationModel) -> None:
        super().__init__(workspace=workspace, situation=situation)
        self.current_snapshots_call_count = 0

    def current_snapshots(self) -> tuple[CognitiveWorkspace, SituationModel]:
        self.current_snapshots_call_count += 1
        return super().current_snapshots()


def test_context_request_assembler_has_exact_slots() -> None:
    assert ContextRequestAssembler.__slots__ == ("_state_owner",)


def test_context_request_assembler_instances_have_no_dict() -> None:
    assembler = ContextRequestAssembler(state_owner=_owner())
    assert not hasattr(assembler, "__dict__")


def test_context_request_assembler_constructor_is_keyword_only() -> None:
    owner = _owner()
    with pytest.raises(TypeError):
        ContextRequestAssembler(owner)  # type: ignore[misc]
    ContextRequestAssembler(state_owner=owner)


def test_context_request_assembler_constructor_type_hint_is_cognitive_state_owner() -> None:
    hints = get_type_hints(ContextRequestAssembler.__init__)
    assert hints["state_owner"] is CognitiveStateOwner


def test_constructor_rejects_non_cognitive_state_owner() -> None:
    with pytest.raises(TypeError, match="CognitiveStateOwner"):
        ContextRequestAssembler(state_owner=object())  # type: ignore[arg-type]


def test_constructor_retains_the_exact_state_owner() -> None:
    owner = _owner()
    assembler = ContextRequestAssembler(state_owner=owner)
    assert assembler._state_owner is owner


def test_public_surface_is_only_assemble() -> None:
    public_members = {name for name in vars(ContextRequestAssembler) if not name.startswith("_")}
    assert public_members == {"assemble"}


def test_forbidden_operations_are_not_exposed() -> None:
    for forbidden in (
        "build_context_stamp",
        "compose",
        "execute",
        "run",
        "observe",
        "current_snapshots",
        "reason",
        "create",
    ):
        assert not hasattr(ContextRequestAssembler, forbidden)


def test_assemble_has_exact_keyword_only_signature() -> None:
    signature = inspect.signature(ContextRequestAssembler.assemble)
    parameters = list(signature.parameters)
    assert parameters == [
        "self",
        "role",
        "task_ref",
        "goal_ref",
        "mode",
        "required_slice_types",
        "forbidden_slice_types",
        "max_sensitivity",
        "minimum_trust",
        "allowed_authorities",
        "max_age",
        "max_tokens",
    ]
    assert "context_stamp" not in signature.parameters
    for name, parameter in signature.parameters.items():
        if name == "self":
            continue
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
        assert parameter.default is inspect.Parameter.empty


def test_assemble_return_type_hint_is_context_request() -> None:
    hints = get_type_hints(ContextRequestAssembler.assemble)
    assert hints["return"] is ContextRequest


def test_assemble_returns_a_context_request() -> None:
    assembler = ContextRequestAssembler(state_owner=_owner())
    request = assembler.assemble(**_assemble_kwargs())  # type: ignore[arg-type]
    assert isinstance(request, ContextRequest)
    assert isinstance(request.context_stamp, ContextStamp)


def test_assemble_calls_current_snapshots_exactly_once() -> None:
    owner = _CountingStateOwner(workspace=_workspace(), situation=_situation())
    assembler = ContextRequestAssembler(state_owner=owner)

    assembler.assemble(**_assemble_kwargs())  # type: ignore[arg-type]

    assert owner.current_snapshots_call_count == 1


def test_assemble_maps_observed_workspace_and_situation_versions() -> None:
    assembler = ContextRequestAssembler(
        state_owner=_owner(workspace_version=3, situation_version=7)
    )

    request = assembler.assemble(**_assemble_kwargs())  # type: ignore[arg-type]

    assert request.context_stamp.workspace_version == 3
    assert request.context_stamp.situation_version == 7


def test_assemble_preserves_large_non_zero_versions() -> None:
    assembler = ContextRequestAssembler(
        state_owner=_owner(workspace_version=42, situation_version=99)
    )

    request = assembler.assemble(**_assemble_kwargs())  # type: ignore[arg-type]

    assert request.context_stamp.workspace_version == 42
    assert request.context_stamp.situation_version == 99


def test_assemble_uses_unmaterialized_markers_for_identity_goal_policy() -> None:
    assembler = ContextRequestAssembler(state_owner=_owner())

    request = assembler.assemble(**_assemble_kwargs())  # type: ignore[arg-type]

    assert request.context_stamp.identity_version is ContextVersionMarker.UNMATERIALIZED
    assert request.context_stamp.goal_version is ContextVersionMarker.UNMATERIALIZED
    assert request.context_stamp.policy_version is ContextVersionMarker.UNMATERIALIZED


def test_marker_dimensions_are_not_assemble_parameters() -> None:
    parameters = inspect.signature(ContextRequestAssembler.assemble).parameters
    assert "identity_version" not in parameters
    assert "goal_version" not in parameters
    assert "policy_version" not in parameters


def test_assemble_forwards_every_caller_field_unchanged() -> None:
    assembler = ContextRequestAssembler(state_owner=_owner())
    required_slice_types = (ContextSliceType.TASK, ContextSliceType.GOAL)
    forbidden_slice_types = (ContextSliceType.MEMORY,)
    allowed_authorities = (InstructionAuthority.USER_EXPLICIT,)
    max_age = timedelta(minutes=5)

    request = assembler.assemble(
        role="planner",
        task_ref="task:abc",
        goal_ref="goal:1",
        mode=CognitiveMode.FAST,
        required_slice_types=required_slice_types,
        forbidden_slice_types=forbidden_slice_types,
        max_sensitivity=ContextSensitivity.SECRET,
        minimum_trust=ContextTrustLevel.TRUSTED,
        allowed_authorities=allowed_authorities,
        max_age=max_age,
        max_tokens=512,
    )

    assert request.role == "planner"
    assert request.task_ref == "task:abc"
    assert request.goal_ref == "goal:1"
    assert request.mode is CognitiveMode.FAST
    assert request.required_slice_types is required_slice_types
    assert request.forbidden_slice_types is forbidden_slice_types
    assert request.max_sensitivity is ContextSensitivity.SECRET
    assert request.minimum_trust is ContextTrustLevel.TRUSTED
    assert request.allowed_authorities is allowed_authorities
    assert request.max_age is max_age
    assert request.max_tokens == 512


def test_assemble_does_not_normalize_caller_string_whitespace() -> None:
    assembler = ContextRequestAssembler(state_owner=_owner())
    kwargs = _assemble_kwargs()
    kwargs["role"] = "  reasoner  "

    request = assembler.assemble(**kwargs)  # type: ignore[arg-type]

    assert request.role == "  reasoner  "


def test_assemble_propagates_context_request_domain_error_unwrapped() -> None:
    assembler = ContextRequestAssembler(state_owner=_owner())
    kwargs = _assemble_kwargs()
    kwargs["role"] = ""

    with pytest.raises(InvalidContextRequestError):
        assembler.assemble(**kwargs)  # type: ignore[arg-type]


def test_assemble_accepts_non_empty_required_slice_types() -> None:
    assembler = ContextRequestAssembler(state_owner=_owner())
    kwargs = _assemble_kwargs()
    kwargs["required_slice_types"] = (ContextSliceType.TASK,)

    request = assembler.assemble(**kwargs)  # type: ignore[arg-type]

    assert request.required_slice_types == (ContextSliceType.TASK,)


def test_sequential_assembly_reflects_canonical_state_replacements() -> None:
    workspace = _workspace()
    situation = _situation()
    owner = CognitiveStateOwner(workspace=workspace, situation=situation)
    assembler = ContextRequestAssembler(state_owner=owner)

    first = assembler.assemble(**_assemble_kwargs())  # type: ignore[arg-type]
    assert first.context_stamp.workspace_version == workspace.version
    assert first.context_stamp.situation_version == situation.version

    owner.replace_workspace(replace(workspace, version=workspace.version + 1))
    owner.replace_situation(replace(situation, version=situation.version + 1))

    second = assembler.assemble(**_assemble_kwargs())  # type: ignore[arg-type]
    assert second.context_stamp.workspace_version == workspace.version + 1
    assert second.context_stamp.situation_version == situation.version + 1


def test_assemblers_bound_to_distinct_owners_are_isolated() -> None:
    assembler_a = ContextRequestAssembler(
        state_owner=_owner(workspace_version=2, situation_version=5)
    )
    assembler_b = ContextRequestAssembler(
        state_owner=_owner(workspace_version=8, situation_version=1)
    )

    stamp_a = assembler_a.assemble(**_assemble_kwargs()).context_stamp  # type: ignore[arg-type]
    stamp_b = assembler_b.assemble(**_assemble_kwargs()).context_stamp  # type: ignore[arg-type]

    assert (stamp_a.workspace_version, stamp_a.situation_version) == (2, 5)
    assert (stamp_b.workspace_version, stamp_b.situation_version) == (8, 1)


def test_application_package_exports_context_request_assembler() -> None:
    from noema.cognition import application

    assert "ContextRequestAssembler" in application.__all__
