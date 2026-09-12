import inspect
from datetime import timedelta
from decimal import Decimal
from typing import get_type_hints

import pytest

import noema.bootstrap as bootstrap
from noema.bootstrap import open_direct_runtime
from noema.cognition.application import (
    CognitiveStateOwner,
    DirectReasoningOperation,
    ReasoningEngine,
)
from noema.cognition.domain.budget import CognitiveBudget
from noema.cognition.domain.context import ContextVersionMarker
from noema.cognition.domain.context_composition import (
    ContextSensitivity,
    ContextTrustLevel,
)
from noema.cognition.domain.modes import CognitiveMode
from noema.cognition.domain.reasoning import (
    ReasoningOutcome,
    ReasoningRequest,
    ReasoningStrategy,
)
from noema.cognition.domain.situation import SituationModel
from noema.cognition.domain.workspace import CognitiveWorkspace, WorkspaceBudget
from noema.cognition.infrastructure import ModelReasoningExecutor
from noema.cognition.ports import ReasoningExecutionError
from noema.model_router.domain import (
    ModelCapability,
    ModelResource,
    ModelResourceCapabilities,
    ModelSelector,
)

# --- fixtures ----------------------------------------------------------------


def _workspace_budget() -> WorkspaceBudget:
    # Fixture data only. These numbers are not a runtime WorkspaceBudget policy.
    return WorkspaceBudget(max_active_items=4, max_working_items=4, max_peripheral_items=4)


def _model_resource(
    *, resource_ref: str = "resource:test", model_ref: str = "model:test"
) -> ModelResource:
    return ModelResource(resource_ref=resource_ref, provider_ref="ollama", model_ref=model_ref)


def _model_resource_capabilities(
    *,
    capabilities: frozenset[ModelCapability] = frozenset({ModelCapability.TEXT_GENERATION}),
    resource_ref: str = "resource:test",
    model_ref: str = "model:test",
) -> ModelResourceCapabilities:
    return ModelResourceCapabilities(
        resource=_model_resource(resource_ref=resource_ref, model_ref=model_ref),
        capabilities=capabilities,
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
        "budget": CognitiveBudget(
            max_time=timedelta(seconds=1),
            max_steps=1,
            max_llm_calls=0,
            max_tool_calls=0,
            max_cost=Decimal("0"),
            max_tokens=0,
            max_search_depth=0,
        ),
    }
    kwargs.update(overrides)
    return kwargs


class _FakeGenerateResponse:
    def __init__(self, text: str) -> None:
        self.response = text


def _make_fake_async_client_class(
    generate_result: object = "the answer",
) -> type:
    """Build a fresh fake ``ollama.AsyncClient`` stand-in class.

    A new class is returned per call so each test gets its own isolated
    ``created`` instance registry, with no real SDK/network involvement.
    """

    class FakeAsyncClient:
        created: list["FakeAsyncClient"] = []

        def __init__(self, *, host: object = None, **kwargs: object) -> None:
            self.host = host
            self.aenter_count = 0
            self.aexit_count = 0
            self.generate_calls: list[dict[str, object]] = []
            type(self).created.append(self)

        async def __aenter__(self) -> "FakeAsyncClient":
            self.aenter_count += 1
            return self

        async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
            self.aexit_count += 1

        async def generate(self, *, model: str, prompt: str, stream: bool) -> _FakeGenerateResponse:
            self.generate_calls.append({"model": model, "prompt": prompt, "stream": stream})
            if isinstance(generate_result, BaseException):
                raise generate_result
            return _FakeGenerateResponse(str(generate_result))

    return FakeAsyncClient


# --- module surface (§48) -----------------------------------------------------


def test_module_exports_only_open_direct_runtime() -> None:
    assert bootstrap.__all__ == ["open_direct_runtime"]


def test_no_runtime_container_type_is_defined() -> None:
    for forbidden in ("NoemaRuntime", "DirectRuntime", "RuntimeContainer", "BootstrapResult"):
        assert not hasattr(bootstrap, forbidden)


def test_no_process_global_runtime_objects_at_import_time() -> None:
    runtime_object_types = (
        CognitiveStateOwner,
        DirectReasoningOperation,
        ReasoningEngine,
        CognitiveWorkspace,
        SituationModel,
    )
    for name, value in vars(bootstrap).items():
        if name.startswith("__"):
            continue
        assert not isinstance(value, runtime_object_types)


# --- signature (§48) ----------------------------------------------------------


def test_open_direct_runtime_has_exact_keyword_only_signature() -> None:
    underlying = open_direct_runtime.__wrapped__  # type: ignore[attr-defined]
    signature = inspect.signature(underlying)
    parameters = list(signature.parameters)
    assert parameters == ["workspace_budget", "ollama_host", "model_resource"]
    for parameter in signature.parameters.values():
        assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
        assert parameter.default is inspect.Parameter.empty


def test_open_direct_runtime_type_hints_are_exact() -> None:
    underlying = open_direct_runtime.__wrapped__  # type: ignore[attr-defined]
    hints = get_type_hints(underlying)
    assert hints["workspace_budget"] is WorkspaceBudget
    assert hints["ollama_host"] is str
    assert hints["model_resource"] is ModelResourceCapabilities


def test_open_direct_runtime_rejects_unexpected_keyword() -> None:
    with pytest.raises(TypeError):
        open_direct_runtime(
            workspace_budget=_workspace_budget(),
            ollama_host="host:1",
            model_resource=_model_resource_capabilities(),
            extra=True,  # type: ignore[call-arg]
        )


# --- host validation (§49, §50) -----------------------------------------------


@pytest.mark.asyncio
async def test_invalid_host_type_raises_type_error_before_client_construction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client_class = _make_fake_async_client_class()
    monkeypatch.setattr(bootstrap, "AsyncClient", fake_client_class)

    with pytest.raises(TypeError, match="ollama_host"):
        async with open_direct_runtime(
            workspace_budget=_workspace_budget(),
            ollama_host=object(),  # type: ignore[arg-type]
            model_resource=_model_resource_capabilities(),
        ):
            pass

    assert fake_client_class.created == []


@pytest.mark.asyncio
async def test_empty_host_raises_value_error_before_client_construction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client_class = _make_fake_async_client_class()
    monkeypatch.setattr(bootstrap, "AsyncClient", fake_client_class)

    with pytest.raises(ValueError, match="ollama_host"):
        async with open_direct_runtime(
            workspace_budget=_workspace_budget(),
            ollama_host="",
            model_resource=_model_resource_capabilities(),
        ):
            pass

    assert fake_client_class.created == []


@pytest.mark.asyncio
async def test_whitespace_only_host_raises_value_error_before_client_construction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client_class = _make_fake_async_client_class()
    monkeypatch.setattr(bootstrap, "AsyncClient", fake_client_class)

    with pytest.raises(ValueError, match="ollama_host"):
        async with open_direct_runtime(
            workspace_budget=_workspace_budget(),
            ollama_host="   ",
            model_resource=_model_resource_capabilities(),
        ):
            pass

    assert fake_client_class.created == []


@pytest.mark.asyncio
async def test_valid_host_is_passed_unchanged_to_async_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client_class = _make_fake_async_client_class()
    monkeypatch.setattr(bootstrap, "AsyncClient", fake_client_class)
    supplied_host = "  http://distinctive-host:4141  "

    async with open_direct_runtime(
        workspace_budget=_workspace_budget(),
        ollama_host=supplied_host,
        model_resource=_model_resource_capabilities(),
    ):
        pass

    assert len(fake_client_class.created) == 1
    assert fake_client_class.created[0].host == supplied_host


# --- context-entry side effects (§51) -----------------------------------------


@pytest.mark.asyncio
async def test_entering_context_does_not_invoke_generate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client_class = _make_fake_async_client_class()
    monkeypatch.setattr(bootstrap, "AsyncClient", fake_client_class)

    async with open_direct_runtime(
        workspace_budget=_workspace_budget(),
        ollama_host="host:1",
        model_resource=_model_resource_capabilities(),
    ):
        assert fake_client_class.created[0].generate_calls == []

    assert fake_client_class.created[0].generate_calls == []


# --- C2 realization (§52, §53) ------------------------------------------------


@pytest.mark.asyncio
async def test_fresh_workspace_and_situation_are_constructed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client_class = _make_fake_async_client_class()
    monkeypatch.setattr(bootstrap, "AsyncClient", fake_client_class)
    workspace_budget = _workspace_budget()

    async with open_direct_runtime(
        workspace_budget=workspace_budget,
        ollama_host="host:1",
        model_resource=_model_resource_capabilities(),
    ) as operation:
        state_owner = operation._context_request_assembler._state_owner  # noqa: SLF001
        workspace, situation = state_owner.current_snapshots()

        assert isinstance(state_owner, CognitiveStateOwner)
        assert workspace.version == 0
        assert workspace.items == ()
        assert workspace.focus_item_id is None
        assert workspace.budget is workspace_budget
        assert situation.version == 0
        assert situation.entries == ()


# --- C5 selection-request / provider / client identity (§54, §55, §56) -------


@pytest.mark.asyncio
async def test_selection_request_uses_exact_supplied_model_resource(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client_class = _make_fake_async_client_class()
    monkeypatch.setattr(bootstrap, "AsyncClient", fake_client_class)
    model_resource = _model_resource_capabilities()

    async with open_direct_runtime(
        workspace_budget=_workspace_budget(),
        ollama_host="host:1",
        model_resource=model_resource,
    ) as operation:
        reasoning_executor = operation._reasoning_engine._executor  # noqa: SLF001
        selection_request = reasoning_executor._selection_request  # noqa: SLF001

        assert selection_request.requirements.required_capabilities == frozenset(
            {ModelCapability.TEXT_GENERATION}
        )
        assert selection_request.candidates == frozenset({model_resource})
        assert next(iter(selection_request.candidates)) is model_resource


@pytest.mark.asyncio
async def test_provider_ref_is_derived_from_model_resource(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client_class = _make_fake_async_client_class()
    monkeypatch.setattr(bootstrap, "AsyncClient", fake_client_class)
    model_resource = _model_resource_capabilities()

    async with open_direct_runtime(
        workspace_budget=_workspace_budget(),
        ollama_host="host:1",
        model_resource=model_resource,
    ) as operation:
        reasoning_executor = operation._reasoning_engine._executor  # noqa: SLF001
        execution_engine = reasoning_executor._execution_engine  # noqa: SLF001
        ollama_executor = execution_engine._executor  # noqa: SLF001

        assert ollama_executor._provider_ref == model_resource.resource.provider_ref  # noqa: SLF001


@pytest.mark.asyncio
async def test_ollama_executor_retains_the_exact_entered_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client_class = _make_fake_async_client_class()
    monkeypatch.setattr(bootstrap, "AsyncClient", fake_client_class)

    async with open_direct_runtime(
        workspace_budget=_workspace_budget(),
        ollama_host="host:1",
        model_resource=_model_resource_capabilities(),
    ) as operation:
        reasoning_executor = operation._reasoning_engine._executor  # noqa: SLF001
        execution_engine = reasoning_executor._execution_engine  # noqa: SLF001
        ollama_executor = execution_engine._executor  # noqa: SLF001

        assert ollama_executor._client is fake_client_class.created[0]  # noqa: SLF001


# --- full offline graph execution (§57, §58, §59) -----------------------------


@pytest.mark.asyncio
async def test_full_offline_graph_execution_returns_reasoning_outcome(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client_class = _make_fake_async_client_class(generate_result="the answer")
    monkeypatch.setattr(bootstrap, "AsyncClient", fake_client_class)
    model_resource = _model_resource_capabilities(model_ref="model:distinctive")

    async with open_direct_runtime(
        workspace_budget=_workspace_budget(),
        ollama_host="host:1",
        model_resource=model_resource,
    ) as operation:
        result = await operation.execute(**_execute_kwargs())  # type: ignore[arg-type]

    assert isinstance(result, ReasoningOutcome)
    assert result.problem_ref == "problem:123"
    assert result.strategy is ReasoningStrategy.DIRECT
    assert result.conclusion == "the answer"

    client = fake_client_class.created[0]
    assert len(client.generate_calls) == 1
    call = client.generate_calls[0]
    assert call["model"] == "model:distinctive"
    assert call["prompt"] == "Determine an answer."
    assert call["stream"] is False


# --- cleanup on normal exit (§61) ---------------------------------------------


@pytest.mark.asyncio
async def test_normal_exit_closes_client_exactly_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client_class = _make_fake_async_client_class()
    monkeypatch.setattr(bootstrap, "AsyncClient", fake_client_class)

    async with open_direct_runtime(
        workspace_budget=_workspace_budget(),
        ollama_host="host:1",
        model_resource=_model_resource_capabilities(),
    ):
        pass

    client = fake_client_class.created[0]
    assert client.aenter_count == 1
    assert client.aexit_count == 1


# --- cleanup on execution failure (§62) ---------------------------------------


@pytest.mark.asyncio
async def test_execution_failure_still_closes_client_exactly_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client_class = _make_fake_async_client_class(
        generate_result=RuntimeError("technical failure")
    )
    monkeypatch.setattr(bootstrap, "AsyncClient", fake_client_class)

    with pytest.raises(ReasoningExecutionError):
        async with open_direct_runtime(
            workspace_budget=_workspace_budget(),
            ollama_host="host:1",
            model_resource=_model_resource_capabilities(),
        ) as operation:
            await operation.execute(**_execute_kwargs())  # type: ignore[arg-type]

    assert fake_client_class.created[0].aexit_count == 1


# --- cleanup on graph-construction failure (§63) ------------------------------


@pytest.mark.asyncio
async def test_construction_failure_after_client_entry_still_closes_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client_class = _make_fake_async_client_class()
    monkeypatch.setattr(bootstrap, "AsyncClient", fake_client_class)

    sentinel_error = RuntimeError("sentinel construction failure")

    class _FailingModelSelector:
        def __init__(self, *args: object, **kwargs: object) -> None:
            raise sentinel_error

    monkeypatch.setattr(bootstrap, "ModelSelector", _FailingModelSelector)

    with pytest.raises(RuntimeError) as raised:
        async with open_direct_runtime(
            workspace_budget=_workspace_budget(),
            ollama_host="host:1",
            model_resource=_model_resource_capabilities(),
        ):
            pass

    assert raised.value is sentinel_error
    assert fake_client_class.created[0].aexit_count == 1


# --- wrong-capability ownership remains ModelSelector's (§64) -----------------


@pytest.mark.asyncio
async def test_missing_text_generation_capability_does_not_fail_at_entry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client_class = _make_fake_async_client_class()
    monkeypatch.setattr(bootstrap, "AsyncClient", fake_client_class)
    model_resource_without_text_generation = _model_resource_capabilities(capabilities=frozenset())

    async with open_direct_runtime(
        workspace_budget=_workspace_budget(),
        ollama_host="host:1",
        model_resource=model_resource_without_text_generation,
    ) as operation:
        assert fake_client_class.created[0].generate_calls == []

        with pytest.raises(ReasoningExecutionError):
            await operation.execute(**_execute_kwargs())  # type: ignore[arg-type]

        assert fake_client_class.created[0].generate_calls == []

    assert fake_client_class.created[0].aexit_count == 1


# --- multiple-runtime independence (§65, §66) ---------------------------------


@pytest.mark.asyncio
async def test_two_nested_runtimes_are_fully_independent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client_class = _make_fake_async_client_class()
    monkeypatch.setattr(bootstrap, "AsyncClient", fake_client_class)

    shared_workspace_budget = _workspace_budget()
    shared_model_resource = _model_resource_capabilities()

    async with open_direct_runtime(
        workspace_budget=shared_workspace_budget,
        ollama_host="host:a",
        model_resource=shared_model_resource,
    ) as operation_a:
        async with open_direct_runtime(
            workspace_budget=shared_workspace_budget,
            ollama_host="host:b",
            model_resource=shared_model_resource,
        ) as operation_b:
            assert operation_a is not operation_b

            owner_a = operation_a._context_request_assembler._state_owner  # noqa: SLF001
            owner_b = operation_b._context_request_assembler._state_owner  # noqa: SLF001
            assert owner_a is not owner_b

            workspace_a, situation_a = owner_a.current_snapshots()
            workspace_b, situation_b = owner_b.current_snapshots()
            assert workspace_a is not workspace_b
            assert situation_a is not situation_b
            assert workspace_a.budget is shared_workspace_budget
            assert workspace_b.budget is shared_workspace_budget

            reasoning_executor_a = operation_a._reasoning_engine._executor  # noqa: SLF001
            reasoning_executor_b = operation_b._reasoning_engine._executor  # noqa: SLF001
            execution_engine_a = reasoning_executor_a._execution_engine  # noqa: SLF001
            execution_engine_b = reasoning_executor_b._execution_engine  # noqa: SLF001
            assert execution_engine_a is not execution_engine_b
            assert execution_engine_a._router is not execution_engine_b._router  # noqa: SLF001

            client_a = execution_engine_a._executor._client  # noqa: SLF001
            client_b = execution_engine_b._executor._client  # noqa: SLF001
            assert client_a is not client_b

        assert fake_client_class.created[1].aexit_count == 1
        assert fake_client_class.created[0].aexit_count == 0

    assert fake_client_class.created[0].aexit_count == 1


# --- imports (no forbidden dependency leaks into this module) ----------------


def test_module_source_does_not_import_settings_frameworks() -> None:
    source = inspect.getsource(bootstrap)
    for forbidden in ("pydantic_settings", "dynaconf", "hydra", "BaseSettings"):
        assert forbidden not in source


def test_selector_symbol_used_is_the_real_model_selector() -> None:
    assert bootstrap.ModelSelector is ModelSelector


# --- initial ContextStamp integration through the real graph ------------------


@pytest.mark.asyncio
async def test_initial_context_stamp_propagates_through_the_real_graph(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prove the fresh canonical state built by bootstrap reaches the real
    ``ReasoningRequest`` via C3, without replacing any real component.

    ``ModelReasoningExecutor.execute`` is temporarily wrapped -- not
    replaced -- so the captured request is exactly what the real graph
    (``DirectReasoningOperation`` -> ``ReasoningEngine`` ->
    ``ModelReasoningExecutor`` -> ``ModelExecutionEngine`` -> ``ModelRouter``
    -> ``ModelSelector`` -> ``OllamaModelExecutor``) actually produced and
    executed.
    """
    fake_client_class = _make_fake_async_client_class(generate_result="the answer")
    monkeypatch.setattr(bootstrap, "AsyncClient", fake_client_class)

    captured_requests: list[ReasoningRequest] = []
    original_execute = ModelReasoningExecutor.execute

    async def _capturing_execute(
        self: ModelReasoningExecutor, request: ReasoningRequest
    ) -> ReasoningOutcome:
        captured_requests.append(request)
        return await original_execute(self, request)

    monkeypatch.setattr(ModelReasoningExecutor, "execute", _capturing_execute)

    async with open_direct_runtime(
        workspace_budget=_workspace_budget(),
        ollama_host="host:1",
        model_resource=_model_resource_capabilities(),
    ) as operation:
        result = await operation.execute(**_execute_kwargs())  # type: ignore[arg-type]

    assert isinstance(result, ReasoningOutcome)
    assert len(captured_requests) == 1

    stamp = captured_requests[0].context.request.context_stamp
    assert stamp.workspace_version == 0
    assert stamp.situation_version == 0
    assert stamp.identity_version is ContextVersionMarker.UNMATERIALIZED
    assert stamp.goal_version is ContextVersionMarker.UNMATERIALIZED
    assert stamp.policy_version is ContextVersionMarker.UNMATERIALIZED


# --- same-runtime multi-operation canonical-state continuity -----------------


@pytest.mark.asyncio
async def test_same_runtime_context_retains_canonical_state_across_operations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prove bootstrap does not reconstruct the canonical runtime graph per
    operation: the same assembler/owner/Workspace/Situation identities and
    the same ``DirectReasoningOperation`` serve two sequential executions.

    This does not imply canonical state is immutable or unreplaceable --
    ``CognitiveStateOwner``'s existing exact-successor replacement authority
    is unchanged; it only proves bootstrap wires one graph per context, not
    one graph per operation.
    """
    fake_client_class = _make_fake_async_client_class(generate_result="the answer")
    monkeypatch.setattr(bootstrap, "AsyncClient", fake_client_class)

    async with open_direct_runtime(
        workspace_budget=_workspace_budget(),
        ollama_host="host:1",
        model_resource=_model_resource_capabilities(),
    ) as operation:
        assembler = operation._context_request_assembler  # noqa: SLF001
        state_owner = assembler._state_owner  # noqa: SLF001
        workspace, situation = state_owner.current_snapshots()

        result_a = await operation.execute(
            **_execute_kwargs(problem_ref="problem:a", problem_statement="First question.")
        )  # type: ignore[arg-type]
        result_b = await operation.execute(
            **_execute_kwargs(problem_ref="problem:b", problem_statement="Second question.")
        )  # type: ignore[arg-type]

        assert operation._context_request_assembler is assembler  # noqa: SLF001
        assert assembler._state_owner is state_owner  # noqa: SLF001
        workspace_after, situation_after = state_owner.current_snapshots()
        assert workspace_after is workspace
        assert situation_after is situation

    assert result_a.problem_ref == "problem:a"
    assert result_b.problem_ref == "problem:b"

    client = fake_client_class.created[0]
    assert len(client.generate_calls) == 2
