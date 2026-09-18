import inspect
from datetime import timedelta
from decimal import Decimal
from typing import Protocol, get_type_hints

from noema.cognition.domain.budget import CognitiveBudget
from noema.cognition.domain.context import ContextStamp
from noema.cognition.domain.context_composition import (
    ContextPackage,
    ContextRequest,
    ContextSensitivity,
    ContextTrustLevel,
)
from noema.cognition.domain.modes import CognitiveMode
from noema.cognition.domain.reasoning import ReasoningRequest, ReasoningStrategy
from noema.cognition.ports import ReasoningInputMaterializer


class StubReasoningInputMaterializer:
    """Local test double documenting the Protocol's structural intent.

    Deliberately does NOT inherit from ReasoningInputMaterializer: the port
    is a structural typing contract, not a base class adapters must extend.
    """

    def materialize(self, request: ReasoningRequest) -> str:
        return request.problem_statement


def reasoning_request() -> ReasoningRequest:
    context_request = ContextRequest(
        role="reasoner",
        task_ref="task:123",
        goal_ref=None,
        mode=CognitiveMode.DELIBERATE,
        required_slice_types=(),
        forbidden_slice_types=(),
        max_sensitivity=ContextSensitivity.INTERNAL,
        minimum_trust=ContextTrustLevel.UNVERIFIED,
        allowed_authorities=(),
        max_age=None,
        max_total_content_size=100,
        context_stamp=ContextStamp(
            workspace_version=1,
            situation_version=1,
            identity_version=1,
            goal_version=1,
            policy_version=1,
        ),
    )
    return ReasoningRequest(
        problem_ref="problem:123",
        problem_statement="Determine an answer.",
        context=ContextPackage(request=context_request, slices=()),
        strategy=ReasoningStrategy.DIRECT,
        budget=CognitiveBudget(
            max_time=timedelta(seconds=1),
            max_steps=1,
            max_llm_calls=0,
            max_tool_calls=0,
            max_cost=Decimal("0"),
            max_tokens=0,
            max_search_depth=0,
        ),
    )


def test_reasoning_input_materializer_is_a_protocol() -> None:
    assert issubclass(ReasoningInputMaterializer, Protocol)


def test_reasoning_input_materializer_is_not_an_abc() -> None:
    abstract_methods = getattr(ReasoningInputMaterializer, "__abstractmethods__", frozenset())
    assert not abstract_methods


def test_reasoning_input_materializer_declares_materialize() -> None:
    assert hasattr(ReasoningInputMaterializer, "materialize")


def test_reasoning_input_materializer_materialize_is_synchronous() -> None:
    assert not inspect.iscoroutinefunction(ReasoningInputMaterializer.materialize)


def test_reasoning_input_materializer_materialize_has_exact_public_signature() -> None:
    signature = inspect.signature(ReasoningInputMaterializer.materialize)
    assert list(signature.parameters) == ["self", "request"]


def test_reasoning_input_materializer_materialize_type_hints_are_exact() -> None:
    hints = get_type_hints(ReasoningInputMaterializer.materialize)
    assert hints["request"] is ReasoningRequest
    assert hints["return"] is str


def test_reasoning_input_materializer_public_surface_is_only_materialize() -> None:
    public_members = {
        name for name, value in vars(ReasoningInputMaterializer).items() if not name.startswith("_")
    }
    assert public_members == {"materialize"}


def test_reasoning_input_materializer_module_has_no_context_composition_dependency() -> None:
    import ast

    import noema.cognition.ports.reasoning_input_materializer as module

    assert not hasattr(module, "ContextPackage")
    assert not hasattr(module, "ContextSlice")

    tree = ast.parse(inspect.getsource(module))
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)

    assert all("context_composition" not in module_name for module_name in imported_modules)
    assert all("cognition.application" not in module_name for module_name in imported_modules)
    assert all("cognition.infrastructure" not in module_name for module_name in imported_modules)
    assert all("model_router" not in module_name for module_name in imported_modules)


def test_stub_materializer_satisfies_the_protocol_structurally() -> None:
    result = StubReasoningInputMaterializer().materialize(reasoning_request())
    assert isinstance(result, str)


def test_application_ports_package_exports_reasoning_input_materializer() -> None:
    from noema.cognition import ports

    assert "ReasoningInputMaterializer" in ports.__all__
