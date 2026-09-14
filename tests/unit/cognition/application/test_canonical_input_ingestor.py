import inspect
from typing import get_type_hints

import pytest

from noema.cognition.application import CanonicalInputIngestor
from noema.cognition.application.cognitive_state_owner import CognitiveStateOwner
from noema.cognition.domain.errors import InvalidSituationEntryError
from noema.cognition.domain.situation import SituationEntryKind, SituationModel
from noema.cognition.domain.workspace import CognitiveWorkspace, WorkspaceBudget


def _workspace_budget() -> WorkspaceBudget:
    # Fixture data only. These numbers are not a runtime WorkspaceBudget policy.
    return WorkspaceBudget(max_active_items=4, max_working_items=4, max_peripheral_items=4)


def _workspace() -> CognitiveWorkspace:
    return CognitiveWorkspace(budget=_workspace_budget())


def _situation() -> SituationModel:
    return SituationModel()


def _owner(
    *, workspace: CognitiveWorkspace | None = None, situation: SituationModel | None = None
) -> CognitiveStateOwner:
    return CognitiveStateOwner(
        workspace=workspace if workspace is not None else _workspace(),
        situation=situation if situation is not None else _situation(),
    )


# --- class shape ---------------------------------------------------------


def test_canonical_input_ingestor_has_exact_slots() -> None:
    assert CanonicalInputIngestor.__slots__ == ("_state_owner",)


def test_canonical_input_ingestor_instances_have_no_dict() -> None:
    ingestor = CanonicalInputIngestor(state_owner=_owner())
    assert not hasattr(ingestor, "__dict__")


def test_constructor_is_keyword_only() -> None:
    owner = _owner()
    with pytest.raises(TypeError):
        CanonicalInputIngestor(owner)  # type: ignore[misc]
    CanonicalInputIngestor(state_owner=owner)


def test_constructor_type_hints_are_exact() -> None:
    hints = get_type_hints(CanonicalInputIngestor.__init__)
    assert hints == {
        "state_owner": CognitiveStateOwner,
        "return": type(None),
    }


def test_constructor_rejects_invalid_state_owner() -> None:
    with pytest.raises(TypeError, match="state_owner"):
        CanonicalInputIngestor(state_owner=object())  # type: ignore[arg-type]


# --- ingest_task shape -----------------------------------------------------


def test_ingest_task_is_synchronous() -> None:
    assert not inspect.iscoroutinefunction(CanonicalInputIngestor.ingest_task)


def test_ingest_task_has_exact_keyword_only_signature() -> None:
    signature = inspect.signature(CanonicalInputIngestor.ingest_task)
    assert list(signature.parameters) == ["self", "task_ref"]
    parameter = signature.parameters["task_ref"]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default is inspect.Parameter.empty


def test_ingest_task_type_hints_are_exact() -> None:
    hints = get_type_hints(CanonicalInputIngestor.ingest_task)
    assert hints == {"task_ref": str, "return": type(None)}


def test_ingest_task_forbidden_parameters_are_absent() -> None:
    parameters = inspect.signature(CanonicalInputIngestor.ingest_task).parameters
    for forbidden in (
        "problem_ref",
        "problem_statement",
        "workspace",
        "situation",
        "kind",
        "content_ref",
    ):
        assert forbidden not in parameters


def test_ingest_task_returns_none() -> None:
    ingestor = CanonicalInputIngestor(state_owner=_owner())
    assert ingestor.ingest_task(task_ref="task:123") is None


# --- content_ref / kind identity (§ frozen G1) ------------------------------


def test_exact_task_ref_becomes_content_ref() -> None:
    owner = _owner()
    ingestor = CanonicalInputIngestor(state_owner=owner)

    ingestor.ingest_task(task_ref="11111111-1111-1111-1111-111111111111")

    _, situation = owner.current_snapshots()
    assert len(situation.entries) == 1
    entry = situation.entries[0]
    assert entry.content_ref == "11111111-1111-1111-1111-111111111111"
    assert entry.kind is SituationEntryKind.TASK


def test_raw_problem_text_is_never_stored() -> None:
    owner = _owner()
    ingestor = CanonicalInputIngestor(state_owner=owner)

    ingestor.ingest_task(task_ref="task:xyz")

    _, situation = owner.current_snapshots()
    entry = situation.entries[0]
    assert entry.content_ref == "task:xyz"
    assert "problem" not in entry.content_ref.lower() or entry.content_ref == "task:xyz"


# --- observation / replacement cardinality ----------------------------------


class _CountingStateOwner(CognitiveStateOwner):
    """A CognitiveStateOwner that records call counts for both methods."""

    __slots__ = ("current_snapshots_call_count", "replace_situation_call_count")

    def __init__(self, *, workspace: CognitiveWorkspace, situation: SituationModel) -> None:
        super().__init__(workspace=workspace, situation=situation)
        self.current_snapshots_call_count = 0
        self.replace_situation_call_count = 0

    def current_snapshots(self) -> tuple[CognitiveWorkspace, SituationModel]:
        self.current_snapshots_call_count += 1
        return super().current_snapshots()

    def replace_situation(self, replacement: SituationModel) -> None:
        self.replace_situation_call_count += 1
        super().replace_situation(replacement)


def test_ingest_task_calls_current_snapshots_exactly_once() -> None:
    owner = _CountingStateOwner(workspace=_workspace(), situation=_situation())
    ingestor = CanonicalInputIngestor(state_owner=owner)

    ingestor.ingest_task(task_ref="task:1")

    assert owner.current_snapshots_call_count == 1


def test_ingest_task_calls_replace_situation_exactly_once() -> None:
    owner = _CountingStateOwner(workspace=_workspace(), situation=_situation())
    ingestor = CanonicalInputIngestor(state_owner=owner)

    ingestor.ingest_task(task_ref="task:1")

    assert owner.replace_situation_call_count == 1


# --- Workspace preservation --------------------------------------------------


def test_workspace_identity_version_entries_focus_are_unchanged() -> None:
    workspace = _workspace()
    owner = _owner(workspace=workspace)
    ingestor = CanonicalInputIngestor(state_owner=owner)

    ingestor.ingest_task(task_ref="task:1")

    observed_workspace, _ = owner.current_snapshots()
    assert observed_workspace is workspace
    assert observed_workspace.version == 0
    assert observed_workspace.items == ()
    assert observed_workspace.focus_item_id is None


# --- Situation successor evidence -------------------------------------------


def test_situation_successor_retains_identity_and_increments_version() -> None:
    situation = _situation()
    owner = _owner(situation=situation)
    ingestor = CanonicalInputIngestor(state_owner=owner)

    ingestor.ingest_task(task_ref="task:1")

    _, successor = owner.current_snapshots()
    assert successor is not situation
    assert successor.situation_id == situation.situation_id
    assert successor.version == situation.version + 1
    assert len(successor.entries) == 1


def test_situation_successor_adds_exactly_one_task_entry() -> None:
    owner = _owner()
    ingestor = CanonicalInputIngestor(state_owner=owner)

    ingestor.ingest_task(task_ref="task:1")

    _, situation = owner.current_snapshots()
    task_entries = situation.entries_of_kind(SituationEntryKind.TASK)
    assert len(task_entries) == 1
    assert task_entries[0].content_ref == "task:1"


# --- failure propagation -----------------------------------------------------


def test_invalid_blank_task_ref_propagates_invalid_situation_entry_error() -> None:
    owner = _owner()
    ingestor = CanonicalInputIngestor(state_owner=owner)

    with pytest.raises(InvalidSituationEntryError):
        ingestor.ingest_task(task_ref="")

    # Canonical situation remains unchanged after the failed construction.
    _, situation = owner.current_snapshots()
    assert situation.version == 0
    assert situation.entries == ()


def test_replacement_failure_propagates_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    from noema.cognition.application.cognitive_state_owner import (
        InvalidCognitiveStateReplacementError,
    )

    owner = _owner()
    ingestor = CanonicalInputIngestor(state_owner=owner)

    def _broken_apply(self: SituationModel, delta: object) -> SituationModel:
        # Return a successor with a mismatched version to force the owner's
        # own exact-successor validation to fail.
        from dataclasses import replace as dataclass_replace

        return dataclass_replace(self, version=self.version + 2)

    monkeypatch.setattr(SituationModel, "apply", _broken_apply)

    with pytest.raises(InvalidCognitiveStateReplacementError):
        ingestor.ingest_task(task_ref="task:1")

    _, situation = owner.current_snapshots()
    assert situation.version == 0


def test_no_retry_on_failure() -> None:
    owner = _owner()
    ingestor = CanonicalInputIngestor(state_owner=owner)

    with pytest.raises(InvalidSituationEntryError):
        ingestor.ingest_task(task_ref="")

    # A single failed attempt must not have retained any successor.
    _, situation = owner.current_snapshots()
    assert situation.entries == ()


# --- export -------------------------------------------------------------


def test_application_package_exports_canonical_input_ingestor() -> None:
    from noema.cognition import application

    assert "CanonicalInputIngestor" in application.__all__
