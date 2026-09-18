import inspect
from dataclasses import replace
from datetime import timedelta
from typing import get_type_hints

import pytest

from noema.cognition.application import ContextRequestAssembler
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


def _assemble_kwargs(**overrides: object) -> dict[str, object]:
    # Fixture policy values only; not runtime defaults.
    kwargs: dict[str, object] = {
        "workspace": _workspace(),
        "situation": _situation(),
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
        "max_total_content_size": 100,
    }
    kwargs.update(overrides)
    return kwargs


def test_context_request_assembler_has_exact_slots() -> None:
    assert ContextRequestAssembler.__slots__ == ()


def test_context_request_assembler_instances_have_no_dict() -> None:
    assembler = ContextRequestAssembler()
    assert not hasattr(assembler, "__dict__")


def test_context_request_assembler_constructor_takes_no_arguments() -> None:
    with pytest.raises(TypeError):
        ContextRequestAssembler(object())  # type: ignore[call-arg]
    ContextRequestAssembler()


def test_context_request_assembler_has_no_state_owner_dependency() -> None:
    assert not hasattr(ContextRequestAssembler(), "_state_owner")
    hints = get_type_hints(ContextRequestAssembler.__init__)
    assert "state_owner" not in hints


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
        "workspace",
        "situation",
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
        "max_total_content_size",
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


def test_assemble_type_hints_for_snapshot_parameters_are_exact() -> None:
    hints = get_type_hints(ContextRequestAssembler.assemble)
    assert hints["workspace"] is CognitiveWorkspace
    assert hints["situation"] is SituationModel


def test_assemble_returns_a_context_request() -> None:
    assembler = ContextRequestAssembler()
    request = assembler.assemble(**_assemble_kwargs())  # type: ignore[arg-type]
    assert isinstance(request, ContextRequest)
    assert isinstance(request.context_stamp, ContextStamp)


def test_assemble_rejects_non_cognitive_workspace() -> None:
    assembler = ContextRequestAssembler()
    with pytest.raises(TypeError, match="workspace"):
        assembler.assemble(**_assemble_kwargs(workspace=object()))  # type: ignore[arg-type]


def test_assemble_rejects_non_situation_model() -> None:
    assembler = ContextRequestAssembler()
    with pytest.raises(TypeError, match="situation"):
        assembler.assemble(**_assemble_kwargs(situation=object()))  # type: ignore[arg-type]


def test_assemble_performs_no_canonical_state_observation() -> None:
    import noema.cognition.application.context_request_assembler as module

    assert not hasattr(module, "CognitiveStateOwner")
    source = inspect.getsource(module)
    assert "current_snapshots" not in source


def test_assemble_maps_supplied_workspace_and_situation_versions() -> None:
    assembler = ContextRequestAssembler()

    request = assembler.assemble(
        **_assemble_kwargs(
            workspace=_workspace(version=3),
            situation=_situation(version=7),
        )
    )  # type: ignore[arg-type]

    assert request.context_stamp.workspace_version == 3
    assert request.context_stamp.situation_version == 7


def test_assemble_preserves_large_non_zero_versions() -> None:
    assembler = ContextRequestAssembler()

    request = assembler.assemble(
        **_assemble_kwargs(
            workspace=_workspace(version=42),
            situation=_situation(version=99),
        )
    )  # type: ignore[arg-type]

    assert request.context_stamp.workspace_version == 42
    assert request.context_stamp.situation_version == 99


def test_assemble_uses_unmaterialized_markers_for_identity_goal_policy() -> None:
    assembler = ContextRequestAssembler()

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
    assembler = ContextRequestAssembler()
    required_slice_types = (ContextSliceType.TASK, ContextSliceType.GOAL)
    forbidden_slice_types = (ContextSliceType.MEMORY,)
    allowed_authorities = (InstructionAuthority.USER_EXPLICIT,)
    max_age = timedelta(minutes=5)

    request = assembler.assemble(
        workspace=_workspace(),
        situation=_situation(),
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
        max_total_content_size=512,
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
    assert request.max_total_content_size == 512


def test_assemble_does_not_normalize_caller_string_whitespace() -> None:
    assembler = ContextRequestAssembler()
    kwargs = _assemble_kwargs()
    kwargs["role"] = "  reasoner  "

    request = assembler.assemble(**kwargs)  # type: ignore[arg-type]

    assert request.role == "  reasoner  "


def test_assemble_propagates_context_request_domain_error_unwrapped() -> None:
    assembler = ContextRequestAssembler()
    kwargs = _assemble_kwargs()
    kwargs["role"] = ""

    with pytest.raises(InvalidContextRequestError):
        assembler.assemble(**kwargs)  # type: ignore[arg-type]


def test_assemble_accepts_non_empty_required_slice_types() -> None:
    assembler = ContextRequestAssembler()
    kwargs = _assemble_kwargs()
    kwargs["required_slice_types"] = (ContextSliceType.TASK,)

    request = assembler.assemble(**kwargs)  # type: ignore[arg-type]

    assert request.required_slice_types == (ContextSliceType.TASK,)


def test_sequential_assembly_reflects_supplied_snapshots() -> None:
    assembler = ContextRequestAssembler()

    first = assembler.assemble(
        **_assemble_kwargs(workspace=_workspace(version=0), situation=_situation(version=0))
    )  # type: ignore[arg-type]
    assert first.context_stamp.workspace_version == 0
    assert first.context_stamp.situation_version == 0

    second = assembler.assemble(
        **_assemble_kwargs(workspace=_workspace(version=1), situation=_situation(version=1))
    )  # type: ignore[arg-type]
    assert second.context_stamp.workspace_version == 1
    assert second.context_stamp.situation_version == 1


def test_assembler_instances_are_stateless_and_reusable() -> None:
    assembler = ContextRequestAssembler()

    stamp_a = assembler.assemble(
        **_assemble_kwargs(workspace=_workspace(version=2), situation=_situation(version=5))
    ).context_stamp  # type: ignore[arg-type]
    stamp_b = assembler.assemble(
        **_assemble_kwargs(workspace=_workspace(version=8), situation=_situation(version=1))
    ).context_stamp  # type: ignore[arg-type]

    assert (stamp_a.workspace_version, stamp_a.situation_version) == (2, 5)
    assert (stamp_b.workspace_version, stamp_b.situation_version) == (8, 1)


def test_application_package_exports_context_request_assembler() -> None:
    from noema.cognition import application

    assert "ContextRequestAssembler" in application.__all__
