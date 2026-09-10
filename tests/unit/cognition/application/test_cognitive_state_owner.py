from dataclasses import replace
from uuid import uuid4

import pytest

from noema.cognition.application import (
    CognitiveStateOwner,
    InvalidCognitiveStateReplacementError,
)
from noema.cognition.domain.situation import SituationModel
from noema.cognition.domain.workspace import CognitiveWorkspace, WorkspaceBudget


def _budget() -> WorkspaceBudget:
    # Test data only. These numbers are not a runtime WorkspaceBudget policy.
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


def _workspace_successor(current: CognitiveWorkspace) -> CognitiveWorkspace:
    return replace(current, version=current.version + 1)


def _situation_successor(current: SituationModel) -> SituationModel:
    return replace(current, version=current.version + 1)


def test_cognitive_state_owner_has_exact_slots() -> None:
    assert CognitiveStateOwner.__slots__ == ("_workspace", "_situation")


def test_cognitive_state_owner_instances_have_no_dict() -> None:
    owner = CognitiveStateOwner(workspace=_workspace(), situation=_situation())
    assert not hasattr(owner, "__dict__")


def test_cognitive_state_owner_constructor_is_keyword_only() -> None:
    workspace = _workspace()
    situation = _situation()
    with pytest.raises(TypeError):
        CognitiveStateOwner(workspace, situation)  # type: ignore[misc]
    CognitiveStateOwner(workspace=workspace, situation=situation)


def test_cognitive_state_owner_public_surface() -> None:
    public_members = {name for name in vars(CognitiveStateOwner) if not name.startswith("_")}
    assert public_members == {"current_snapshots", "replace_workspace", "replace_situation"}


def test_constructor_retains_supplied_snapshots() -> None:
    workspace = _workspace()
    situation = _situation()

    owner = CognitiveStateOwner(workspace=workspace, situation=situation)

    canonical_workspace, canonical_situation = owner.current_snapshots()
    assert canonical_workspace is workspace
    assert canonical_situation is situation


def test_current_snapshots_returns_workspace_situation_pair_in_order() -> None:
    owner = CognitiveStateOwner(workspace=_workspace(), situation=_situation())

    snapshots = owner.current_snapshots()

    assert isinstance(snapshots, tuple)
    assert len(snapshots) == 2
    assert isinstance(snapshots[0], CognitiveWorkspace)
    assert isinstance(snapshots[1], SituationModel)


def test_constructor_rejects_non_workspace() -> None:
    with pytest.raises(TypeError, match="CognitiveWorkspace"):
        CognitiveStateOwner(workspace=object(), situation=_situation())  # type: ignore[arg-type]


def test_constructor_rejects_non_situation() -> None:
    with pytest.raises(TypeError, match="SituationModel"):
        CognitiveStateOwner(workspace=_workspace(), situation=object())  # type: ignore[arg-type]


def test_constructor_accepts_non_zero_initial_versions() -> None:
    workspace = _workspace(version=5)
    situation = _situation(version=5)

    owner = CognitiveStateOwner(workspace=workspace, situation=situation)

    canonical_workspace, canonical_situation = owner.current_snapshots()
    assert canonical_workspace is workspace
    assert canonical_situation is situation


def test_same_object_workspace_replacement_is_a_noop() -> None:
    workspace = _workspace()
    owner = CognitiveStateOwner(workspace=workspace, situation=_situation())

    assert owner.replace_workspace(workspace) is None
    assert owner.current_snapshots()[0] is workspace


def test_same_object_situation_replacement_is_a_noop() -> None:
    situation = _situation()
    owner = CognitiveStateOwner(workspace=_workspace(), situation=situation)

    assert owner.replace_situation(situation) is None
    assert owner.current_snapshots()[1] is situation


def test_exact_successor_workspace_replacement_becomes_canonical() -> None:
    workspace = _workspace()
    owner = CognitiveStateOwner(workspace=workspace, situation=_situation())
    successor = _workspace_successor(workspace)

    owner.replace_workspace(successor)

    assert owner.current_snapshots()[0] is successor


def test_exact_successor_situation_replacement_becomes_canonical() -> None:
    situation = _situation()
    owner = CognitiveStateOwner(workspace=_workspace(), situation=situation)
    successor = _situation_successor(situation)

    owner.replace_situation(successor)

    assert owner.current_snapshots()[1] is successor


def test_successor_validation_is_relative_to_the_supplied_initial_version() -> None:
    initial = _workspace(version=5)
    owner = CognitiveStateOwner(workspace=initial, situation=_situation())

    # A jump from the initial version 5 straight to 7 is rejected.
    with pytest.raises(InvalidCognitiveStateReplacementError):
        owner.replace_workspace(replace(initial, version=7))
    assert owner.current_snapshots()[0] is initial

    # The exact successor 6 is accepted and becomes canonical.
    successor_six = replace(initial, version=6)
    owner.replace_workspace(successor_six)
    assert owner.current_snapshots()[0] is successor_six

    # From the new canonical version 6, a jump to 8 is rejected.
    with pytest.raises(InvalidCognitiveStateReplacementError):
        owner.replace_workspace(replace(successor_six, version=8))
    assert owner.current_snapshots()[0] is successor_six


def test_workspace_replacement_rejects_wrong_type() -> None:
    workspace = _workspace()
    owner = CognitiveStateOwner(workspace=workspace, situation=_situation())

    with pytest.raises(TypeError, match="CognitiveWorkspace"):
        owner.replace_workspace(object())  # type: ignore[arg-type]
    assert owner.current_snapshots()[0] is workspace


def test_workspace_replacement_rejects_different_identifier() -> None:
    workspace = _workspace()
    owner = CognitiveStateOwner(workspace=workspace, situation=_situation())
    foreign = replace(workspace, workspace_id=uuid4(), version=workspace.version + 1)

    with pytest.raises(InvalidCognitiveStateReplacementError, match="workspace_id"):
        owner.replace_workspace(foreign)
    assert owner.current_snapshots()[0] is workspace


def test_workspace_replacement_rejects_stale_version() -> None:
    workspace = _workspace(version=2)
    owner = CognitiveStateOwner(workspace=workspace, situation=_situation())
    stale = replace(workspace, version=1)

    with pytest.raises(InvalidCognitiveStateReplacementError, match="version"):
        owner.replace_workspace(stale)
    assert owner.current_snapshots()[0] is workspace


def test_workspace_replacement_rejects_equal_version_different_object() -> None:
    workspace = _workspace()
    owner = CognitiveStateOwner(workspace=workspace, situation=_situation())
    twin = replace(workspace)

    assert twin is not workspace
    with pytest.raises(InvalidCognitiveStateReplacementError, match="version"):
        owner.replace_workspace(twin)
    assert owner.current_snapshots()[0] is workspace


def test_workspace_replacement_rejects_version_jump() -> None:
    workspace = _workspace()
    owner = CognitiveStateOwner(workspace=workspace, situation=_situation())
    jumped = replace(workspace, version=workspace.version + 2)

    with pytest.raises(InvalidCognitiveStateReplacementError, match="version"):
        owner.replace_workspace(jumped)
    assert owner.current_snapshots()[0] is workspace


def test_situation_replacement_rejects_wrong_type() -> None:
    situation = _situation()
    owner = CognitiveStateOwner(workspace=_workspace(), situation=situation)

    with pytest.raises(TypeError, match="SituationModel"):
        owner.replace_situation(object())  # type: ignore[arg-type]
    assert owner.current_snapshots()[1] is situation


def test_situation_replacement_rejects_different_identifier() -> None:
    situation = _situation()
    owner = CognitiveStateOwner(workspace=_workspace(), situation=situation)
    foreign = replace(situation, situation_id=uuid4(), version=situation.version + 1)

    with pytest.raises(InvalidCognitiveStateReplacementError, match="situation_id"):
        owner.replace_situation(foreign)
    assert owner.current_snapshots()[1] is situation


def test_situation_replacement_rejects_stale_version() -> None:
    situation = _situation(version=2)
    owner = CognitiveStateOwner(workspace=_workspace(), situation=situation)
    stale = replace(situation, version=1)

    with pytest.raises(InvalidCognitiveStateReplacementError, match="version"):
        owner.replace_situation(stale)
    assert owner.current_snapshots()[1] is situation


def test_situation_replacement_rejects_equal_version_different_object() -> None:
    situation = _situation()
    owner = CognitiveStateOwner(workspace=_workspace(), situation=situation)
    twin = replace(situation)

    assert twin is not situation
    with pytest.raises(InvalidCognitiveStateReplacementError, match="version"):
        owner.replace_situation(twin)
    assert owner.current_snapshots()[1] is situation


def test_situation_replacement_rejects_version_jump() -> None:
    situation = _situation()
    owner = CognitiveStateOwner(workspace=_workspace(), situation=situation)
    jumped = replace(situation, version=situation.version + 2)

    with pytest.raises(InvalidCognitiveStateReplacementError, match="version"):
        owner.replace_situation(jumped)
    assert owner.current_snapshots()[1] is situation


def test_owner_instances_are_isolated() -> None:
    workspace_a = _workspace()
    situation_a = _situation()
    workspace_b = _workspace()
    situation_b = _situation()
    owner_a = CognitiveStateOwner(workspace=workspace_a, situation=situation_a)
    owner_b = CognitiveStateOwner(workspace=workspace_b, situation=situation_b)

    owner_a.replace_workspace(_workspace_successor(workspace_a))
    owner_a.replace_situation(_situation_successor(situation_a))

    assert owner_a.current_snapshots()[0].version == workspace_a.version + 1
    assert owner_a.current_snapshots()[1].version == situation_a.version + 1
    assert owner_b.current_snapshots() == (workspace_b, situation_b)


def test_application_package_exports_cognitive_state_owner() -> None:
    from noema.cognition import application

    assert "CognitiveStateOwner" in application.__all__
    assert "InvalidCognitiveStateReplacementError" in application.__all__
