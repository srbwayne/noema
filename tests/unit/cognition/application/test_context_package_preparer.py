import inspect
import math
from dataclasses import replace
from datetime import timedelta
from typing import get_type_hints

import pytest

from noema.cognition.application import (
    ContextPackagePreparer,
    ContextRelevanceAuthority,
    ContextRequestAssembler,
    InvalidContextRelevanceResultError,
    NormalizedExactTaskContentRelevanceAuthority,
    PriorTaskContextProjector,
    RuntimeContentReferenceAuthority,
)
from noema.cognition.application.cognitive_state_owner import CognitiveStateOwner
from noema.cognition.domain.context_composition import (
    ContextCandidate,
    ContextComposer,
    ContextCompositionPolicy,
    ContextPackage,
    ContextPackageZone,
    ContextSensitivity,
    ContextSlice,
    ContextSliceType,
    ContextTrustLevel,
)
from noema.cognition.domain.errors import ContextCompositionUnsatisfiedError
from noema.cognition.domain.modes import CognitiveMode
from noema.cognition.domain.situation import SituationEntry, SituationEntryKind, SituationModel
from noema.cognition.domain.workspace import CognitiveWorkspace, WorkspaceBudget


def _workspace_budget() -> WorkspaceBudget:
    return WorkspaceBudget(max_active_items=4, max_working_items=4, max_peripheral_items=4)


def _workspace(*, version: int = 0) -> CognitiveWorkspace:
    workspace = CognitiveWorkspace(budget=_workspace_budget())
    if version == 0:
        return workspace
    return replace(workspace, version=version)


def _situation(*entries: SituationEntry, version: int = 0) -> SituationModel:
    situation = SituationModel(entries=entries)
    if version == 0:
        return situation
    return replace(situation, version=version)


def _owner(
    *,
    workspace: CognitiveWorkspace | None = None,
    situation: SituationModel | None = None,
) -> CognitiveStateOwner:
    return CognitiveStateOwner(
        workspace=workspace if workspace is not None else _workspace(),
        situation=situation if situation is not None else _situation(),
    )


class _CountingStateOwner(CognitiveStateOwner):
    __slots__ = ("current_snapshots_call_count", "returned_pairs")

    def __init__(self, *, workspace: CognitiveWorkspace, situation: SituationModel) -> None:
        super().__init__(workspace=workspace, situation=situation)
        self.current_snapshots_call_count = 0
        self.returned_pairs: list[tuple[CognitiveWorkspace, SituationModel]] = []

    def current_snapshots(self) -> tuple[CognitiveWorkspace, SituationModel]:
        self.current_snapshots_call_count += 1
        pair = super().current_snapshots()
        self.returned_pairs.append(pair)
        return pair


class _SpyProjector(PriorTaskContextProjector):
    __slots__ = ("project_calls", "_candidates")

    def __init__(
        self,
        *,
        runtime_content_authority: RuntimeContentReferenceAuthority,
        candidates: tuple[ContextCandidate, ...] = (),
    ) -> None:
        super().__init__(runtime_content_authority=runtime_content_authority)
        self.project_calls: list[SituationModel] = []
        self._candidates = candidates

    def project(self, *, situation: SituationModel) -> tuple[ContextCandidate, ...]:
        self.project_calls.append(situation)
        return self._candidates


def _composer_spy(
    *, policy: ContextCompositionPolicy, result: ContextPackage
) -> tuple[ContextComposer, list[object]]:
    """Return a ``ContextComposer`` subclass instance and its live call log.

    Uses a closure-captured list rather than extra instance slots, so it
    never has to fight the frozen/slotted base dataclass's own
    ``__setattr__``.
    """
    calls: list[object] = []

    class _SpyComposer(ContextComposer):
        def compose(self, *, request: object, candidates: object) -> ContextPackage:
            calls.append((request, candidates))
            return result

    return _SpyComposer(policy=policy), calls


def _task_slice(*, content_ref: str = "task:prior") -> ContextSlice:
    return ContextSlice(
        slice_type=ContextSliceType.TASK,
        content_ref=content_ref,
        zone=ContextPackageZone.COGNITIVE_STATE,
        sensitivity=ContextSensitivity.SECRET,
        trust=ContextTrustLevel.UNVERIFIED,
        instruction_authority=None,
        provenance_ref="provenance:1",
        content_size=5,
    )


def _candidate(*, content_ref: str = "task:prior") -> ContextCandidate:
    return ContextCandidate(
        context_slice=_task_slice(content_ref=content_ref), relevance=None, age=None
    )


def _policy() -> ContextCompositionPolicy:
    return ContextCompositionPolicy(minimum_relevance=0.0, max_slices=3)


def _prepare_kwargs(**overrides: object) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "role": "reasoner",
        "task_ref": "task:current",
        "goal_ref": None,
        "mode": CognitiveMode.DELIBERATE,
        "required_slice_types": (),
        "forbidden_slice_types": (),
        "max_sensitivity": ContextSensitivity.SECRET,
        "minimum_trust": ContextTrustLevel.UNVERIFIED,
        "allowed_authorities": (),
        "max_age": None,
        "max_total_content_size": 1000,
    }
    kwargs.update(overrides)
    return kwargs


def _disabled_preparer(
    *, state_owner: CognitiveStateOwner, projector: PriorTaskContextProjector | None = None
) -> ContextPackagePreparer:
    authority = RuntimeContentReferenceAuthority()
    return ContextPackagePreparer(
        state_owner=state_owner,
        context_request_assembler=ContextRequestAssembler(),
        prior_task_context_projector=projector
        if projector is not None
        else PriorTaskContextProjector(runtime_content_authority=authority),
        context_composer=None,
        prior_task_context_enabled=False,
    )


# --- constructor invariants --------------------------------------------------


def test_constructor_rejects_invalid_state_owner() -> None:
    authority = RuntimeContentReferenceAuthority()
    with pytest.raises(TypeError, match="state_owner"):
        ContextPackagePreparer(
            state_owner=object(),  # type: ignore[arg-type]
            context_request_assembler=ContextRequestAssembler(),
            prior_task_context_projector=PriorTaskContextProjector(
                runtime_content_authority=authority
            ),
            context_composer=None,
            prior_task_context_enabled=False,
        )


def test_constructor_rejects_invalid_context_request_assembler() -> None:
    authority = RuntimeContentReferenceAuthority()
    with pytest.raises(TypeError, match="context_request_assembler"):
        ContextPackagePreparer(
            state_owner=_owner(),
            context_request_assembler=object(),  # type: ignore[arg-type]
            prior_task_context_projector=PriorTaskContextProjector(
                runtime_content_authority=authority
            ),
            context_composer=None,
            prior_task_context_enabled=False,
        )


def test_constructor_rejects_invalid_projector() -> None:
    with pytest.raises(TypeError, match="prior_task_context_projector"):
        ContextPackagePreparer(
            state_owner=_owner(),
            context_request_assembler=ContextRequestAssembler(),
            prior_task_context_projector=object(),  # type: ignore[arg-type]
            context_composer=None,
            prior_task_context_enabled=False,
        )


def test_constructor_rejects_non_bool_enabled_flag() -> None:
    authority = RuntimeContentReferenceAuthority()
    with pytest.raises(TypeError, match="prior_task_context_enabled"):
        ContextPackagePreparer(
            state_owner=_owner(),
            context_request_assembler=ContextRequestAssembler(),
            prior_task_context_projector=PriorTaskContextProjector(
                runtime_content_authority=authority
            ),
            context_composer=None,
            prior_task_context_enabled=1,  # type: ignore[arg-type]
        )


def test_constructor_rejects_enabled_with_no_composer() -> None:
    authority = RuntimeContentReferenceAuthority()
    with pytest.raises(TypeError, match="context_composer"):
        ContextPackagePreparer(
            state_owner=_owner(),
            context_request_assembler=ContextRequestAssembler(),
            prior_task_context_projector=PriorTaskContextProjector(
                runtime_content_authority=authority
            ),
            context_composer=None,
            prior_task_context_enabled=True,
        )


def test_constructor_rejects_disabled_with_composer_present() -> None:
    authority = RuntimeContentReferenceAuthority()
    with pytest.raises(TypeError, match="context_composer"):
        ContextPackagePreparer(
            state_owner=_owner(),
            context_request_assembler=ContextRequestAssembler(),
            prior_task_context_projector=PriorTaskContextProjector(
                runtime_content_authority=authority
            ),
            context_composer=ContextComposer(policy=_policy()),
            prior_task_context_enabled=False,
        )


def test_constructor_accepts_consistent_enabled_pair() -> None:
    authority = RuntimeContentReferenceAuthority()
    ContextPackagePreparer(
        state_owner=_owner(),
        context_request_assembler=ContextRequestAssembler(),
        prior_task_context_projector=PriorTaskContextProjector(runtime_content_authority=authority),
        context_composer=ContextComposer(policy=_policy()),
        prior_task_context_enabled=True,
    )


def test_prepare_return_type_hint_is_context_package() -> None:
    hints = get_type_hints(ContextPackagePreparer.prepare)
    assert hints["return"] is ContextPackage


def test_prepare_has_exact_keyword_only_signature() -> None:
    signature = inspect.signature(ContextPackagePreparer.prepare)
    for name, parameter in signature.parameters.items():
        if name == "self":
            continue
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY


# --- single-snapshot rule -----------------------------------------------------


def test_disabled_prepare_calls_current_snapshots_exactly_once() -> None:
    owner = _CountingStateOwner(workspace=_workspace(), situation=_situation())
    preparer = _disabled_preparer(state_owner=owner)

    preparer.prepare(**_prepare_kwargs())  # type: ignore[arg-type]

    assert owner.current_snapshots_call_count == 1


def test_enabled_prepare_with_candidates_calls_current_snapshots_exactly_once() -> None:
    owner = _CountingStateOwner(
        workspace=_workspace(),
        situation=_situation(
            SituationEntry(kind=SituationEntryKind.TASK, content_ref="task:prior"),
            SituationEntry(kind=SituationEntryKind.TASK, content_ref="task:current"),
        ),
    )
    authority = RuntimeContentReferenceAuthority()
    authority.register(content_ref="task:prior", payload="prior payload")
    projector = PriorTaskContextProjector(runtime_content_authority=authority)
    composer = ContextComposer(policy=_policy())
    preparer = ContextPackagePreparer(
        state_owner=owner,
        context_request_assembler=ContextRequestAssembler(),
        prior_task_context_projector=projector,
        context_composer=composer,
        prior_task_context_enabled=True,
    )

    preparer.prepare(**_prepare_kwargs())  # type: ignore[arg-type]

    assert owner.current_snapshots_call_count == 1


def test_same_snapshot_objects_feed_assembler_and_projector() -> None:
    situation = _situation(
        SituationEntry(kind=SituationEntryKind.TASK, content_ref="task:prior"),
        SituationEntry(kind=SituationEntryKind.TASK, content_ref="task:current"),
    )
    owner = _CountingStateOwner(workspace=_workspace(), situation=situation)
    authority = RuntimeContentReferenceAuthority()
    authority.register(content_ref="task:prior", payload="prior payload")
    projector = _SpyProjector(runtime_content_authority=authority, candidates=(_candidate(),))
    composer = ContextComposer(policy=_policy())
    preparer = ContextPackagePreparer(
        state_owner=owner,
        context_request_assembler=ContextRequestAssembler(),
        prior_task_context_projector=projector,
        context_composer=composer,
        prior_task_context_enabled=True,
    )

    result = preparer.prepare(**_prepare_kwargs())  # type: ignore[arg-type]

    observed_workspace, observed_situation = owner.returned_pairs[0]
    assert projector.project_calls == [observed_situation]
    assert result.request.context_stamp.situation_version == observed_situation.version
    assert result.request.context_stamp.workspace_version == observed_workspace.version


# --- disabled path -------------------------------------------------------------


def test_disabled_path_never_calls_projector() -> None:
    owner = _owner()
    authority = RuntimeContentReferenceAuthority()
    projector = _SpyProjector(runtime_content_authority=authority, candidates=(_candidate(),))
    preparer = _disabled_preparer(state_owner=owner, projector=projector)

    preparer.prepare(**_prepare_kwargs())  # type: ignore[arg-type]

    assert projector.project_calls == []


def test_disabled_path_returns_empty_package() -> None:
    owner = _owner()
    preparer = _disabled_preparer(state_owner=owner)

    result = preparer.prepare(**_prepare_kwargs())  # type: ignore[arg-type]

    assert isinstance(result, ContextPackage)
    assert result.slices == ()


def test_disabled_path_does_not_touch_required_slice_types() -> None:
    owner = _owner()
    preparer = _disabled_preparer(state_owner=owner)

    result = preparer.prepare(**_prepare_kwargs(required_slice_types=()))  # type: ignore[arg-type]

    assert result.request.required_slice_types == ()


# --- enabled path: zero candidates --------------------------------------------


def test_enabled_zero_candidates_does_not_call_composer() -> None:
    owner = _owner(
        situation=_situation(
            SituationEntry(kind=SituationEntryKind.TASK, content_ref="task:current")
        )
    )
    authority = RuntimeContentReferenceAuthority()
    projector = _SpyProjector(runtime_content_authority=authority, candidates=())
    policy = _policy()
    composer, compose_calls = _composer_spy(
        policy=policy,
        result=ContextPackage(request=_context_request_stub(), slices=()),  # type: ignore[arg-type]
    )
    preparer = ContextPackagePreparer(
        state_owner=owner,
        context_request_assembler=ContextRequestAssembler(),
        prior_task_context_projector=projector,
        context_composer=composer,
        prior_task_context_enabled=True,
    )

    result = preparer.prepare(**_prepare_kwargs())  # type: ignore[arg-type]

    assert len(projector.project_calls) == 1
    assert compose_calls == []
    assert result.slices == ()


def test_enabled_zero_candidates_does_not_inject_task() -> None:
    owner = _owner(
        situation=_situation(
            SituationEntry(kind=SituationEntryKind.TASK, content_ref="task:current")
        )
    )
    authority = RuntimeContentReferenceAuthority()
    projector = _SpyProjector(runtime_content_authority=authority, candidates=())
    composer = ContextComposer(policy=_policy())
    preparer = ContextPackagePreparer(
        state_owner=owner,
        context_request_assembler=ContextRequestAssembler(),
        prior_task_context_projector=projector,
        context_composer=composer,
        prior_task_context_enabled=True,
    )

    result = preparer.prepare(**_prepare_kwargs())  # type: ignore[arg-type]

    assert result.request.required_slice_types == ()


# --- enabled path: with candidates --------------------------------------------


def test_enabled_with_candidates_calls_projector_and_composer_exactly_once() -> None:
    situation = _situation(
        SituationEntry(kind=SituationEntryKind.TASK, content_ref="task:prior"),
        SituationEntry(kind=SituationEntryKind.TASK, content_ref="task:current"),
    )
    owner = _owner(situation=situation)
    authority = RuntimeContentReferenceAuthority()
    authority.register(content_ref="task:prior", payload="prior payload")
    projector = _SpyProjector(runtime_content_authority=authority, candidates=(_candidate(),))
    policy = _policy()
    expected_result = ContextPackage(request=_context_request_stub(), slices=())  # type: ignore[arg-type]
    composer, compose_calls = _composer_spy(policy=policy, result=expected_result)
    preparer = ContextPackagePreparer(
        state_owner=owner,
        context_request_assembler=ContextRequestAssembler(),
        prior_task_context_projector=projector,
        context_composer=composer,
        prior_task_context_enabled=True,
    )

    result = preparer.prepare(**_prepare_kwargs())  # type: ignore[arg-type]

    assert len(projector.project_calls) == 1
    assert len(compose_calls) == 1
    assert result is expected_result


def test_enabled_with_candidates_appends_task_exactly_once() -> None:
    situation = _situation(
        SituationEntry(kind=SituationEntryKind.TASK, content_ref="task:prior"),
        SituationEntry(kind=SituationEntryKind.TASK, content_ref="task:current"),
    )
    owner = _owner(situation=situation)
    authority = RuntimeContentReferenceAuthority()
    authority.register(content_ref="task:prior", payload="prior payload")
    projector = PriorTaskContextProjector(runtime_content_authority=authority)
    captured_requests = []

    class _CapturingComposer(ContextComposer):
        def compose(self, *, request: object, candidates: object) -> ContextPackage:
            captured_requests.append(request)
            return super().compose(request=request, candidates=candidates)  # type: ignore[arg-type]

    composer = _CapturingComposer(policy=_policy())
    preparer = ContextPackagePreparer(
        state_owner=owner,
        context_request_assembler=ContextRequestAssembler(),
        prior_task_context_projector=projector,
        context_composer=composer,
        prior_task_context_enabled=True,
    )

    preparer.prepare(**_prepare_kwargs(required_slice_types=()))  # type: ignore[arg-type]

    assert captured_requests[0].required_slice_types == (ContextSliceType.TASK,)


def test_task_already_in_baseline_required_types_is_not_duplicated() -> None:
    situation = _situation(
        SituationEntry(kind=SituationEntryKind.TASK, content_ref="task:prior"),
        SituationEntry(kind=SituationEntryKind.TASK, content_ref="task:current"),
    )
    owner = _owner(situation=situation)
    authority = RuntimeContentReferenceAuthority()
    authority.register(content_ref="task:prior", payload="prior payload")
    projector = PriorTaskContextProjector(runtime_content_authority=authority)
    captured_requests = []

    class _CapturingComposer(ContextComposer):
        def compose(self, *, request: object, candidates: object) -> ContextPackage:
            captured_requests.append(request)
            return super().compose(request=request, candidates=candidates)  # type: ignore[arg-type]

    composer = _CapturingComposer(policy=_policy())
    preparer = ContextPackagePreparer(
        state_owner=owner,
        context_request_assembler=ContextRequestAssembler(),
        prior_task_context_projector=projector,
        context_composer=composer,
        prior_task_context_enabled=True,
    )

    preparer.prepare(**_prepare_kwargs(required_slice_types=(ContextSliceType.TASK,)))  # type: ignore[arg-type]

    assert captured_requests[0].required_slice_types == (ContextSliceType.TASK,)


def test_baseline_required_type_ordering_is_preserved_before_task() -> None:
    situation = _situation(
        SituationEntry(kind=SituationEntryKind.TASK, content_ref="task:prior"),
        SituationEntry(kind=SituationEntryKind.TASK, content_ref="task:current"),
    )
    owner = _owner(situation=situation)
    authority = RuntimeContentReferenceAuthority()
    authority.register(content_ref="task:prior", payload="prior payload")
    projector = PriorTaskContextProjector(runtime_content_authority=authority)
    captured_requests = []

    class _CapturingComposer(ContextComposer):
        def compose(self, *, request: object, candidates: object) -> ContextPackage:
            captured_requests.append(request)
            return super().compose(request=request, candidates=candidates)  # type: ignore[arg-type]

    composer = _CapturingComposer(
        policy=ContextCompositionPolicy(minimum_relevance=0.0, max_slices=3)
    )
    preparer = ContextPackagePreparer(
        state_owner=owner,
        context_request_assembler=ContextRequestAssembler(),
        prior_task_context_projector=projector,
        context_composer=composer,
        prior_task_context_enabled=True,
    )

    # GOAL has no eligible candidate (the projector only ever produces TASK
    # candidates), so composition ultimately fails for GOAL -- but the
    # composer's own capture already ran before that failure, so it still
    # proves the ContextRequest's ordering: TASK appended after GOAL.
    with pytest.raises(ContextCompositionUnsatisfiedError):
        preparer.prepare(**_prepare_kwargs(required_slice_types=(ContextSliceType.GOAL,)))  # type: ignore[arg-type]

    assert captured_requests[0].required_slice_types == (
        ContextSliceType.GOAL,
        ContextSliceType.TASK,
    )


def test_composer_return_object_is_retained_exactly() -> None:
    situation = _situation(
        SituationEntry(kind=SituationEntryKind.TASK, content_ref="task:prior"),
        SituationEntry(kind=SituationEntryKind.TASK, content_ref="task:current"),
    )
    owner = _owner(situation=situation)
    authority = RuntimeContentReferenceAuthority()
    authority.register(content_ref="task:prior", payload="prior payload")
    projector = PriorTaskContextProjector(runtime_content_authority=authority)
    composer = ContextComposer(policy=_policy())
    preparer = ContextPackagePreparer(
        state_owner=owner,
        context_request_assembler=ContextRequestAssembler(),
        prior_task_context_projector=projector,
        context_composer=composer,
        prior_task_context_enabled=True,
    )

    result = preparer.prepare(**_prepare_kwargs())  # type: ignore[arg-type]

    assert len(result.slices) == 1
    assert result.slices[0].content_ref == "task:prior"


# --- failure propagation -------------------------------------------------------


def test_projector_failure_propagates_unchanged() -> None:
    from noema.cognition.application import RuntimeContentReferenceNotFoundError

    situation = _situation(
        SituationEntry(kind=SituationEntryKind.TASK, content_ref="task:unregistered"),
        SituationEntry(kind=SituationEntryKind.TASK, content_ref="task:current"),
    )
    owner = _owner(situation=situation)
    authority = RuntimeContentReferenceAuthority()
    projector = PriorTaskContextProjector(runtime_content_authority=authority)
    composer = ContextComposer(policy=_policy())
    preparer = ContextPackagePreparer(
        state_owner=owner,
        context_request_assembler=ContextRequestAssembler(),
        prior_task_context_projector=projector,
        context_composer=composer,
        prior_task_context_enabled=True,
    )

    with pytest.raises(RuntimeContentReferenceNotFoundError):
        preparer.prepare(**_prepare_kwargs())  # type: ignore[arg-type]


def test_context_request_construction_failure_propagates_unchanged() -> None:
    from noema.cognition.domain.errors import InvalidContextRequestError

    owner = _owner()
    preparer = _disabled_preparer(state_owner=owner)

    with pytest.raises(InvalidContextRequestError):
        preparer.prepare(**_prepare_kwargs(role=""))  # type: ignore[arg-type]


def test_composition_failure_propagates_unchanged() -> None:
    situation = _situation(
        SituationEntry(kind=SituationEntryKind.TASK, content_ref="task:prior"),
        SituationEntry(kind=SituationEntryKind.TASK, content_ref="task:current"),
    )
    owner = _owner(situation=situation)
    authority = RuntimeContentReferenceAuthority()
    authority.register(content_ref="task:prior", payload="prior payload")
    projector = PriorTaskContextProjector(runtime_content_authority=authority)
    # max_sensitivity below SECRET makes the projected candidate (SECRET/UNVERIFIED)
    # ineligible for the coverage it is required to satisfy.
    composer = ContextComposer(policy=_policy())
    preparer = ContextPackagePreparer(
        state_owner=owner,
        context_request_assembler=ContextRequestAssembler(),
        prior_task_context_projector=projector,
        context_composer=composer,
        prior_task_context_enabled=True,
    )

    with pytest.raises(ContextCompositionUnsatisfiedError):
        preparer.prepare(**_prepare_kwargs(max_sensitivity=ContextSensitivity.INTERNAL))  # type: ignore[arg-type]


def _context_request_stub() -> object:
    from noema.cognition.domain.context import ContextStamp, ContextVersionMarker
    from noema.cognition.domain.context_composition import ContextRequest

    return ContextRequest(
        role="reasoner",
        task_ref="task:current",
        goal_ref=None,
        mode=CognitiveMode.DELIBERATE,
        required_slice_types=(),
        forbidden_slice_types=(),
        max_sensitivity=ContextSensitivity.SECRET,
        minimum_trust=ContextTrustLevel.UNVERIFIED,
        allowed_authorities=(),
        max_age=None,
        max_total_content_size=1000,
        context_stamp=ContextStamp(
            workspace_version=0,
            situation_version=0,
            identity_version=ContextVersionMarker.UNMATERIALIZED,
            goal_version=ContextVersionMarker.UNMATERIALIZED,
            policy_version=ContextVersionMarker.UNMATERIALIZED,
        ),
    )


# --- relevance authority seam (ADR-0041) ----------------------------------------


class _SpyRelevanceAuthority:
    """Structural ``ContextRelevanceAuthority`` fake returning a fixed result."""

    def __init__(self, *, result: object = None, error: Exception | None = None) -> None:
        self.calls: list[tuple[str, tuple[ContextCandidate, ...]]] = []
        self._result = result
        self._error = error

    def judge(
        self, *, task_ref: str, candidates: tuple[ContextCandidate, ...]
    ) -> tuple[float | None, ...]:
        self.calls.append((task_ref, candidates))
        if self._error is not None:
            raise self._error
        if self._result is None:
            return tuple(None for _ in candidates)
        return self._result  # type: ignore[return-value]


class _FloatSubclass(float):
    pass


def _aged_candidate(*, content_ref: str, age: timedelta | None) -> ContextCandidate:
    return ContextCandidate(
        context_slice=_task_slice(content_ref=content_ref), relevance=None, age=age
    )


def _two_candidates() -> tuple[ContextCandidate, ...]:
    return (
        _aged_candidate(content_ref="task:prior:a", age=timedelta(seconds=5)),
        _aged_candidate(content_ref="task:prior:b", age=None),
    )


def _relevance_preparer(
    *,
    candidates: tuple[ContextCandidate, ...],
    relevance_authority: object,
    enabled: bool = True,
) -> tuple[ContextPackagePreparer, _SpyProjector, list[object]]:
    content_authority = RuntimeContentReferenceAuthority()
    projector = _SpyProjector(runtime_content_authority=content_authority, candidates=candidates)
    composer, compose_calls = _composer_spy(
        policy=_policy(),
        result=ContextPackage(request=_context_request_stub(), slices=()),  # type: ignore[arg-type]
    )
    preparer = ContextPackagePreparer(
        state_owner=_owner(),
        context_request_assembler=ContextRequestAssembler(),
        prior_task_context_projector=projector,
        context_composer=composer if enabled else None,
        prior_task_context_enabled=enabled,
        context_relevance_authority=relevance_authority,  # type: ignore[arg-type]
    )
    return preparer, projector, compose_calls


def _composed_candidates(compose_calls: list[object]) -> tuple[ContextCandidate, ...]:
    assert len(compose_calls) == 1
    _, candidates = compose_calls[0]  # type: ignore[misc]
    return candidates  # type: ignore[no-any-return]


def test_context_relevance_authority_is_a_keyword_only_parameter_defaulting_to_none() -> None:
    parameter = inspect.signature(ContextPackagePreparer).parameters["context_relevance_authority"]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default is None


def test_omitted_relevance_authority_preserves_existing_behavior() -> None:
    candidates = _two_candidates()
    content_authority = RuntimeContentReferenceAuthority()
    projector = _SpyProjector(runtime_content_authority=content_authority, candidates=candidates)
    composer, compose_calls = _composer_spy(
        policy=_policy(),
        result=ContextPackage(request=_context_request_stub(), slices=()),  # type: ignore[arg-type]
    )
    preparer = ContextPackagePreparer(
        state_owner=_owner(),
        context_request_assembler=ContextRequestAssembler(),
        prior_task_context_projector=projector,
        context_composer=composer,
        prior_task_context_enabled=True,
    )

    preparer.prepare(**_prepare_kwargs())  # type: ignore[arg-type]

    assert preparer._context_relevance_authority is None  # noqa: SLF001
    assert _composed_candidates(compose_calls) is candidates


def test_explicit_none_relevance_authority_preserves_existing_behavior() -> None:
    candidates = _two_candidates()
    preparer, _, compose_calls = _relevance_preparer(
        candidates=candidates, relevance_authority=None
    )

    preparer.prepare(**_prepare_kwargs())  # type: ignore[arg-type]

    composed = _composed_candidates(compose_calls)
    assert composed is candidates
    assert all(candidate.relevance is None for candidate in composed)


def test_constructor_rejects_invalid_relevance_authority() -> None:
    with pytest.raises(TypeError, match="context_relevance_authority"):
        _relevance_preparer(candidates=(), relevance_authority=object())


def test_constructor_accepts_structural_relevance_authority() -> None:
    authority = _SpyRelevanceAuthority()
    assert isinstance(authority, ContextRelevanceAuthority)

    preparer, _, _ = _relevance_preparer(candidates=(), relevance_authority=authority)

    assert preparer._context_relevance_authority is authority  # noqa: SLF001


def test_constructor_accepts_relevance_authority_with_disabled_prior_task_context() -> None:
    authority = _SpyRelevanceAuthority()
    preparer, _, _ = _relevance_preparer(
        candidates=(), relevance_authority=authority, enabled=False
    )
    assert preparer._context_relevance_authority is authority  # noqa: SLF001


def test_disabled_path_never_invokes_bound_relevance_authority() -> None:
    authority = _SpyRelevanceAuthority()
    preparer, projector, compose_calls = _relevance_preparer(
        candidates=_two_candidates(), relevance_authority=authority, enabled=False
    )

    result = preparer.prepare(**_prepare_kwargs())  # type: ignore[arg-type]

    assert authority.calls == []
    assert projector.project_calls == []
    assert compose_calls == []
    assert result.slices == ()


def test_zero_candidates_skip_relevance_authority() -> None:
    authority = _SpyRelevanceAuthority()
    preparer, projector, compose_calls = _relevance_preparer(
        candidates=(), relevance_authority=authority
    )

    result = preparer.prepare(**_prepare_kwargs())  # type: ignore[arg-type]

    assert len(projector.project_calls) == 1
    assert authority.calls == []
    assert compose_calls == []
    assert result.slices == ()
    assert result.request.required_slice_types == ()


def test_candidates_with_bound_authority_invoke_judge_exactly_once_with_exact_inputs() -> None:
    candidates = _two_candidates()
    authority = _SpyRelevanceAuthority()
    preparer, _, _ = _relevance_preparer(candidates=candidates, relevance_authority=authority)

    preparer.prepare(**_prepare_kwargs(task_ref="task:the-current-one"))  # type: ignore[arg-type]

    assert len(authority.calls) == 1
    task_ref, judged_candidates = authority.calls[0]
    assert task_ref == "task:the-current-one"
    assert judged_candidates is candidates


def test_result_values_are_applied_positionally() -> None:
    candidates = _two_candidates()
    authority = _SpyRelevanceAuthority(result=(None, 0.75))
    preparer, _, compose_calls = _relevance_preparer(
        candidates=candidates, relevance_authority=authority
    )

    preparer.prepare(**_prepare_kwargs())  # type: ignore[arg-type]

    composed = _composed_candidates(compose_calls)
    assert [candidate.relevance for candidate in composed] == [None, 0.75]
    assert [candidate.context_slice.content_ref for candidate in composed] == [
        "task:prior:a",
        "task:prior:b",
    ]


def test_reconstruction_preserves_context_slice_and_age_without_mutating_originals() -> None:
    candidates = _two_candidates()
    originals = tuple(replace(candidate) for candidate in candidates)
    authority = _SpyRelevanceAuthority(result=(1.0, 0.25))
    preparer, _, compose_calls = _relevance_preparer(
        candidates=candidates, relevance_authority=authority
    )

    preparer.prepare(**_prepare_kwargs())  # type: ignore[arg-type]

    composed = _composed_candidates(compose_calls)
    assert composed is not candidates
    assert len(composed) == len(candidates)
    for original, reconstructed in zip(candidates, composed, strict=True):
        assert reconstructed.context_slice is original.context_slice
        assert reconstructed.age is original.age
    assert candidates == originals
    assert all(candidate.relevance is None for candidate in candidates)


@pytest.mark.parametrize("value", [None, 0.0, 1.0, 0.5, _FloatSubclass(0.5)])
def test_valid_relevance_values_are_accepted(value: float | None) -> None:
    candidates = (_candidate(),)
    authority = _SpyRelevanceAuthority(result=(value,))
    preparer, _, compose_calls = _relevance_preparer(
        candidates=candidates, relevance_authority=authority
    )

    preparer.prepare(**_prepare_kwargs())  # type: ignore[arg-type]

    composed = _composed_candidates(compose_calls)
    assert composed[0].relevance is value


@pytest.mark.parametrize(
    "result",
    [
        [1.0, 1.0],
        (1.0,),
        (1.0, 1.0, 1.0),
        (1, None),
        (True, None),
        (math.nan, None),
        (math.inf, None),
        (-math.inf, None),
        (-0.1, None),
        (1.1, None),
        (None, "1.0"),
    ],
    ids=[
        "list-container",
        "shorter",
        "longer",
        "int",
        "bool",
        "nan",
        "positive-infinity",
        "negative-infinity",
        "negative",
        "above-one",
        "str",
    ],
)
def test_invalid_relevance_result_is_rejected_before_reconstruction(
    result: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    from noema.cognition.application import context_package_preparer

    replace_calls: list[object] = []

    def _recording_replace(obj: object, /, **changes: object) -> object:
        replace_calls.append(obj)
        return replace(obj, **changes)  # type: ignore[type-var]

    monkeypatch.setattr(context_package_preparer, "replace", _recording_replace)
    candidates = _two_candidates()
    authority = _SpyRelevanceAuthority(result=result)
    preparer, _, compose_calls = _relevance_preparer(
        candidates=candidates, relevance_authority=authority
    )

    with pytest.raises(InvalidContextRelevanceResultError):
        preparer.prepare(**_prepare_kwargs())  # type: ignore[arg-type]

    assert replace_calls == []
    assert compose_calls == []
    assert all(candidate.relevance is None for candidate in candidates)


def test_invalid_result_error_does_not_expose_resolved_content() -> None:
    content_authority = RuntimeContentReferenceAuthority()
    content_authority.register(content_ref="task:current", payload="SECRET-TASK-PAYLOAD")

    class _LeakyShapedAuthority:
        def judge(
            self, *, task_ref: str, candidates: tuple[ContextCandidate, ...]
        ) -> tuple[float | None, ...]:
            content_authority.resolve(content_ref=task_ref)
            return (2.0,)

    preparer, _, _ = _relevance_preparer(
        candidates=(_candidate(),), relevance_authority=_LeakyShapedAuthority()
    )

    with pytest.raises(InvalidContextRelevanceResultError) as excinfo:
        preparer.prepare(**_prepare_kwargs())  # type: ignore[arg-type]

    assert "SECRET-TASK-PAYLOAD" not in str(excinfo.value)
    assert "2.0" not in str(excinfo.value)


def test_relevance_authority_operational_failure_propagates_unchanged() -> None:
    error = RuntimeError("authority failed")
    authority = _SpyRelevanceAuthority(error=error)
    preparer, _, compose_calls = _relevance_preparer(
        candidates=_two_candidates(), relevance_authority=authority
    )

    with pytest.raises(RuntimeError) as excinfo:
        preparer.prepare(**_prepare_kwargs())  # type: ignore[arg-type]

    assert excinfo.value is error
    assert not isinstance(excinfo.value, InvalidContextRelevanceResultError)
    assert compose_calls == []


@pytest.mark.parametrize("result", [(None, None), (1.0, 1.0), (0.0, 0.0)])
def test_task_activation_depends_on_candidate_existence_not_relevance(
    result: tuple[float | None, ...],
) -> None:
    authority = _SpyRelevanceAuthority(result=result)
    preparer, _, compose_calls = _relevance_preparer(
        candidates=_two_candidates(), relevance_authority=authority
    )

    preparer.prepare(**_prepare_kwargs(required_slice_types=()))  # type: ignore[arg-type]

    request, _ = compose_calls[0]  # type: ignore[misc]
    assert request.required_slice_types == (ContextSliceType.TASK,)  # type: ignore[attr-defined]


def test_composer_receives_reconstructed_candidates_only_after_validation() -> None:
    order: list[str] = []
    candidates = _two_candidates()

    class _OrderedAuthority:
        def judge(
            self, *, task_ref: str, candidates: tuple[ContextCandidate, ...]
        ) -> tuple[float | None, ...]:
            order.append("judge")
            return (0.5, None)

    class _OrderedComposer(ContextComposer):
        def compose(self, *, request: object, candidates: object) -> ContextPackage:
            order.append("compose")
            assert [c.relevance for c in candidates] == [0.5, None]  # type: ignore[attr-defined]
            return super().compose(request=request, candidates=candidates)  # type: ignore[arg-type]

    content_authority = RuntimeContentReferenceAuthority()
    preparer = ContextPackagePreparer(
        state_owner=_owner(),
        context_request_assembler=ContextRequestAssembler(),
        prior_task_context_projector=_SpyProjector(
            runtime_content_authority=content_authority, candidates=candidates
        ),
        context_composer=_OrderedComposer(policy=_policy()),
        prior_task_context_enabled=True,
        context_relevance_authority=_OrderedAuthority(),
    )

    preparer.prepare(**_prepare_kwargs())  # type: ignore[arg-type]

    assert order == ["judge", "compose"]


def test_deterministic_realization_integrates_with_preparer() -> None:
    situation = _situation(
        SituationEntry(kind=SituationEntryKind.TASK, content_ref="task:prior"),
        SituationEntry(kind=SituationEntryKind.TASK, content_ref="task:current"),
    )
    content_authority = RuntimeContentReferenceAuthority()
    content_authority.register(content_ref="task:prior", payload="same question")
    content_authority.register(content_ref="task:current", payload="same question")
    captured: list[object] = []

    class _CapturingComposer(ContextComposer):
        def compose(self, *, request: object, candidates: object) -> ContextPackage:
            captured.append(candidates)
            return super().compose(request=request, candidates=candidates)  # type: ignore[arg-type]

    preparer = ContextPackagePreparer(
        state_owner=_owner(situation=situation),
        context_request_assembler=ContextRequestAssembler(),
        prior_task_context_projector=PriorTaskContextProjector(
            runtime_content_authority=content_authority
        ),
        context_composer=_CapturingComposer(policy=_policy()),
        prior_task_context_enabled=True,
        context_relevance_authority=NormalizedExactTaskContentRelevanceAuthority(
            runtime_content_authority=content_authority
        ),
    )

    preparer.prepare(**_prepare_kwargs())  # type: ignore[arg-type]

    assert [candidate.relevance for candidate in captured[0]] == [1.0]  # type: ignore[attr-defined]


# --- export --------------------------------------------------------------------


def test_application_package_exports_context_package_preparer() -> None:
    from noema.cognition import application

    assert "ContextPackagePreparer" in application.__all__


def test_application_package_exports_relevance_seam() -> None:
    from noema.cognition import application

    assert "ContextRelevanceAuthority" in application.__all__
    assert "InvalidContextRelevanceResultError" in application.__all__
    assert "NormalizedExactTaskContentRelevanceAuthority" in application.__all__
