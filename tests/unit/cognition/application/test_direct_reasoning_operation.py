import inspect
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal
from typing import get_type_hints

import pytest

from noema.cognition.application import (
    ContextRequestAssembler,
    DirectReasoningOperation,
    ReasoningEngine,
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
from noema.cognition.domain.situation import SituationModel
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
    """A CognitiveStateOwner that records how often current_snapshots is called."""

    __slots__ = ("current_snapshots_call_count",)

    def __init__(self, *, workspace: CognitiveWorkspace, situation: SituationModel) -> None:
        super().__init__(workspace=workspace, situation=situation)
        self.current_snapshots_call_count = 0

    def current_snapshots(self) -> tuple[CognitiveWorkspace, SituationModel]:
        self.current_snapshots_call_count += 1
        return super().current_snapshots()


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
        "max_tokens": 100,
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
    *, owner: CognitiveStateOwner, executor: object
) -> tuple[DirectReasoningOperation, "SpyReasoningExecutor"]:
    assembler = ContextRequestAssembler(state_owner=owner)
    engine = ReasoningEngine(executor=executor)  # type: ignore[arg-type]
    return (
        DirectReasoningOperation(context_request_assembler=assembler, reasoning_engine=engine),
        executor,  # type: ignore[return-value]
    )


# --- class shape (§51) ---------------------------------------------------


def test_direct_reasoning_operation_has_exact_slots() -> None:
    assert DirectReasoningOperation.__slots__ == (
        "_context_request_assembler",
        "_reasoning_engine",
    )


def test_direct_reasoning_operation_instances_have_no_dict() -> None:
    owner = _owner()
    operation, _ = _operation(owner=owner, executor=SpyReasoningExecutor(_completed_outcome()))
    assert not hasattr(operation, "__dict__")


def test_constructor_is_keyword_only() -> None:
    assembler = ContextRequestAssembler(state_owner=_owner())
    engine = ReasoningEngine(executor=SpyReasoningExecutor(_completed_outcome()))
    with pytest.raises(TypeError):
        DirectReasoningOperation(assembler, engine)  # type: ignore[misc]
    DirectReasoningOperation(context_request_assembler=assembler, reasoning_engine=engine)


def test_constructor_type_hints_are_exact() -> None:
    hints = get_type_hints(DirectReasoningOperation.__init__)
    assert hints == {
        "context_request_assembler": ContextRequestAssembler,
        "reasoning_engine": ReasoningEngine,
        "return": type(None),
    }


def test_constructor_rejects_invalid_context_request_assembler() -> None:
    engine = ReasoningEngine(executor=SpyReasoningExecutor(_completed_outcome()))
    with pytest.raises(TypeError, match="context_request_assembler"):
        DirectReasoningOperation(
            context_request_assembler=object(),  # type: ignore[arg-type]
            reasoning_engine=engine,
        )


def test_constructor_rejects_invalid_reasoning_engine() -> None:
    assembler = ContextRequestAssembler(state_owner=_owner())
    with pytest.raises(TypeError, match="reasoning_engine"):
        DirectReasoningOperation(
            context_request_assembler=assembler,
            reasoning_engine=object(),  # type: ignore[arg-type]
        )


# --- public surface (§52) -------------------------------------------------


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
    ):
        assert not hasattr(DirectReasoningOperation, forbidden)


# --- async boundary (§53) -------------------------------------------------


def test_execute_is_a_coroutine_function() -> None:
    assert inspect.iscoroutinefunction(DirectReasoningOperation.execute)


# --- signature (§54, §55) --------------------------------------------------


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
        "max_tokens",
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
    assert hints["max_tokens"] is int
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
    ):
        assert forbidden not in parameters


# --- happy path (§56) -------------------------------------------------------


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


# --- canonical-version propagation (§57) ------------------------------------


@pytest.mark.asyncio
async def test_canonical_versions_propagate_through_the_full_path() -> None:
    owner = _owner(workspace_version=3, situation_version=7)
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor)

    await operation.execute(**_execute_kwargs())  # type: ignore[arg-type]

    stamp = executor.received_requests[0].context.request.context_stamp
    assert stamp.workspace_version == 3
    assert stamp.situation_version == 7
    assert stamp.identity_version is ContextVersionMarker.UNMATERIALIZED
    assert stamp.goal_version is ContextVersionMarker.UNMATERIALIZED
    assert stamp.policy_version is ContextVersionMarker.UNMATERIALIZED


# --- one-observation proof (§58) --------------------------------------------


@pytest.mark.asyncio
async def test_one_execute_call_causes_exactly_one_canonical_observation() -> None:
    owner = _CountingStateOwner(workspace=_workspace(), situation=_situation())
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor)

    await operation.execute(**_execute_kwargs())  # type: ignore[arg-type]

    assert owner.current_snapshots_call_count == 1


# --- caller context-field forwarding (§59) ----------------------------------


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
            max_tokens=512,
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
    assert request.max_tokens == 512


# --- problem forwarding (§60) -----------------------------------------------


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


# --- budget identity (§61) --------------------------------------------------


@pytest.mark.asyncio
async def test_budget_identity_is_preserved() -> None:
    owner = _owner()
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor)
    budget = _budget()

    await operation.execute(**_execute_kwargs(budget=budget))  # type: ignore[arg-type]

    assert executor.received_requests[0].budget is budget


# --- DIRECT strategy propagation (§62) --------------------------------------


@pytest.mark.asyncio
async def test_strategy_is_always_direct() -> None:
    owner = _owner()
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor)

    await operation.execute(**_execute_kwargs())  # type: ignore[arg-type]

    assert executor.received_requests[0].strategy is ReasoningStrategy.DIRECT


# --- outcome identity (§63) -------------------------------------------------


@pytest.mark.asyncio
async def test_outcome_identity_is_preserved() -> None:
    owner = _owner()
    expected_outcome = _completed_outcome()
    executor = SpyReasoningExecutor(expected_outcome)
    operation, _ = _operation(owner=owner, executor=executor)

    result = await operation.execute(**_execute_kwargs())  # type: ignore[arg-type]

    assert result is expected_outcome


# --- invalid ContextRequest-field propagation (§64) -------------------------


@pytest.mark.asyncio
async def test_invalid_context_request_field_propagates_and_skips_executor() -> None:
    owner = _owner()
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor)

    with pytest.raises(InvalidContextRequestError):
        await operation.execute(**_execute_kwargs(role=""))  # type: ignore[arg-type]

    assert executor.call_count == 0


# --- required-slice incompatibility propagation (§65) -----------------------


@pytest.mark.asyncio
async def test_required_slice_incompatibility_propagates_and_skips_executor() -> None:
    owner = _owner()
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor)

    with pytest.raises(InvalidContextPackageError):
        await operation.execute(**_execute_kwargs(required_slice_types=(ContextSliceType.TASK,)))  # type: ignore[arg-type]

    assert executor.call_count == 0


# --- invalid problem input propagation (§66) --------------------------------


@pytest.mark.asyncio
async def test_invalid_problem_ref_propagates_and_skips_executor() -> None:
    owner = _owner()
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor)

    with pytest.raises(InvalidReasoningRequestError):
        await operation.execute(**_execute_kwargs(problem_ref=""))  # type: ignore[arg-type]

    assert executor.call_count == 0


# --- exact ReasoningExecutionError propagation (§67) ------------------------


@pytest.mark.asyncio
async def test_exact_execution_error_instance_propagates() -> None:
    owner = _owner()
    expected_error = ReasoningExecutionError("technical failure")
    executor = SpyReasoningExecutor(expected_error)
    operation, _ = _operation(owner=owner, executor=executor)

    with pytest.raises(ReasoningExecutionError) as raised:
        await operation.execute(**_execute_kwargs())  # type: ignore[arg-type]

    assert raised.value is expected_error


# --- sequential reuse (§69) -------------------------------------------------


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


# --- canonical-state evolution (§70) -----------------------------------------


@pytest.mark.asyncio
async def test_canonical_state_evolution_is_reflected_across_operations() -> None:
    workspace = _workspace()
    situation = _situation()
    owner = CognitiveStateOwner(workspace=workspace, situation=situation)
    executor = SpyReasoningExecutor(_completed_outcome())
    operation, _ = _operation(owner=owner, executor=executor)

    await operation.execute(**_execute_kwargs())  # type: ignore[arg-type]
    first_stamp = executor.received_requests[0].context.request.context_stamp
    assert first_stamp.workspace_version == workspace.version
    assert first_stamp.situation_version == situation.version

    owner.replace_workspace(replace(workspace, version=workspace.version + 1))
    owner.replace_situation(replace(situation, version=situation.version + 1))

    await operation.execute(**_execute_kwargs())  # type: ignore[arg-type]
    second_stamp = executor.received_requests[1].context.request.context_stamp
    assert second_stamp.workspace_version == workspace.version + 1
    assert second_stamp.situation_version == situation.version + 1


# --- no direct technology dependency (§71) ----------------------------------


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


# --- export (§ application package) -----------------------------------------


def test_application_package_exports_direct_reasoning_operation() -> None:
    from noema.cognition import application

    assert "DirectReasoningOperation" in application.__all__
