import inspect
from datetime import timedelta
from decimal import Decimal

import pytest

from noema.cognition.application import (
    CanonicalInputIngestor,
    ContextPackagePreparer,
    ContextRequestAssembler,
    DirectReasoningOperation,
    PriorTaskContextProjector,
    ReasoningEngine,
    ReasoningStrategyAdmittingDirectOperation,
    RuntimeContentReferenceAuthority,
    UnsupportedReasoningStrategyError,
)
from noema.cognition.application.cognitive_state_owner import CognitiveStateOwner
from noema.cognition.domain.budget import CognitiveBudget
from noema.cognition.domain.context_composition import ContextSensitivity, ContextTrustLevel
from noema.cognition.domain.errors import AmbiguousReasoningStrategyError
from noema.cognition.domain.modes import CognitiveMode
from noema.cognition.domain.reasoning import (
    ReasoningOutcome,
    ReasoningStatus,
    ReasoningStrategy,
    ReasoningStrategyDemand,
    ReasoningStrategySelector,
)
from noema.cognition.domain.situation import SituationModel
from noema.cognition.domain.workspace import CognitiveWorkspace, WorkspaceBudget
from noema.cognition.ports import ReasoningExecutionError


def _all_false_demand(**overrides: bool) -> ReasoningStrategyDemand:
    fields = {
        "requires_decomposition": False,
        "requires_hypothesis_testing": False,
        "requires_causal_reasoning": False,
        "requires_comparison": False,
        "requires_search": False,
        "requires_counterfactual": False,
        "requires_critique": False,
        "requires_tool_assistance": False,
        "requires_multi_model": False,
    }
    fields.update(overrides)
    return ReasoningStrategyDemand(**fields)  # type: ignore[arg-type]


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


def _workspace_budget() -> WorkspaceBudget:
    return WorkspaceBudget(max_active_items=4, max_working_items=4, max_peripheral_items=4)


class _DummyReasoningExecutor:
    """Never invoked in these tests; only needed to construct a real ReasoningEngine."""

    async def execute(self, request: object) -> ReasoningOutcome:  # pragma: no cover
        raise AssertionError("must never be called")


def _real_direct_operation() -> DirectReasoningOperation:
    """A cheaply-constructed, fully real DirectReasoningOperation for isinstance binding.

    Its collaborators are never exercised by the tests that use
    ``_SpyDirectOperation`` below -- only real enough to satisfy
    ``DirectReasoningOperation.__init__``'s own type checks.
    """
    owner = CognitiveStateOwner(
        workspace=CognitiveWorkspace(budget=_workspace_budget()),
        situation=SituationModel(),
    )
    authority = RuntimeContentReferenceAuthority()
    return DirectReasoningOperation(
        runtime_content_authority=authority,
        canonical_input_ingestor=CanonicalInputIngestor(state_owner=owner),
        context_package_preparer=ContextPackagePreparer(
            state_owner=owner,
            context_request_assembler=ContextRequestAssembler(),
            prior_task_context_projector=PriorTaskContextProjector(
                runtime_content_authority=authority
            ),
            context_composer=None,
            prior_task_context_enabled=False,
        ),
        reasoning_engine=ReasoningEngine(executor=_DummyReasoningExecutor()),  # type: ignore[arg-type]
    )


class _SpyDirectOperation(DirectReasoningOperation):
    """A DirectReasoningOperation subclass that records calls instead of executing."""

    __slots__ = ("call_count", "received_kwargs", "_result")

    def __init__(self, result: object) -> None:
        real = _real_direct_operation()
        super().__init__(
            runtime_content_authority=real._runtime_content_authority,  # noqa: SLF001
            canonical_input_ingestor=real._canonical_input_ingestor,  # noqa: SLF001
            context_package_preparer=real._context_package_preparer,  # noqa: SLF001
            reasoning_engine=real._reasoning_engine,  # noqa: SLF001
        )
        self.call_count = 0
        self.received_kwargs: list[dict[str, object]] = []
        self._result = result

    async def execute(self, **kwargs: object) -> ReasoningOutcome:
        self.call_count += 1
        self.received_kwargs.append(kwargs)
        if isinstance(self._result, BaseException):
            raise self._result
        return self._result  # type: ignore[return-value]


def _wrapper(
    *, direct_operation: DirectReasoningOperation
) -> ReasoningStrategyAdmittingDirectOperation:
    return ReasoningStrategyAdmittingDirectOperation(
        selector=ReasoningStrategySelector(),
        direct_operation=direct_operation,
    )


# --- constructor / structural shape -------------------------------------------


def test_wrapper_has_exact_slots() -> None:
    assert ReasoningStrategyAdmittingDirectOperation.__slots__ == (
        "_selector",
        "_direct_operation",
    )


def test_wrapper_instances_have_no_dict() -> None:
    wrapper = _wrapper(direct_operation=_real_direct_operation())
    assert not hasattr(wrapper, "__dict__")


def test_wrapper_constructor_is_keyword_only() -> None:
    selector = ReasoningStrategySelector()
    direct_operation = _real_direct_operation()
    with pytest.raises(TypeError):
        ReasoningStrategyAdmittingDirectOperation(selector, direct_operation)  # type: ignore[misc]
    ReasoningStrategyAdmittingDirectOperation(selector=selector, direct_operation=direct_operation)


def test_wrapper_rejects_non_selector() -> None:
    with pytest.raises(TypeError, match="selector must be a ReasoningStrategySelector"):
        ReasoningStrategyAdmittingDirectOperation(
            selector="not a selector",  # type: ignore[arg-type]
            direct_operation=_real_direct_operation(),
        )


def test_wrapper_rejects_non_direct_operation() -> None:
    with pytest.raises(TypeError, match="direct_operation must be a DirectReasoningOperation"):
        ReasoningStrategyAdmittingDirectOperation(
            selector=ReasoningStrategySelector(),
            direct_operation="not an operation",  # type: ignore[arg-type]
        )


def test_wrapper_retains_exact_dependency_identity() -> None:
    selector = ReasoningStrategySelector()
    direct_operation = _real_direct_operation()
    wrapper = ReasoningStrategyAdmittingDirectOperation(
        selector=selector, direct_operation=direct_operation
    )
    assert wrapper._selector is selector  # noqa: SLF001
    assert wrapper._direct_operation is direct_operation  # noqa: SLF001


def test_wrapper_execute_is_a_coroutine_function() -> None:
    assert inspect.iscoroutinefunction(ReasoningStrategyAdmittingDirectOperation.execute)


def test_wrapper_public_surface_is_only_execute() -> None:
    public_members = {
        name for name in vars(ReasoningStrategyAdmittingDirectOperation) if not name.startswith("_")
    }
    assert public_members == {"execute"}


# --- demand validation -----------------------------------------------------------


@pytest.mark.parametrize("invalid_demand", [None, {}, (), "demand", 1])
@pytest.mark.asyncio
async def test_non_demand_raises_type_error(invalid_demand: object) -> None:
    inner = _SpyDirectOperation(_completed_outcome())
    wrapper = _wrapper(direct_operation=inner)

    with pytest.raises(TypeError, match="demand must be a ReasoningStrategyDemand"):
        await wrapper.execute(demand=invalid_demand, **_execute_kwargs())  # type: ignore[arg-type]

    assert inner.call_count == 0


# --- DIRECT admission --------------------------------------------------------------


@pytest.mark.asyncio
async def test_all_false_demand_admits_direct_and_calls_underlying_operation_once() -> None:
    outcome = _completed_outcome()
    inner = _SpyDirectOperation(outcome)
    wrapper = _wrapper(direct_operation=inner)

    await wrapper.execute(demand=_all_false_demand(), **_execute_kwargs())

    assert inner.call_count == 1


@pytest.mark.asyncio
async def test_all_execute_arguments_are_forwarded_unchanged() -> None:
    inner = _SpyDirectOperation(_completed_outcome())
    wrapper = _wrapper(direct_operation=inner)
    kwargs = _execute_kwargs()

    await wrapper.execute(demand=_all_false_demand(), **kwargs)

    assert len(inner.received_kwargs) == 1
    assert inner.received_kwargs[0] == kwargs


@pytest.mark.asyncio
async def test_exact_returned_outcome_identity_is_preserved() -> None:
    outcome = _completed_outcome()
    inner = _SpyDirectOperation(outcome)
    wrapper = _wrapper(direct_operation=inner)

    result = await wrapper.execute(demand=_all_false_demand(), **_execute_kwargs())

    assert result is outcome


@pytest.mark.asyncio
async def test_underlying_operation_exception_propagates_unchanged_for_admitted_direct() -> None:
    expected_error = ReasoningExecutionError("technical failure")
    inner = _SpyDirectOperation(expected_error)
    wrapper = _wrapper(direct_operation=inner)

    with pytest.raises(ReasoningExecutionError) as raised:
        await wrapper.execute(demand=_all_false_demand(), **_execute_kwargs())

    assert raised.value is expected_error


# --- specialized denial ------------------------------------------------------------


@pytest.mark.asyncio
async def test_single_specialized_demand_raises_unsupported_strategy_error() -> None:
    inner = _SpyDirectOperation(_completed_outcome())
    wrapper = _wrapper(direct_operation=inner)

    with pytest.raises(UnsupportedReasoningStrategyError):
        await wrapper.execute(demand=_all_false_demand(requires_search=True), **_execute_kwargs())


@pytest.mark.asyncio
async def test_specialized_denial_never_calls_underlying_operation() -> None:
    inner = _SpyDirectOperation(_completed_outcome())
    wrapper = _wrapper(direct_operation=inner)

    with pytest.raises(UnsupportedReasoningStrategyError):
        await wrapper.execute(demand=_all_false_demand(requires_search=True), **_execute_kwargs())

    assert inner.call_count == 0
    assert inner.received_kwargs == []


@pytest.mark.asyncio
async def test_unsupported_error_identifies_selected_strategy_safely() -> None:
    inner = _SpyDirectOperation(_completed_outcome())
    wrapper = _wrapper(direct_operation=inner)

    with pytest.raises(UnsupportedReasoningStrategyError) as raised:
        await wrapper.execute(demand=_all_false_demand(requires_search=True), **_execute_kwargs())

    assert ReasoningStrategy.SEARCH.name in str(raised.value)


@pytest.mark.asyncio
async def test_unsupported_error_identifies_structured_reason_safely() -> None:
    inner = _SpyDirectOperation(_completed_outcome())
    wrapper = _wrapper(direct_operation=inner)

    with pytest.raises(UnsupportedReasoningStrategyError) as raised:
        await wrapper.execute(demand=_all_false_demand(requires_search=True), **_execute_kwargs())

    assert "SEARCH_REQUIRED" in str(raised.value)


@pytest.mark.asyncio
async def test_unsupported_error_excludes_problem_text_and_refs() -> None:
    inner = _SpyDirectOperation(_completed_outcome())
    wrapper = _wrapper(direct_operation=inner)
    kwargs = _execute_kwargs(
        problem_statement="a very specific distinctive problem statement",
        problem_ref="problem:distinctive",
        task_ref="task:distinctive",
    )

    with pytest.raises(UnsupportedReasoningStrategyError) as raised:
        await wrapper.execute(demand=_all_false_demand(requires_search=True), **kwargs)

    message = str(raised.value)
    assert "a very specific distinctive problem statement" not in message
    assert "problem:distinctive" not in message
    assert "task:distinctive" not in message


# --- ambiguous denial ---------------------------------------------------------------


@pytest.mark.asyncio
async def test_multiple_specialized_requirements_propagate_exact_ambiguous_error() -> None:
    inner = _SpyDirectOperation(_completed_outcome())
    wrapper = _wrapper(direct_operation=inner)
    demand = _all_false_demand(requires_search=True, requires_critique=True)

    with pytest.raises(AmbiguousReasoningStrategyError):
        await wrapper.execute(demand=demand, **_execute_kwargs())


@pytest.mark.asyncio
async def test_ambiguous_demand_never_calls_underlying_operation() -> None:
    inner = _SpyDirectOperation(_completed_outcome())
    wrapper = _wrapper(direct_operation=inner)
    demand = _all_false_demand(requires_search=True, requires_critique=True)

    with pytest.raises(AmbiguousReasoningStrategyError):
        await wrapper.execute(demand=demand, **_execute_kwargs())

    assert inner.call_count == 0


# --- export ------------------------------------------------------------------


def test_application_package_exports_wrapper_and_error() -> None:
    from noema.cognition import application

    assert "ReasoningStrategyAdmittingDirectOperation" in application.__all__
    assert "UnsupportedReasoningStrategyError" in application.__all__


def test_unsupported_error_is_not_a_domain_error_or_execution_error() -> None:
    from noema.shared.domain import DomainError

    assert not issubclass(UnsupportedReasoningStrategyError, DomainError)
    assert not issubclass(UnsupportedReasoningStrategyError, ReasoningExecutionError)
    assert UnsupportedReasoningStrategyError.__mro__[1] is Exception
