import inspect
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from typing import get_type_hints

import pytest

from noema.cognition.application import (
    CanonicalInputIngestor,
    ContextRequestAssembler,
    DirectReasoningOperation,
    ReasoningEngine,
    RuntimeContentReferenceAuthority,
    RuntimeContentReferenceConflictError,
)
from noema.cognition.application.cognitive_state_owner import CognitiveStateOwner
from noema.cognition.domain.budget import CognitiveBudget
from noema.cognition.domain.context import ContextVersionMarker
from noema.cognition.domain.context_composition import (
    ContextRequest,
    ContextSensitivity,
    ContextSliceType,
    ContextTrustLevel,
    InstructionAuthority,
)
from noema.cognition.domain.errors import (
    InvalidContextPackageError,
    InvalidContextRequestError,
    InvalidReasoningRequestError,
)
from noema.cognition.domain.modes import CognitiveMode
from noema.cognition.domain.reasoning import (
    ReasoningOutcome,
    ReasoningRequest,
    ReasoningStatus,
    ReasoningStrategy,
)
from noema.cognition.domain.situation import SituationEntryKind, SituationModel
from noema.cognition.domain.workspace import CognitiveWorkspace, WorkspaceBudget
from noema.cognition.ports import ReasoningExecutionError


def _workspace_budget() -> WorkspaceBudget:
    # Fixture data only. These numbers are not a runtime WorkspaceBudget policy.
    return WorkspaceBudget(max_active_items=4, max_working_items=4, max_peripheral_items=4)


def _workspace(*, version: int = 0) -> CognitiveWorkspace:
    workspace = CognitiveWorkspace(budget=_workspace_budget())
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


class _CountingStateOwner(CognitiveStateOwner):
    """A CognitiveStateOwner that records an ordered log of canonical calls."""

    __slots__ = ("current_snapshots_call_count", "replace_situation_call_count", "call_log")

    def __init__(self, *, workspace: CognitiveWorkspace, situation: SituationModel) -> None:
        super().__init__(workspace=workspace, situation=situation)
        self.current_snapshots_call_count = 0
        self.replace_situation_call_count = 0
        self.call_log: list[str] = []

    def current_snapshots(self) -> tuple[CognitiveWorkspace, SituationModel]:
        self.current_snapshots_call_count += 1
        self.call_log.append("current_snapshots")
        return super().current_snapshots()

    def replace_situation(self, replacement: SituationModel) -> None:
        self.replace_situation_call_count += 1
        self.call_log.append("replace_situation")
        super().replace_situation(replacement)


class _SpyIngestor(CanonicalInputIngestor):
    """A CanonicalInputIngestor that records every ingest_task call.

    ``shared_events``, when supplied, is a single list this spy appends to
    live, at the exact moment ``ingest_task`` runs -- shared with another
    spy so relative call order between two independent collaborators can be
    proven, not just each collaborator's own occurrence.
    """

    __slots__ = ("ingest_task_calls", "_shared_events")

    def __init__(
        self,
        *,
        state_owner: CognitiveStateOwner,
        shared_events: list[str] | None = None,
    ) -> None:
        super().__init__(state_owner=state_owner)
        self.ingest_task_calls: list[str] = []
        self._shared_events = shared_events

    def ingest_task(self, *, task_ref: str) -> None:
        self.ingest_task_calls.append(task_ref)
        if self._shared_events is not None:
            self._shared_events.append("ingest")
        super().ingest_task(task_ref=task_ref)


class _SpyContentAuthority(RuntimeContentReferenceAuthority):
    """A RuntimeContentReferenceAuthority that records register/resolve calls.

    ``shared_events``, when supplied, is the same live-appended list a
    ``_SpyIngestor`` may also be given, so the two collaborators' calls can
    be observed on one shared, ordered timeline.
    """

    __slots__ = ("register_calls", "resolve_calls", "call_log", "_shared_events")

    def __init__(self, *, shared_events: list[str] | None = None) -> None:
        super().__init__()
        self.register_calls: list[tuple[str, str]] = []
        self.resolve_calls: list[str] = []
        self.call_log: list[str] = []
        self._shared_events = shared_events

    def register(self, *, content_ref: str, payload: str) -> None:
        self.register_calls.append((content_ref, payload))
        self.call_log.append("register")
        if self._shared_events is not None:
            self._shared_events.append("register")
        super().register(content_ref=content_ref, payload=payload)

    def resolve(self, *, content_ref: str) -> str:
        self.resolve_calls.append(content_ref)
        self.call_log.append("resolve")
        return super().resolve(content_ref=content_ref)


class SpyReasoningExecutor:
    """Records every request received and returns a preconfigured result."""

    def __init__(self, result: object) -> None:
        self._result = result
        self.received_requests: list[ReasoningRequest] = []
        self.call_count = 0

    async def execute(self, request: ReasoningRequest) -> ReasoningOutcome:
        self.received_requests.append(request)
        self.call_count += 1
        if isinstance(self._result, BaseException):
            raise self._result
        if isinstance(self._result, ReasoningOutcome) and (
            self._result.problem_ref != request.problem_ref
            or self._result.strategy is not request.strategy
        ):
            # Correlate the fixed outcome to this request, the same way a
            # real executor would, so the engine's correlation check passes
            # for tests that vary problem_ref/strategy. Tests asserting
            # outcome identity always use a request whose problem_ref and
            # strategy already match the configured outcome, so this branch
            # does not run for them and identity is preserved.
            return replace(
                self._result,
                problem_ref=request.problem_ref,
                strategy=request.strategy,
            )
        return self._result  # type: ignore[return-value]


def _budget() -> CognitiveBudget:
    # Fixture data only. These numbers are not a runtime CognitiveBudget policy.
    return CognitiveBudget(
        max_time=timedelta(seconds=1),
        max_steps=1,
        max_llm_calls=0,
        max_tool_calls=0,
        max_cost=Decimal("0"),
        max_tokens=0,
        max_search_depth=0,
    )


def _execute_kwargs(**overrides: object) -> dict[str, object]:
    # Fixture policy values only; not runtime defaults.
    kwargs: dict[str, object] = {
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
        "problem_ref": "problem:123",
        "problem_statement": "Determine an answer.",
        "budget": _budget(),
    }
    kwargs.update(overrides)
    return kwargs


def _completed_outcome(
    *,
    problem_ref: str = "problem:123",
    strategy: ReasoningStrategy = ReasoningStrategy.DIRECT,
) -> ReasoningOutcome:
    return ReasoningOutcome(
        problem_ref=problem_ref,
        strategy=strategy,
        status=ReasoningStatus.COMPLETED,
        conclusion="the answer",
        reason_summary="direct reasoning",
        information_needs=(),
    )


def _operation(
    *,
    owner: CognitiveStateOwner,
    executor: object,
    authority: RuntimeContentReferenceAuthority | None = None,
) -> tuple[DirectReasoningOperation, "SpyReasoningExecutor"]:
    ingestor = CanonicalInputIngestor(state_owner=owner)
    assembler = ContextRequestAssembler(state_owner=owner)
    engine = ReasoningEngine(executor=executor)  # type: ignore[arg-type]
    return (
        DirectReasoningOperation(
            runtime_content_authority=authority
            if authority is not None
            else RuntimeContentReferenceAuthority(),
            canonical_input_ingestor=ingestor,
            context_request_assembler=assembler,
            reasoning_engine=engine,
        ),
        executor,  # type: ignore[return-value]
    )


# --- class shape -------------------------------------------------------


def test_direct_reasoning_operation_has_exact_slots() -> None:
    assert DirectReasoningOperation.__slots__ == (
        "_runtime_content_authority",
        "_canonical_input_ingestor",
        "_context_request_assembler",
        "_reasoning_engine",
    )


def test_direct_reasoning_operation_instances_have_no_dict() -> None:
    owner = _owner()
    operation, _ = _operation(owner=owner, executor=SpyReasoningExecutor(_completed_outcome()))
    assert not hasattr(operation, "__dict__")


def test_constructor_is_keyword_only() -> None:
    owner = _owner()
    authority = RuntimeContentReferenceAuthority()
    ingestor = CanonicalInputIngestor(state_owner=owner)
    assembler = ContextRequestAssembler(state_owner=owner)
    engine = ReasoningEngine(executor=SpyReasoningExecutor(_completed_outcome()))
    with pytest.raises(TypeError):
        DirectReasoningOperation(authority, ingestor, assembler, engine)  # type: ignore[misc]
    DirectReasoningOperation(
        runtime_content_authority=authority,
        canonical_input_ingestor=ingestor,
        context_request_assembler=assembler,
        reasoning_engine=engine,
    )


def test_constructor_type_hints_are_exact() -> None:
    hints = get_type_hints(DirectReasoningOperation.__init__)
    assert hints == {
        "runtime_content_authority": RuntimeContentReferenceAuthority,
        "canonical_input_ingestor": CanonicalInputIngestor,
        "context_request_assembler": ContextRequestAssembler,
        "reasoning_engine": ReasoningEngine,
        "return": type(None),
    }


def test_constructor_rejects_invalid_runtime_content_authority() -> None:
    owner = _owner()
    ingestor = CanonicalInputIngestor(state_owner=owner)
    assembler = ContextRequestAssembler(state_owner=owner)
    engine = ReasoningEngine(executor=SpyReasoningExecutor(_completed_outcome()))
    with pytest.raises(TypeError, match="runtime_content_authority"):
        DirectReasoningOperation(
            runtime_content_authority=object(),  # type: ignore[arg-type]
            canonical_input_ingestor=ingestor,
            context_request_assembler=assembler,
            reasoning_engine=engine,
        )


def test_constructor_rejects_invalid_canonical_input_ingestor() -> None:
    owner = _owner()
    authority = RuntimeContentReferenceAuthority()
    assembler = ContextRequestAssembler(state_owner=owner)
    engine = ReasoningEngine(executor=SpyReasoningExecutor(_completed_outcome()))
    with pytest.raises(TypeError, match="canonical_input_ingestor"):
        DirectReasoningOperation(
            runtime_content_authority=authority,
            canonical_input_ingestor=object(),  # type: ignore[arg-type]
            context_request_assembler=assembler,
            reasoning_engine=engine,
        )


def test_constructor_rejects_invalid_context_request_assembler() -> None:
    owner = _owner()
    authority = RuntimeContentReferenceAuthority()
    ingestor = CanonicalInputIngestor(state_owner=owner)
    engine = ReasoningEngine(executor=SpyReasoningExecutor(_completed_outcome()))
    with pytest.raises(TypeError, match="context_request_assembler"):
        DirectReasoningOperation(
            runtime_content_authority=authority,
            canonical_input_ingestor=ingestor,
            context_request_assembler=object(),  # type: ignore[arg-type]
            reasoning_engine=engine,
        )


def test_constructor_rejects_invalid_reasoning_engine() -> None:
    owner = _owner()
    authority = RuntimeContentReferenceAuthority()
    ingestor = CanonicalInputIngestor(state_owner=owner)
    assembler = ContextRequestAssembler(state_owner=owner)
    with pytest.raises(TypeError, match="reasoning_engine"):
        DirectReasoningOperation(
            runtime_content_authority=authority,
            canonical_input_ingestor=ingestor,
            context_request_assembler=assembler,
            reasoning_engine=object(),  # type: ignore[arg-type]
        )


# --- public surface --------------------------------------------------------


def test_public_surface_is_only_execute() -> None:
    public_members = {name for name in vars(DirectReasoningOperation) if not name.startswith("_")}
    assert public_members == {"execute"}


def test_forbidden_operations_are_not_exposed() -> None:
    for forbidden in (
        "assemble",
        "assemble_context",
        "assemble_reasoning_request",
        "reason",
        "run",
        "invoke",
        "build",
        "ingest_task",
        "register",
        "resolve",
        "resolve_content",
        "content_authority",
        "registered_content",
    ):
        assert not hasattr(DirectReasoningOperation, forbidden)


# --- async boundary ---------------------------------------------------------


def test_execute_is_a_coroutine_function() -> None:
    assert inspect.iscoroutinefunction(DirectReasoningOperation.execute)


# --- signature (unchanged by M0-16) -----------------------------------------


def test_execute_has_exact_keyword_only_signature() -> None:
    signature = inspect.signature(DirectReasoningOperation.execute)
    assert list(signature.parameters) == [
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
        "max_total_content_size",
        "problem_ref",
        "problem_statement",
        "budget",
    ]
    for name, parameter in signature.parameters.items():
        if name == "self":
            continue
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
        assert parameter.default is inspect.Parameter.empty


def test_execute_type_hints_are_exact() -> None:
    hints = get_type_hints(DirectReasoningOperation.execute)
    assert hints["role"] is str
    assert hints["task_ref"] is str
    assert hints["goal_ref"] == (str | None)
    assert hints["mode"] is CognitiveMode
    assert hints["required_slice_types"] == tuple[ContextSliceType, ...]
    assert hints["forbidden_slice_types"] == tuple[ContextSliceType, ...]
    assert hints["max_sensitivity"] is ContextSensitivity
    assert hints["minimum_trust"] is ContextTrustLevel
    assert hints["allowed_authorities"] == tuple[InstructionAuthority, ...]
    assert hints["max_age"] == (timedelta | None)
    assert hints["max_total_content_size"] is int
    assert hints["problem_ref"] is str
    assert hints["problem_statement"] is str
    assert hints["budget"] is CognitiveBudget
    assert hints["return"] is ReasoningOutcome


def test_forbidden_parameters_are_absent() -> None:
    parameters = inspect.signature(DirectReasoningOperation.execute).parameters
    for forbidden in (
        "context_stamp",
        "context_request",
        "reasoning_request",
        "strategy",
        "reasoning_executor",
        "model_selection_request",
        "provider_ref",
        "resource_ref",
        "model_ref",
        "ollama_host",
        "state_owner",
        "situation",
        "workspace",
    ):
        assert forbidden not in parameters


# --- happy path --------------------------------------------------------------


@pytest.mark.asyncio
async def test_happy_path_calls_executor_exactly_once() -> None:
    owner = _owner()
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor)

    await operation.execute(**_execute_kwargs())  # type: ignore[arg-type]

    assert executor.call_count == 1
    assert len(executor.received_requests) == 1


@pytest.mark.asyncio
async def test_happy_path_request_shape_is_direct_with_empty_slices() -> None:
    owner = _owner()
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor)

    await operation.execute(**_execute_kwargs())  # type: ignore[arg-type]

    received = executor.received_requests[0]
    assert received.strategy is ReasoningStrategy.DIRECT
    assert received.context.slices == ()
    assert isinstance(received.context.request, ContextRequest)


@pytest.mark.asyncio
async def test_happy_path_returns_exact_outcome() -> None:
    owner = _owner()
    expected_outcome = _completed_outcome()
    executor = SpyReasoningExecutor(expected_outcome)
    operation, _ = _operation(owner=owner, executor=executor)

    result = await operation.execute(**_execute_kwargs())  # type: ignore[arg-type]

    assert result is expected_outcome


# --- canonical-version propagation (updated for M0-16 ingestion) -----------


@pytest.mark.asyncio
async def test_canonical_versions_propagate_through_the_full_path() -> None:
    # Workspace is untouched by ingestion; Situation advances by exactly one
    # version because every execute() call ingests exactly one TASK entry.
    owner = _owner(workspace_version=3, situation_version=7)
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor)

    await operation.execute(**_execute_kwargs())  # type: ignore[arg-type]

    stamp = executor.received_requests[0].context.request.context_stamp
    assert stamp.workspace_version == 3
    assert stamp.situation_version == 8
    assert stamp.identity_version is ContextVersionMarker.UNMATERIALIZED
    assert stamp.goal_version is ContextVersionMarker.UNMATERIALIZED
    assert stamp.policy_version is ContextVersionMarker.UNMATERIALIZED


# --- observation cardinality (M0-16: two observations per execute) ---------


@pytest.mark.asyncio
async def test_one_execute_call_causes_exactly_two_canonical_observations() -> None:
    # Call 1: CanonicalInputIngestor's transition-base observation.
    # Call 2: ContextRequestAssembler's post-ingestion ContextStamp observation.
    owner = _CountingStateOwner(workspace=_workspace(), situation=_situation())
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor)

    await operation.execute(**_execute_kwargs())  # type: ignore[arg-type]

    assert owner.current_snapshots_call_count == 2
    assert owner.replace_situation_call_count == 1


@pytest.mark.asyncio
async def test_ingestion_replacement_occurs_between_the_two_observations() -> None:
    owner = _CountingStateOwner(workspace=_workspace(), situation=_situation())
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor)

    await operation.execute(**_execute_kwargs())  # type: ignore[arg-type]

    assert owner.call_log == ["current_snapshots", "replace_situation", "current_snapshots"]


# --- M0-16 task ingestion -----------------------------------------------------


@pytest.mark.asyncio
async def test_ingest_task_is_called_exactly_once_with_exact_task_ref() -> None:
    owner = _owner()
    authority = RuntimeContentReferenceAuthority()
    ingestor = _SpyIngestor(state_owner=owner)
    assembler = ContextRequestAssembler(state_owner=owner)
    executor = SpyReasoningExecutor(_completed_outcome())
    engine = ReasoningEngine(executor=executor)
    operation = DirectReasoningOperation(
        runtime_content_authority=authority,
        canonical_input_ingestor=ingestor,
        context_request_assembler=assembler,
        reasoning_engine=engine,
    )

    await operation.execute(**_execute_kwargs(task_ref="task:exact-value"))  # type: ignore[arg-type]

    assert ingestor.ingest_task_calls == ["task:exact-value"]


@pytest.mark.asyncio
async def test_ingestion_occurs_before_context_request_assembly() -> None:
    owner = _owner()
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor)

    await operation.execute(**_execute_kwargs(task_ref="task:ordering"))  # type: ignore[arg-type]

    # The ContextStamp observed by the assembler must already reflect the
    # ingestion that happened before it -- proving the ordering indirectly
    # through the resulting canonical version, not just call counts.
    stamp = executor.received_requests[0].context.request.context_stamp
    assert stamp.situation_version == 1


@pytest.mark.asyncio
async def test_workspace_version_is_unaffected_by_ingestion() -> None:
    owner = _owner(workspace_version=5)
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor)

    await operation.execute(**_execute_kwargs())  # type: ignore[arg-type]

    stamp = executor.received_requests[0].context.request.context_stamp
    assert stamp.workspace_version == 5


@pytest.mark.asyncio
async def test_task_ref_forwarded_unchanged_to_ingestor_and_context_request() -> None:
    owner = _owner()
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor)

    await operation.execute(**_execute_kwargs(task_ref="task:shared"))  # type: ignore[arg-type]

    request = executor.received_requests[0].context.request
    assert request.task_ref == "task:shared"

    _, situation = owner.current_snapshots()
    task_entries = situation.entries_of_kind(SituationEntryKind.TASK)
    assert len(task_entries) == 1
    assert task_entries[0].content_ref == "task:shared"


@pytest.mark.asyncio
async def test_problem_ref_remains_independent_of_task_ref() -> None:
    owner = _owner()
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor)

    await operation.execute(**_execute_kwargs(task_ref="task:one", problem_ref="problem:two"))  # type: ignore[arg-type]

    received = executor.received_requests[0]
    assert received.problem_ref == "problem:two"

    _, situation = owner.current_snapshots()
    task_entry = situation.entries_of_kind(SituationEntryKind.TASK)[0]
    assert task_entry.content_ref == "task:one"
    assert task_entry.content_ref != received.problem_ref


# --- M0-18 runtime content registration --------------------------------------


@pytest.mark.asyncio
async def test_register_is_called_exactly_once_with_exact_task_ref_and_problem_statement() -> None:
    owner = _owner()
    authority = _SpyContentAuthority()
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor, authority=authority)

    await operation.execute(
        **_execute_kwargs(task_ref="task:content", problem_statement="Exact payload.")
    )  # type: ignore[arg-type]

    assert authority.register_calls == [("task:content", "Exact payload.")]


@pytest.mark.asyncio
async def test_registration_occurs_before_ingestion() -> None:
    # A single shared, live-appended event list -- not two independent
    # per-spy logs -- is what actually proves relative order: if production
    # called ingest_task before register, this list would read
    # ["ingest", "register"] instead, and the assertion below would fail.
    events: list[str] = []
    owner = _owner()
    authority = _SpyContentAuthority(shared_events=events)
    ingestor = _SpyIngestor(state_owner=owner, shared_events=events)
    assembler = ContextRequestAssembler(state_owner=owner)
    executor = SpyReasoningExecutor(_completed_outcome())
    engine = ReasoningEngine(executor=executor)
    operation = DirectReasoningOperation(
        runtime_content_authority=authority,
        canonical_input_ingestor=ingestor,
        context_request_assembler=assembler,
        reasoning_engine=engine,
    )

    await operation.execute(**_execute_kwargs(task_ref="task:order"))  # type: ignore[arg-type]

    assert events == ["register", "ingest"]
    assert authority.call_log == ["register"]
    assert ingestor.ingest_task_calls == ["task:order"]


@pytest.mark.asyncio
async def test_resolve_is_never_called_by_execute() -> None:
    owner = _owner()
    authority = _SpyContentAuthority()
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor, authority=authority)

    await operation.execute(**_execute_kwargs())  # type: ignore[arg-type]

    assert authority.resolve_calls == []


@pytest.mark.asyncio
async def test_registration_conflict_propagates_and_skips_ingestion_and_executor() -> None:
    owner = _owner()
    authority = RuntimeContentReferenceAuthority()
    authority.register(content_ref="task:conflict", payload="original payload")
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor, authority=authority)

    with pytest.raises(RuntimeContentReferenceConflictError):
        await operation.execute(
            **_execute_kwargs(task_ref="task:conflict", problem_statement="different payload")
        )  # type: ignore[arg-type]

    assert executor.call_count == 0
    _, situation = owner.current_snapshots()
    assert situation.entries == ()
    assert authority.resolve(content_ref="task:conflict") == "original payload"


@pytest.mark.asyncio
async def test_registration_type_error_propagates_and_skips_ingestion_and_executor() -> None:
    owner = _owner()
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor)

    with pytest.raises(TypeError):
        await operation.execute(**_execute_kwargs(problem_statement=object()))  # type: ignore[arg-type]

    assert executor.call_count == 0
    _, situation = owner.current_snapshots()
    assert situation.entries == ()


@pytest.mark.asyncio
async def test_blank_task_ref_leaves_orphan_registration_and_raises_ingestion_error() -> None:
    from noema.cognition.domain.errors import InvalidSituationEntryError

    owner = _owner()
    authority = RuntimeContentReferenceAuthority()
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor, authority=authority)

    with pytest.raises(InvalidSituationEntryError):
        await operation.execute(
            **_execute_kwargs(task_ref="", problem_statement="orphaned payload")
        )  # type: ignore[arg-type]

    assert executor.call_count == 0
    _, situation = owner.current_snapshots()
    assert situation.entries == ()
    assert authority.resolve(content_ref="") == "orphaned payload"


@pytest.mark.asyncio
async def test_blank_problem_statement_retains_registration_and_canonical_task() -> None:
    owner = _owner()
    authority = RuntimeContentReferenceAuthority()
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor, authority=authority)

    with pytest.raises(InvalidReasoningRequestError):
        await operation.execute(
            **_execute_kwargs(task_ref="task:blank-problem", problem_statement="   ")
        )  # type: ignore[arg-type]

    assert executor.call_count == 0
    assert authority.resolve(content_ref="task:blank-problem") == "   "
    _, situation = owner.current_snapshots()
    task_entries = situation.entries_of_kind(SituationEntryKind.TASK)
    assert len(task_entries) == 1
    assert task_entries[0].content_ref == "task:blank-problem"


@pytest.mark.asyncio
async def test_same_ref_same_payload_second_execute_still_attempts_ingestion() -> None:
    owner = _owner()
    authority = RuntimeContentReferenceAuthority()
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor, authority=authority)

    await operation.execute(
        **_execute_kwargs(task_ref="task:repeat", problem_statement="same payload")
    )  # type: ignore[arg-type]
    await operation.execute(
        **_execute_kwargs(task_ref="task:repeat", problem_statement="same payload")
    )  # type: ignore[arg-type]

    assert executor.call_count == 2
    _, situation = owner.current_snapshots()
    task_entries = situation.entries_of_kind(SituationEntryKind.TASK)
    assert len(task_entries) == 2
    assert all(entry.content_ref == "task:repeat" for entry in task_entries)


@pytest.mark.asyncio
async def test_same_ref_different_payload_second_execute_conflicts_before_ingestion() -> None:
    owner = _owner()
    authority = RuntimeContentReferenceAuthority()
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor, authority=authority)

    await operation.execute(
        **_execute_kwargs(task_ref="task:repeat", problem_statement="first payload")
    )  # type: ignore[arg-type]

    with pytest.raises(RuntimeContentReferenceConflictError):
        await operation.execute(
            **_execute_kwargs(task_ref="task:repeat", problem_statement="second payload")
        )  # type: ignore[arg-type]

    assert executor.call_count == 1
    _, situation = owner.current_snapshots()
    task_entries = situation.entries_of_kind(SituationEntryKind.TASK)
    assert len(task_entries) == 1
    assert authority.resolve(content_ref="task:repeat") == "first payload"


@pytest.mark.asyncio
async def test_downstream_failures_retain_registration() -> None:
    owner = _owner()
    authority = RuntimeContentReferenceAuthority()
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor, authority=authority)

    with pytest.raises(InvalidContextRequestError):
        await operation.execute(
            **_execute_kwargs(task_ref="task:context-fail", role="", problem_statement="kept")
        )  # type: ignore[arg-type]

    assert authority.resolve(content_ref="task:context-fail") == "kept"


@pytest.mark.asyncio
async def test_sequential_executions_retain_both_registrations_on_same_authority() -> None:
    owner = _owner()
    authority = RuntimeContentReferenceAuthority()
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor, authority=authority)

    await operation.execute(**_execute_kwargs(task_ref="task:1", problem_statement="first"))  # type: ignore[arg-type]
    await operation.execute(**_execute_kwargs(task_ref="task:2", problem_statement="second"))  # type: ignore[arg-type]

    assert authority.resolve(content_ref="task:1") == "first"
    assert authority.resolve(content_ref="task:2") == "second"
    _, situation = owner.current_snapshots()
    task_refs = {entry.content_ref for entry in situation.entries_of_kind(SituationEntryKind.TASK)}
    assert task_refs == {"task:1", "task:2"}


# --- caller context-field forwarding ----------------------------------------


@pytest.mark.asyncio
async def test_context_fields_are_forwarded_unchanged() -> None:
    owner = _owner()
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor)

    forbidden_slice_types = (ContextSliceType.MEMORY,)
    allowed_authorities = (InstructionAuthority.USER_EXPLICIT,)
    max_age = timedelta(minutes=5)

    await operation.execute(
        **_execute_kwargs(
            role="planner",
            task_ref="task:abc",
            goal_ref="goal:1",
            mode=CognitiveMode.FAST,
            required_slice_types=(),
            forbidden_slice_types=forbidden_slice_types,
            max_sensitivity=ContextSensitivity.SECRET,
            minimum_trust=ContextTrustLevel.TRUSTED,
            allowed_authorities=allowed_authorities,
            max_age=max_age,
            max_total_content_size=512,
        )
    )  # type: ignore[arg-type]

    request = executor.received_requests[0].context.request
    assert request.role == "planner"
    assert request.task_ref == "task:abc"
    assert request.goal_ref == "goal:1"
    assert request.mode is CognitiveMode.FAST
    assert request.required_slice_types == ()
    assert request.forbidden_slice_types is forbidden_slice_types
    assert request.max_sensitivity is ContextSensitivity.SECRET
    assert request.minimum_trust is ContextTrustLevel.TRUSTED
    assert request.allowed_authorities is allowed_authorities
    assert request.max_age is max_age
    assert request.max_total_content_size == 512


# --- problem forwarding -----------------------------------------------------


@pytest.mark.asyncio
async def test_problem_inputs_are_forwarded_unchanged() -> None:
    owner = _owner()
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor)

    await operation.execute(
        **_execute_kwargs(problem_ref="problem:xyz", problem_statement="  Solve it.  ")
    )  # type: ignore[arg-type]

    received = executor.received_requests[0]
    assert received.problem_ref == "problem:xyz"
    assert received.problem_statement == "  Solve it.  "


# --- budget identity ---------------------------------------------------------


@pytest.mark.asyncio
async def test_budget_identity_is_preserved() -> None:
    owner = _owner()
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor)
    budget = _budget()

    await operation.execute(**_execute_kwargs(budget=budget))  # type: ignore[arg-type]

    assert executor.received_requests[0].budget is budget


# --- DIRECT strategy propagation ---------------------------------------------


@pytest.mark.asyncio
async def test_strategy_is_always_direct() -> None:
    owner = _owner()
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor)

    await operation.execute(**_execute_kwargs())  # type: ignore[arg-type]

    assert executor.received_requests[0].strategy is ReasoningStrategy.DIRECT


# --- outcome identity ---------------------------------------------------------


@pytest.mark.asyncio
async def test_outcome_identity_is_preserved() -> None:
    owner = _owner()
    expected_outcome = _completed_outcome()
    executor = SpyReasoningExecutor(expected_outcome)
    operation, _ = _operation(owner=owner, executor=executor)

    result = await operation.execute(**_execute_kwargs())  # type: ignore[arg-type]

    assert result is expected_outcome


# --- invalid ContextRequest-field propagation --------------------------------


@pytest.mark.asyncio
async def test_invalid_context_request_field_propagates_and_skips_executor() -> None:
    owner = _owner()
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor)

    with pytest.raises(InvalidContextRequestError):
        await operation.execute(**_execute_kwargs(role=""))  # type: ignore[arg-type]

    assert executor.call_count == 0


@pytest.mark.asyncio
async def test_context_request_failure_does_not_cause_second_ingestion() -> None:
    owner = _owner()
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor)

    with pytest.raises(InvalidContextRequestError):
        await operation.execute(**_execute_kwargs(role=""))  # type: ignore[arg-type]

    # Ingestion already committed (it runs before ContextRequest assembly);
    # the later failure must not have triggered a compensating re-ingestion.
    _, situation = owner.current_snapshots()
    assert len(situation.entries_of_kind(SituationEntryKind.TASK)) == 1


# --- required-slice incompatibility propagation ------------------------------


@pytest.mark.asyncio
async def test_required_slice_incompatibility_propagates_and_skips_executor() -> None:
    owner = _owner()
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor)

    with pytest.raises(InvalidContextPackageError):
        await operation.execute(**_execute_kwargs(required_slice_types=(ContextSliceType.TASK,)))  # type: ignore[arg-type]

    assert executor.call_count == 0


# --- invalid problem input propagation ---------------------------------------


@pytest.mark.asyncio
async def test_invalid_problem_ref_propagates_and_skips_executor() -> None:
    owner = _owner()
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor)

    with pytest.raises(InvalidReasoningRequestError):
        await operation.execute(**_execute_kwargs(problem_ref=""))  # type: ignore[arg-type]

    assert executor.call_count == 0


@pytest.mark.asyncio
async def test_reasoning_request_failure_does_not_cause_second_ingestion() -> None:
    owner = _owner()
    authority = RuntimeContentReferenceAuthority()
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor, authority=authority)

    with pytest.raises(InvalidReasoningRequestError):
        await operation.execute(**_execute_kwargs(problem_ref=""))  # type: ignore[arg-type]

    _, situation = owner.current_snapshots()
    assert len(situation.entries_of_kind(SituationEntryKind.TASK)) == 1
    assert authority.resolve(content_ref="task:123") == "Determine an answer."


# --- exact ReasoningExecutionError propagation -------------------------------


@pytest.mark.asyncio
async def test_exact_execution_error_instance_propagates() -> None:
    owner = _owner()
    expected_error = ReasoningExecutionError("technical failure")
    executor = SpyReasoningExecutor(expected_error)
    operation, _ = _operation(owner=owner, executor=executor)

    with pytest.raises(ReasoningExecutionError) as raised:
        await operation.execute(**_execute_kwargs())  # type: ignore[arg-type]

    assert raised.value is expected_error


@pytest.mark.asyncio
async def test_reasoning_execution_error_does_not_cause_second_ingestion() -> None:
    owner = _owner()
    authority = RuntimeContentReferenceAuthority()
    executor = SpyReasoningExecutor(ReasoningExecutionError("technical failure"))
    operation, _ = _operation(owner=owner, executor=executor, authority=authority)

    with pytest.raises(ReasoningExecutionError):
        await operation.execute(**_execute_kwargs())  # type: ignore[arg-type]

    _, situation = owner.current_snapshots()
    assert len(situation.entries_of_kind(SituationEntryKind.TASK)) == 1
    assert authority.resolve(content_ref="task:123") == "Determine an answer."


# --- ingestion failure prevents later stages ---------------------------------


@pytest.mark.asyncio
async def test_ingestion_failure_propagates_and_skips_assembler_and_executor() -> None:
    from noema.cognition.domain.errors import InvalidSituationEntryError

    owner = _owner()
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor)

    with pytest.raises(InvalidSituationEntryError):
        await operation.execute(**_execute_kwargs(task_ref=""))  # type: ignore[arg-type]

    assert executor.call_count == 0
    _, situation = owner.current_snapshots()
    assert situation.entries == ()


# --- sequential reuse ---------------------------------------------------------


@pytest.mark.asyncio
async def test_sequential_operation_reuse_calls_executor_twice() -> None:
    owner = _owner()
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor)

    await operation.execute(**_execute_kwargs(problem_ref="problem:a"))  # type: ignore[arg-type]
    await operation.execute(**_execute_kwargs(problem_ref="problem:b"))  # type: ignore[arg-type]

    assert executor.call_count == 2
    assert executor.received_requests[0] is not executor.received_requests[1]
    assert executor.received_requests[0].problem_ref == "problem:a"
    assert executor.received_requests[1].problem_ref == "problem:b"


# --- canonical-state evolution (updated for M0-16 per-execute ingestion) ----


@pytest.mark.asyncio
async def test_canonical_state_evolution_is_reflected_across_operations() -> None:
    workspace = _workspace()
    situation = _situation()
    owner = CognitiveStateOwner(workspace=workspace, situation=situation)
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor)

    await operation.execute(**_execute_kwargs())  # type: ignore[arg-type]
    first_stamp = executor.received_requests[0].context.request.context_stamp
    # Situation already advances by one from this call's own ingestion.
    assert first_stamp.workspace_version == 0
    assert first_stamp.situation_version == 1

    # Simulate an unrelated external Workspace change between operations;
    # Situation continues to evolve automatically via each call's ingestion.
    current_workspace, _ = owner.current_snapshots()
    owner.replace_workspace(replace(current_workspace, version=current_workspace.version + 1))

    await operation.execute(**_execute_kwargs())  # type: ignore[arg-type]
    second_stamp = executor.received_requests[1].context.request.context_stamp
    assert second_stamp.workspace_version == 1
    assert second_stamp.situation_version == 2


# --- no direct technology dependency ------------------------------------------


def test_module_has_no_model_router_ollama_or_executor_dependency() -> None:
    import noema.cognition.application.direct_reasoning_operation as module

    assert not hasattr(module, "ModelRouter")
    assert not hasattr(module, "ollama")
    assert not hasattr(module, "ReasoningExecutor")
    assert not hasattr(module, "ModelReasoningExecutor")


def test_module_source_does_not_import_model_router_or_ollama() -> None:
    import inspect as inspect_module

    import noema.cognition.application.direct_reasoning_operation as module

    source = inspect_module.getsource(module)
    assert "model_router" not in source
    assert "ollama" not in source
    assert "ReasoningExecutor" not in source


def test_module_has_no_situation_domain_or_state_owner_dependency() -> None:
    import noema.cognition.application.direct_reasoning_operation as module

    assert not hasattr(module, "SituationEntry")
    assert not hasattr(module, "SituationEntryKind")
    assert not hasattr(module, "SituationDelta")
    assert not hasattr(module, "SituationModel")
    assert not hasattr(module, "CognitiveStateOwner")


# --- export ------------------------------------------------------------------


def test_application_package_exports_direct_reasoning_operation() -> None:
    from noema.cognition import application

    assert "DirectReasoningOperation" in application.__all__
