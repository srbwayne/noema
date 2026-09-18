import inspect
from datetime import timedelta
from decimal import Decimal
from typing import get_type_hints

import pytest

from noema.cognition.application import assemble_direct_reasoning_request
from noema.cognition.domain.budget import CognitiveBudget
from noema.cognition.domain.context import ContextStamp, ContextVersionMarker
from noema.cognition.domain.context_composition import (
    ContextPackage,
    ContextPackageZone,
    ContextRequest,
    ContextSensitivity,
    ContextSlice,
    ContextSliceType,
    ContextTrustLevel,
)
from noema.cognition.domain.errors import InvalidReasoningRequestError
from noema.cognition.domain.modes import CognitiveMode
from noema.cognition.domain.reasoning import ReasoningRequest, ReasoningStrategy


def _context_stamp() -> ContextStamp:
    return ContextStamp(
        workspace_version=0,
        situation_version=0,
        identity_version=ContextVersionMarker.UNMATERIALIZED,
        goal_version=ContextVersionMarker.UNMATERIALIZED,
        policy_version=ContextVersionMarker.UNMATERIALIZED,
    )


def _context_request(
    *,
    required_slice_types: tuple[ContextSliceType, ...] = (),
) -> ContextRequest:
    # Fixture policy values only; not runtime defaults.
    return ContextRequest(
        role="reasoner",
        task_ref="task:123",
        goal_ref=None,
        mode=CognitiveMode.DELIBERATE,
        required_slice_types=required_slice_types,
        forbidden_slice_types=(),
        max_sensitivity=ContextSensitivity.INTERNAL,
        minimum_trust=ContextTrustLevel.UNVERIFIED,
        allowed_authorities=(),
        max_age=None,
        max_total_content_size=100,
        context_stamp=_context_stamp(),
    )


def _empty_package(
    *,
    required_slice_types: tuple[ContextSliceType, ...] = (),
) -> ContextPackage:
    return ContextPackage(
        request=_context_request(required_slice_types=required_slice_types), slices=()
    )


def _package_with_one_slice() -> ContextPackage:
    context_request = _context_request(required_slice_types=(ContextSliceType.TASK,))
    task_slice = ContextSlice(
        slice_type=ContextSliceType.TASK,
        content_ref="content:task-1",
        zone=ContextPackageZone.COGNITIVE_STATE,
        sensitivity=ContextSensitivity.INTERNAL,
        trust=ContextTrustLevel.UNVERIFIED,
        instruction_authority=None,
        provenance_ref="provenance:1",
        content_size=10,
    )
    return ContextPackage(request=context_request, slices=(task_slice,))


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


def test_is_a_plain_function() -> None:
    assert inspect.isfunction(assemble_direct_reasoning_request)


def test_is_synchronous() -> None:
    assert not inspect.iscoroutinefunction(assemble_direct_reasoning_request)


def test_has_exact_keyword_only_signature() -> None:
    signature = inspect.signature(assemble_direct_reasoning_request)
    parameters = list(signature.parameters)
    assert parameters == ["context", "problem_ref", "problem_statement", "budget"]
    assert "strategy" not in signature.parameters
    assert "context_request" not in signature.parameters
    for parameter in signature.parameters.values():
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
        assert parameter.default is inspect.Parameter.empty


def test_type_hints_are_exact() -> None:
    hints = get_type_hints(assemble_direct_reasoning_request)
    assert hints["context"] is ContextPackage
    assert hints["problem_ref"] is str
    assert hints["problem_statement"] is str
    assert hints["budget"] is CognitiveBudget
    assert hints["return"] is ReasoningRequest


def test_module_does_not_reference_context_composer() -> None:
    import noema.cognition.application.direct_reasoning_request_assembler as module

    assert not hasattr(module, "ContextComposer")
    assert not hasattr(module, "ContextCompositionPolicy")
    assert not hasattr(module, "ContextCandidate")


def test_module_never_constructs_a_context_package() -> None:
    import noema.cognition.application.direct_reasoning_request_assembler as module

    source = inspect.getsource(module)
    assert "ContextPackage(" not in source


def test_happy_path_returns_reasoning_request() -> None:
    context = _empty_package()
    budget = _budget()

    result = assemble_direct_reasoning_request(
        context=context,
        problem_ref="problem:123",
        problem_statement="Determine an answer.",
        budget=budget,
    )

    assert isinstance(result, ReasoningRequest)
    assert result.problem_ref == "problem:123"
    assert result.problem_statement == "Determine an answer."
    assert result.strategy is ReasoningStrategy.DIRECT
    assert isinstance(result.context, ContextPackage)


def test_context_package_identity_is_preserved() -> None:
    context = _empty_package()

    result = assemble_direct_reasoning_request(
        context=context,
        problem_ref="problem:123",
        problem_statement="Determine an answer.",
        budget=_budget(),
    )

    assert result.context is context


def test_non_empty_context_package_identity_is_preserved() -> None:
    context = _package_with_one_slice()

    result = assemble_direct_reasoning_request(
        context=context,
        problem_ref="problem:123",
        problem_statement="Determine an answer.",
        budget=_budget(),
    )

    assert result.context is context
    assert result.context.slices == context.slices


def test_budget_identity_is_preserved() -> None:
    budget = _budget()

    result = assemble_direct_reasoning_request(
        context=_empty_package(),
        problem_ref="problem:123",
        problem_statement="Determine an answer.",
        budget=budget,
    )

    assert result.budget is budget


def test_does_not_normalize_problem_inputs() -> None:
    result = assemble_direct_reasoning_request(
        context=_empty_package(),
        problem_ref="problem:123",
        problem_statement="  Determine an answer.  ",
        budget=_budget(),
    )

    assert result.problem_statement == "  Determine an answer.  "


def test_strategy_is_always_direct_regardless_of_context() -> None:
    result = assemble_direct_reasoning_request(
        context=_package_with_one_slice(),
        problem_ref="problem:123",
        problem_statement="Determine an answer.",
        budget=_budget(),
    )

    assert result.strategy is ReasoningStrategy.DIRECT


def test_invalid_problem_ref_propagates() -> None:
    with pytest.raises(InvalidReasoningRequestError):
        assemble_direct_reasoning_request(
            context=_empty_package(),
            problem_ref="",
            problem_statement="Determine an answer.",
            budget=_budget(),
        )


def test_invalid_problem_statement_propagates() -> None:
    with pytest.raises(InvalidReasoningRequestError):
        assemble_direct_reasoning_request(
            context=_empty_package(),
            problem_ref="problem:123",
            problem_statement="",
            budget=_budget(),
        )


def test_invalid_budget_propagates() -> None:
    with pytest.raises(InvalidReasoningRequestError):
        assemble_direct_reasoning_request(
            context=_empty_package(),
            problem_ref="problem:123",
            problem_statement="Determine an answer.",
            budget=object(),  # type: ignore[arg-type]
        )


def test_invalid_context_propagates_through_reasoning_request_validation() -> None:
    with pytest.raises(InvalidReasoningRequestError):
        assemble_direct_reasoning_request(
            context=object(),  # type: ignore[arg-type]
            problem_ref="problem:123",
            problem_statement="Determine an answer.",
            budget=_budget(),
        )


def test_application_package_exports_assemble_direct_reasoning_request() -> None:
    from noema.cognition import application

    assert "assemble_direct_reasoning_request" in application.__all__
