from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

import pytest

from noema.cognition.application import (
    PriorTaskContextMaterializer,
    PriorTaskReasoningInputMaterializer,
    RuntimeContentReferenceAuthority,
)
from noema.cognition.domain.budget import CognitiveBudget
from noema.cognition.domain.context import ContextStamp
from noema.cognition.domain.context_composition import (
    ContextPackage,
    ContextPackageZone,
    ContextRequest,
    ContextSensitivity,
    ContextSlice,
    ContextSliceType,
    ContextTrustLevel,
)
from noema.cognition.domain.modes import CognitiveMode
from noema.cognition.domain.reasoning import ReasoningRequest, ReasoningStrategy


def _authority(**payloads: str) -> RuntimeContentReferenceAuthority:
    authority = RuntimeContentReferenceAuthority()
    for content_ref, payload in payloads.items():
        authority.register(content_ref=content_ref, payload=payload)
    return authority


def _context_request(*, required_slice_types: tuple[ContextSliceType, ...] = ()) -> ContextRequest:
    return ContextRequest(
        role="reasoner",
        task_ref="task:current",
        goal_ref=None,
        mode=CognitiveMode.DELIBERATE,
        required_slice_types=required_slice_types,
        forbidden_slice_types=(),
        max_sensitivity=ContextSensitivity.SECRET,
        minimum_trust=ContextTrustLevel.UNVERIFIED,
        allowed_authorities=(),
        max_age=None,
        max_total_content_size=100_000,
        context_stamp=ContextStamp(
            workspace_version=1,
            situation_version=1,
            identity_version=1,
            goal_version=1,
            policy_version=1,
        ),
    )


def _package(*slices: ContextSlice, required: tuple[ContextSliceType, ...] = ()) -> ContextPackage:
    return ContextPackage(request=_context_request(required_slice_types=required), slices=slices)


def _budget() -> CognitiveBudget:
    return CognitiveBudget(
        max_time=timedelta(seconds=1),
        max_steps=1,
        max_llm_calls=0,
        max_tool_calls=0,
        max_cost=Decimal("0"),
        max_tokens=0,
        max_search_depth=0,
    )


def _request(
    *, problem_statement: str = "current problem", context: ContextPackage | None = None
) -> ReasoningRequest:
    return ReasoningRequest(
        problem_ref="problem:123",
        problem_statement=problem_statement,
        context=context if context is not None else _package(),
        strategy=ReasoningStrategy.DIRECT,
        budget=_budget(),
    )


# --- constructor ---------------------------------------------------------


def test_constructor_rejects_invalid_context_materializer() -> None:
    with pytest.raises(TypeError, match="context_materializer"):
        PriorTaskReasoningInputMaterializer(context_materializer="not-a-materializer")  # type: ignore[arg-type]


def test_constructor_retains_exact_materializer() -> None:
    materializer = PriorTaskContextMaterializer(runtime_content_authority=_authority())
    adapter = PriorTaskReasoningInputMaterializer(context_materializer=materializer)
    assert adapter._context_materializer is materializer  # noqa: SLF001


# --- materialize() argument validation ------------------------------------


def test_materialize_rejects_non_reasoning_request() -> None:
    adapter = PriorTaskReasoningInputMaterializer(
        context_materializer=PriorTaskContextMaterializer(runtime_content_authority=_authority())
    )
    with pytest.raises(TypeError, match="request"):
        adapter.materialize("not-a-request")  # type: ignore[arg-type]


# --- exact delegation -------------------------------------------------------


def test_exact_problem_statement_forwarded() -> None:
    materializer = PriorTaskContextMaterializer(runtime_content_authority=_authority())
    adapter = PriorTaskReasoningInputMaterializer(context_materializer=materializer)
    request = _request(problem_statement="Exact problem text.")

    result = adapter.materialize(request)

    assert result == "Exact problem text."


def test_exact_context_package_forwarded() -> None:
    authority = _authority(**{"task:prior": "prior payload"})
    materializer = PriorTaskContextMaterializer(runtime_content_authority=authority)
    adapter = PriorTaskReasoningInputMaterializer(context_materializer=materializer)
    context_slice = ContextSlice(
        slice_type=ContextSliceType.TASK,
        content_ref="task:prior",
        zone=ContextPackageZone.COGNITIVE_STATE,
        sensitivity=ContextSensitivity.SECRET,
        trust=ContextTrustLevel.UNVERIFIED,
        instruction_authority=None,
        provenance_ref="entry:1",
        content_size=len("prior payload"),
    )
    request = _request(
        problem_statement="current",
        context=_package(context_slice, required=(ContextSliceType.TASK,)),
    )

    result = adapter.materialize(request)

    assert "prior payload" in result
    assert "current" in result


def test_returned_string_propagated_exactly() -> None:
    materializer = PriorTaskContextMaterializer(runtime_content_authority=_authority())
    adapter = PriorTaskReasoningInputMaterializer(context_materializer=materializer)
    request = _request(problem_statement="exact and unchanged")

    result = adapter.materialize(request)

    assert result == "exact and unchanged"
    assert result is request.problem_statement


def test_underlying_materializer_failure_propagates_unchanged() -> None:
    from noema.cognition.application import RuntimeContentReferenceNotFoundError

    authority = _authority()
    materializer = PriorTaskContextMaterializer(runtime_content_authority=authority)
    adapter = PriorTaskReasoningInputMaterializer(context_materializer=materializer)
    context_slice = ContextSlice(
        slice_type=ContextSliceType.TASK,
        content_ref="task:unregistered",
        zone=ContextPackageZone.COGNITIVE_STATE,
        sensitivity=ContextSensitivity.SECRET,
        trust=ContextTrustLevel.UNVERIFIED,
        instruction_authority=None,
        provenance_ref="entry:1",
        content_size=1,
    )
    request = _request(context=_package(context_slice, required=(ContextSliceType.TASK,)))

    with pytest.raises(RuntimeContentReferenceNotFoundError):
        adapter.materialize(request)


def test_no_mutation_of_request_or_context() -> None:
    materializer = PriorTaskContextMaterializer(runtime_content_authority=_authority())
    adapter = PriorTaskReasoningInputMaterializer(context_materializer=materializer)
    request = _request()
    before = replace(request)

    adapter.materialize(request)

    assert request == before


def test_no_provider_or_model_dependency() -> None:
    import inspect

    import noema.cognition.application.prior_task_reasoning_input_materializer as module

    source = inspect.getsource(module)
    assert "model_router" not in source
    assert "ollama" not in source


# --- export ------------------------------------------------------------------


def test_application_package_exports_adapter() -> None:
    from noema.cognition import application

    assert "PriorTaskReasoningInputMaterializer" in application.__all__
