import copy
import inspect
import json
import os
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest

from noema._process import (
    _execute_first_direct_operation,
    _execute_first_direct_session,
    _FirstDirectInvocationPolicy,
    _FirstDirectProcessConfiguration,
    _load_first_direct_process_configuration,
    _ProcessConfigurationError,
)
from noema.cognition.domain.budget import CognitiveBudget
from noema.cognition.domain.context_composition import ContextSensitivity, ContextTrustLevel
from noema.cognition.domain.errors import InvalidCognitiveBudgetError
from noema.cognition.domain.modes import CognitiveMode
from noema.cognition.domain.reasoning import (
    InformationNeed,
    ReasoningOutcome,
    ReasoningStatus,
    ReasoningStrategy,
)
from noema.cognition.domain.workspace import WorkspaceBudget
from noema.cognition.ports import ReasoningExecutionError
from noema.model_router.domain import ModelCapability, ModelResource, ModelResourceCapabilities
from noema.model_router.domain.errors import InvalidModelResourceError
from noema.shared.domain import DomainError

# --- TOML fixture construction (fixture values only; not runtime defaults) ---


def _valid_tables() -> dict[str, dict[str, dict[str, object]]]:
    return {
        "runtime": {
            "workspace": {
                "max_active_items": 5,
                "max_working_items": 5,
                "max_peripheral_items": 5,
            },
            "ollama": {
                "host": "http://localhost:11434",
            },
            "model": {
                "resource_ref": "resource-1",
                "provider_ref": "ollama",
                "model_ref": "model-1",
                "capabilities": ["text_generation"],
            },
        },
        "direct": {
            "policy": {
                "role": "reasoner",
                "mode": "deliberate",
                "max_sensitivity": "internal",
                "minimum_trust": "unverified",
                "context_max_tokens": 100,
            },
            "budget": {
                "max_time_ms": 1000,
                "max_steps": 1,
                "max_llm_calls": 1,
                "max_tool_calls": 0,
                "max_cost": "0.00",
                "max_tokens": 100,
                "max_search_depth": 0,
            },
        },
    }


def _toml_scalar(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, list):
        return "[" + ", ".join(_toml_scalar(item) for item in value) + "]"
    raise TypeError(f"unsupported fixture TOML value type: {type(value)!r}")


def _toml_text(tables: dict[str, dict[str, dict[str, object]]]) -> str:
    lines: list[str] = []
    for root_key, subtables in tables.items():
        for sub_key, leaves in subtables.items():
            lines.append(f"[{root_key}.{sub_key}]")
            for key, value in leaves.items():
                lines.append(f"{key} = {_toml_scalar(value)}")
            lines.append("")
    return "\n".join(lines)


def _write_config(tmp_path: Path, tables: dict[str, dict[str, dict[str, object]]]) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(_toml_text(tables), encoding="utf-8")
    return path


def _with_leaf(
    tables: dict[str, dict[str, dict[str, object]]],
    root: str,
    sub: str,
    key: str,
    value: object,
) -> dict[str, dict[str, dict[str, object]]]:
    mutated = copy.deepcopy(tables)
    mutated[root][sub][key] = value
    return mutated


def _without_leaf(
    tables: dict[str, dict[str, dict[str, object]]], root: str, sub: str, key: str
) -> dict[str, dict[str, dict[str, object]]]:
    mutated = copy.deepcopy(tables)
    del mutated[root][sub][key]
    return mutated


def _without_subtable(
    tables: dict[str, dict[str, dict[str, object]]], root: str, sub: str
) -> dict[str, dict[str, dict[str, object]]]:
    mutated = copy.deepcopy(tables)
    del mutated[root][sub]
    return mutated


def _without_root(
    tables: dict[str, dict[str, dict[str, object]]], root: str
) -> dict[str, dict[str, dict[str, object]]]:
    mutated: dict[str, Any] = copy.deepcopy(tables)
    del mutated[root]
    return mutated


_ALL_LEAVES = [
    ("runtime", "workspace", "max_active_items"),
    ("runtime", "workspace", "max_working_items"),
    ("runtime", "workspace", "max_peripheral_items"),
    ("runtime", "ollama", "host"),
    ("runtime", "model", "resource_ref"),
    ("runtime", "model", "provider_ref"),
    ("runtime", "model", "model_ref"),
    ("runtime", "model", "capabilities"),
    ("direct", "policy", "role"),
    ("direct", "policy", "mode"),
    ("direct", "policy", "max_sensitivity"),
    ("direct", "policy", "minimum_trust"),
    ("direct", "policy", "context_max_tokens"),
    ("direct", "budget", "max_time_ms"),
    ("direct", "budget", "max_steps"),
    ("direct", "budget", "max_llm_calls"),
    ("direct", "budget", "max_tool_calls"),
    ("direct", "budget", "max_cost"),
    ("direct", "budget", "max_tokens"),
    ("direct", "budget", "max_search_depth"),
]

_INT_LEAVES = [
    ("runtime", "workspace", "max_active_items"),
    ("runtime", "workspace", "max_working_items"),
    ("runtime", "workspace", "max_peripheral_items"),
    ("direct", "policy", "context_max_tokens"),
    ("direct", "budget", "max_time_ms"),
    ("direct", "budget", "max_steps"),
    ("direct", "budget", "max_llm_calls"),
    ("direct", "budget", "max_tool_calls"),
    ("direct", "budget", "max_tokens"),
    ("direct", "budget", "max_search_depth"),
]

_STR_LEAVES = [
    ("runtime", "ollama", "host"),
    ("runtime", "model", "resource_ref"),
    ("runtime", "model", "provider_ref"),
    ("runtime", "model", "model_ref"),
    ("direct", "policy", "role"),
    ("direct", "budget", "max_cost"),
]


def test_config_leaf_key_count_is_twenty() -> None:
    assert len(_ALL_LEAVES) == 20


# --- successful resolution (§91) --------------------------------------------


def test_loader_success_constructs_exact_configuration(tmp_path: Path) -> None:
    path = _write_config(tmp_path, _valid_tables())

    configuration = _load_first_direct_process_configuration(path)

    assert isinstance(configuration, _FirstDirectProcessConfiguration)
    assert configuration.workspace_budget == WorkspaceBudget(
        max_active_items=5, max_working_items=5, max_peripheral_items=5
    )
    assert configuration.ollama_host == "http://localhost:11434"
    assert isinstance(configuration.model_resource, ModelResourceCapabilities)
    assert configuration.model_resource.resource == ModelResource(
        resource_ref="resource-1", provider_ref="ollama", model_ref="model-1"
    )
    assert configuration.model_resource.capabilities == frozenset({ModelCapability.TEXT_GENERATION})

    policy = configuration.invocation_policy
    assert isinstance(policy, _FirstDirectInvocationPolicy)
    assert policy.role == "reasoner"
    assert policy.mode is CognitiveMode.DELIBERATE
    assert policy.max_sensitivity is ContextSensitivity.INTERNAL
    assert policy.minimum_trust is ContextTrustLevel.UNVERIFIED
    assert policy.context_max_tokens == 100
    assert policy.cognitive_budget == CognitiveBudget(
        max_time=timedelta(milliseconds=1000),
        max_steps=1,
        max_llm_calls=1,
        max_tool_calls=0,
        max_cost=Decimal("0.00"),
        max_tokens=100,
        max_search_depth=0,
    )


# --- root/table strictness (§92) --------------------------------------------


@pytest.mark.parametrize("root", ["runtime", "direct"])
def test_missing_root_table_errors(tmp_path: Path, root: str) -> None:
    path = _write_config(tmp_path, _without_root(_valid_tables(), root))

    with pytest.raises(_ProcessConfigurationError):
        _load_first_direct_process_configuration(path)


def test_unknown_root_table_errors(tmp_path: Path) -> None:
    tables = _valid_tables()
    tables["extra"] = {"section": {"key": "value"}}
    path = _write_config(tmp_path, tables)

    with pytest.raises(_ProcessConfigurationError):
        _load_first_direct_process_configuration(path)


@pytest.mark.parametrize("sub", ["workspace", "ollama", "model"])
def test_missing_runtime_subtable_errors(tmp_path: Path, sub: str) -> None:
    path = _write_config(tmp_path, _without_subtable(_valid_tables(), "runtime", sub))

    with pytest.raises(_ProcessConfigurationError):
        _load_first_direct_process_configuration(path)


def test_unknown_runtime_subtable_errors(tmp_path: Path) -> None:
    tables = _valid_tables()
    tables["runtime"]["extra"] = {"key": "value"}
    path = _write_config(tmp_path, tables)

    with pytest.raises(_ProcessConfigurationError):
        _load_first_direct_process_configuration(path)


@pytest.mark.parametrize("sub", ["policy", "budget"])
def test_missing_direct_subtable_errors(tmp_path: Path, sub: str) -> None:
    path = _write_config(tmp_path, _without_subtable(_valid_tables(), "direct", sub))

    with pytest.raises(_ProcessConfigurationError):
        _load_first_direct_process_configuration(path)


def test_unknown_direct_subtable_errors(tmp_path: Path) -> None:
    tables = _valid_tables()
    tables["direct"]["extra"] = {"key": "value"}
    path = _write_config(tmp_path, tables)

    with pytest.raises(_ProcessConfigurationError):
        _load_first_direct_process_configuration(path)


# --- leaf-key strictness (§92) -----------------------------------------------


@pytest.mark.parametrize(("root", "sub", "key"), _ALL_LEAVES)
def test_missing_leaf_key_errors(tmp_path: Path, root: str, sub: str, key: str) -> None:
    path = _write_config(tmp_path, _without_leaf(_valid_tables(), root, sub, key))

    with pytest.raises(_ProcessConfigurationError):
        _load_first_direct_process_configuration(path)


@pytest.mark.parametrize(
    ("root", "sub"),
    [("runtime", "workspace"), ("runtime", "ollama"), ("runtime", "model")],
)
def test_unknown_runtime_leaf_key_errors(tmp_path: Path, root: str, sub: str) -> None:
    tables = _with_leaf(_valid_tables(), root, sub, "unexpected_key", "value")
    path = _write_config(tmp_path, tables)

    with pytest.raises(_ProcessConfigurationError):
        _load_first_direct_process_configuration(path)


@pytest.mark.parametrize(("root", "sub"), [("direct", "policy"), ("direct", "budget")])
def test_unknown_direct_leaf_key_errors(tmp_path: Path, root: str, sub: str) -> None:
    tables = _with_leaf(_valid_tables(), root, sub, "unexpected_key", "value")
    path = _write_config(tmp_path, tables)

    with pytest.raises(_ProcessConfigurationError):
        _load_first_direct_process_configuration(path)


# --- transport-type strictness (§93/§94) ------------------------------------


@pytest.mark.parametrize(("root", "sub", "key"), _INT_LEAVES)
def test_bool_rejected_for_integer_leaves(tmp_path: Path, root: str, sub: str, key: str) -> None:
    tables = _with_leaf(_valid_tables(), root, sub, key, True)
    path = _write_config(tmp_path, tables)

    with pytest.raises(_ProcessConfigurationError):
        _load_first_direct_process_configuration(path)


@pytest.mark.parametrize(("root", "sub", "key"), _INT_LEAVES)
def test_string_rejected_for_integer_leaves(tmp_path: Path, root: str, sub: str, key: str) -> None:
    tables = _with_leaf(_valid_tables(), root, sub, key, "not-an-int")
    path = _write_config(tmp_path, tables)

    with pytest.raises(_ProcessConfigurationError):
        _load_first_direct_process_configuration(path)


@pytest.mark.parametrize(("root", "sub", "key"), _STR_LEAVES)
def test_int_rejected_for_string_leaves(tmp_path: Path, root: str, sub: str, key: str) -> None:
    tables = _with_leaf(_valid_tables(), root, sub, key, 123)
    path = _write_config(tmp_path, tables)

    with pytest.raises(_ProcessConfigurationError):
        _load_first_direct_process_configuration(path)


def test_capabilities_wrong_element_type_errors(tmp_path: Path) -> None:
    tables = _with_leaf(_valid_tables(), "runtime", "model", "capabilities", [1, 2])
    path = _write_config(tmp_path, tables)

    with pytest.raises(_ProcessConfigurationError):
        _load_first_direct_process_configuration(path)


def test_capabilities_not_a_list_errors(tmp_path: Path) -> None:
    tables = _with_leaf(_valid_tables(), "runtime", "model", "capabilities", "text_generation")
    path = _write_config(tmp_path, tables)

    with pytest.raises(_ProcessConfigurationError):
        _load_first_direct_process_configuration(path)


# --- capability conversion (§95) ---------------------------------------------


def test_capabilities_valid_values(tmp_path: Path) -> None:
    tables = _with_leaf(
        _valid_tables(),
        "runtime",
        "model",
        "capabilities",
        ["text_generation", "structured_output", "tool_calling"],
    )
    path = _write_config(tmp_path, tables)

    configuration = _load_first_direct_process_configuration(path)

    assert configuration.model_resource.capabilities == frozenset(
        {
            ModelCapability.TEXT_GENERATION,
            ModelCapability.STRUCTURED_OUTPUT,
            ModelCapability.TOOL_CALLING,
        }
    )


def test_capabilities_empty_list_accepted(tmp_path: Path) -> None:
    tables = _with_leaf(_valid_tables(), "runtime", "model", "capabilities", [])
    path = _write_config(tmp_path, tables)

    configuration = _load_first_direct_process_configuration(path)

    assert configuration.model_resource.capabilities == frozenset()


def test_capabilities_without_text_generation_accepted(tmp_path: Path) -> None:
    tables = _with_leaf(_valid_tables(), "runtime", "model", "capabilities", ["structured_output"])
    path = _write_config(tmp_path, tables)

    configuration = _load_first_direct_process_configuration(path)

    assert configuration.model_resource.capabilities == frozenset(
        {ModelCapability.STRUCTURED_OUTPUT}
    )


def test_capabilities_unknown_value_errors(tmp_path: Path) -> None:
    tables = _with_leaf(_valid_tables(), "runtime", "model", "capabilities", ["not_a_capability"])
    path = _write_config(tmp_path, tables)

    with pytest.raises(_ProcessConfigurationError):
        _load_first_direct_process_configuration(path)


def test_capabilities_duplicate_declaration_errors(tmp_path: Path) -> None:
    tables = _with_leaf(
        _valid_tables(),
        "runtime",
        "model",
        "capabilities",
        ["text_generation", "text_generation"],
    )
    path = _write_config(tmp_path, tables)

    with pytest.raises(_ProcessConfigurationError):
        _load_first_direct_process_configuration(path)


# --- enum conversion (§96) ---------------------------------------------------


@pytest.mark.parametrize("value", ["reflex", "fast", "deliberate", "deep"])
def test_mode_valid_values(tmp_path: Path, value: str) -> None:
    tables = _with_leaf(_valid_tables(), "direct", "policy", "mode", value)
    path = _write_config(tmp_path, tables)

    configuration = _load_first_direct_process_configuration(path)

    assert configuration.invocation_policy.mode is CognitiveMode(value)


def test_mode_unknown_value_errors(tmp_path: Path) -> None:
    tables = _with_leaf(_valid_tables(), "direct", "policy", "mode", "not_a_mode")
    path = _write_config(tmp_path, tables)

    with pytest.raises(_ProcessConfigurationError):
        _load_first_direct_process_configuration(path)


def test_mode_case_changed_value_rejected(tmp_path: Path) -> None:
    tables = _with_leaf(_valid_tables(), "direct", "policy", "mode", "Deliberate")
    path = _write_config(tmp_path, tables)

    with pytest.raises(_ProcessConfigurationError):
        _load_first_direct_process_configuration(path)


@pytest.mark.parametrize("value", ["public", "internal", "private", "secret"])
def test_max_sensitivity_valid_values(tmp_path: Path, value: str) -> None:
    tables = _with_leaf(_valid_tables(), "direct", "policy", "max_sensitivity", value)
    path = _write_config(tmp_path, tables)

    configuration = _load_first_direct_process_configuration(path)

    assert configuration.invocation_policy.max_sensitivity is ContextSensitivity(value)


def test_max_sensitivity_unknown_value_errors(tmp_path: Path) -> None:
    tables = _with_leaf(_valid_tables(), "direct", "policy", "max_sensitivity", "not_a_level")
    path = _write_config(tmp_path, tables)

    with pytest.raises(_ProcessConfigurationError):
        _load_first_direct_process_configuration(path)


@pytest.mark.parametrize("value", ["trusted", "unverified", "untrusted"])
def test_minimum_trust_valid_values(tmp_path: Path, value: str) -> None:
    tables = _with_leaf(_valid_tables(), "direct", "policy", "minimum_trust", value)
    path = _write_config(tmp_path, tables)

    configuration = _load_first_direct_process_configuration(path)

    assert configuration.invocation_policy.minimum_trust is ContextTrustLevel(value)


def test_minimum_trust_unknown_value_errors(tmp_path: Path) -> None:
    tables = _with_leaf(_valid_tables(), "direct", "policy", "minimum_trust", "not_a_trust")
    path = _write_config(tmp_path, tables)

    with pytest.raises(_ProcessConfigurationError):
        _load_first_direct_process_configuration(path)


def test_minimum_trust_case_changed_value_rejected(tmp_path: Path) -> None:
    tables = _with_leaf(_valid_tables(), "direct", "policy", "minimum_trust", "TRUSTED")
    path = _write_config(tmp_path, tables)

    with pytest.raises(_ProcessConfigurationError):
        _load_first_direct_process_configuration(path)


# --- Decimal conversion (§97) -------------------------------------------------


def test_max_cost_valid_decimal_string(tmp_path: Path) -> None:
    tables = _with_leaf(_valid_tables(), "direct", "budget", "max_cost", "12.50")
    path = _write_config(tmp_path, tables)

    configuration = _load_first_direct_process_configuration(path)

    assert configuration.invocation_policy.cognitive_budget.max_cost == Decimal("12.50")


def test_max_cost_invalid_decimal_syntax_errors(tmp_path: Path) -> None:
    tables = _with_leaf(_valid_tables(), "direct", "budget", "max_cost", "not-a-decimal")
    path = _write_config(tmp_path, tables)

    with pytest.raises(_ProcessConfigurationError):
        _load_first_direct_process_configuration(path)


def test_max_cost_negative_valid_syntax_propagates_domain_error(tmp_path: Path) -> None:
    tables = _with_leaf(_valid_tables(), "direct", "budget", "max_cost", "-1")
    path = _write_config(tmp_path, tables)

    with pytest.raises(InvalidCognitiveBudgetError):
        _load_first_direct_process_configuration(path)


# --- max_time conversion (§98) ------------------------------------------------


def test_max_time_ms_converts_to_exact_timedelta(tmp_path: Path) -> None:
    tables = _with_leaf(_valid_tables(), "direct", "budget", "max_time_ms", 2500)
    path = _write_config(tmp_path, tables)

    configuration = _load_first_direct_process_configuration(path)

    assert configuration.invocation_policy.cognitive_budget.max_time == timedelta(milliseconds=2500)


def test_max_time_ms_zero_propagates_domain_error(tmp_path: Path) -> None:
    tables = _with_leaf(_valid_tables(), "direct", "budget", "max_time_ms", 0)
    path = _write_config(tmp_path, tables)

    with pytest.raises(InvalidCognitiveBudgetError):
        _load_first_direct_process_configuration(path)


# --- domain-error propagation (§99/§100) -------------------------------------


def test_workspace_budget_domain_error_propagates_unchanged(tmp_path: Path) -> None:
    tables = _with_leaf(_valid_tables(), "runtime", "workspace", "max_active_items", 0)
    path = _write_config(tmp_path, tables)

    with pytest.raises(DomainError):
        _load_first_direct_process_configuration(path)


def test_model_resource_domain_error_propagates_unchanged(tmp_path: Path) -> None:
    tables = _with_leaf(_valid_tables(), "runtime", "model", "resource_ref", "   ")
    path = _write_config(tmp_path, tables)

    with pytest.raises(InvalidModelResourceError):
        _load_first_direct_process_configuration(path)


# --- host ownership (§101) ----------------------------------------------------


def test_loader_accepts_blank_host_transport(tmp_path: Path) -> None:
    """P1 performs no nonblank-host check; that remains bootstrap authority."""
    tables = _with_leaf(_valid_tables(), "runtime", "ollama", "host", "")
    path = _write_config(tmp_path, tables)

    configuration = _load_first_direct_process_configuration(path)

    assert configuration.ollama_host == ""


# --- path / search / environment (§102/§103) ---------------------------------


def test_missing_config_path_raises_os_error_with_no_fallback_search(tmp_path: Path) -> None:
    other_config = tmp_path / "noema.toml"
    other_config.write_text(_toml_text(_valid_tables()), encoding="utf-8")

    missing_path = tmp_path / "does-not-exist.toml"

    with pytest.raises(OSError):
        _load_first_direct_process_configuration(missing_path)


def test_loader_does_not_consult_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OLLAMA_HOST", "http://from-env:1234")
    monkeypatch.setenv("NOEMA_CONFIG", str(tmp_path / "elsewhere.toml"))
    path = _write_config(tmp_path, _valid_tables())

    configuration = _load_first_direct_process_configuration(path)

    assert configuration.ollama_host == "http://localhost:11434"
    assert os.environ["OLLAMA_HOST"] == "http://from-env:1234"


# --- process session / per-operation helper fixtures (M0-17) ------------------


def _configuration() -> _FirstDirectProcessConfiguration:
    return _FirstDirectProcessConfiguration(
        workspace_budget=WorkspaceBudget(
            max_active_items=1, max_working_items=1, max_peripheral_items=1
        ),
        ollama_host="http://localhost:11434",
        model_resource=ModelResourceCapabilities(
            resource=ModelResource(
                resource_ref="resource-1", provider_ref="ollama", model_ref="model-1"
            ),
            capabilities=frozenset({ModelCapability.TEXT_GENERATION}),
        ),
        invocation_policy=_FirstDirectInvocationPolicy(
            role="reasoner",
            mode=CognitiveMode.DELIBERATE,
            max_sensitivity=ContextSensitivity.INTERNAL,
            minimum_trust=ContextTrustLevel.UNVERIFIED,
            context_max_tokens=100,
            cognitive_budget=CognitiveBudget(
                max_time=timedelta(seconds=1),
                max_steps=1,
                max_llm_calls=1,
                max_tool_calls=0,
                max_cost=Decimal("0"),
                max_tokens=100,
                max_search_depth=0,
            ),
        ),
    )


def _completed_outcome() -> ReasoningOutcome:
    return ReasoningOutcome(
        problem_ref="problem:x",
        strategy=ReasoningStrategy.DIRECT,
        status=ReasoningStatus.COMPLETED,
        conclusion="the answer",
        reason_summary="direct reasoning",
        information_needs=(),
    )


def _policy() -> _FirstDirectInvocationPolicy:
    return _configuration().invocation_policy


def _patch_uuid_sequence(monkeypatch: pytest.MonkeyPatch, count: int) -> list[UUID]:
    """Patch ``noema._process.uuid4`` to yield a deterministic ascending sequence."""
    fixed_uuids = [UUID(int=index + 1) for index in range(count)]
    call_count = 0

    def _fake_uuid4() -> UUID:
        nonlocal call_count
        value = fixed_uuids[call_count]
        call_count += 1
        return value

    monkeypatch.setattr("noema._process.uuid4", _fake_uuid4)
    return fixed_uuids


class _FakeOperation:
    """Records every execute() call and returns/raises results in call order."""

    def __init__(self, *, results: list[object] | None = None) -> None:
        self.results: list[object] = results if results is not None else [_completed_outcome()]
        self.execute_calls: list[dict[str, object]] = []

    async def execute(self, **kwargs: object) -> ReasoningOutcome:
        result = self.results[len(self.execute_calls)]
        self.execute_calls.append(kwargs)
        if isinstance(result, BaseException):
            raise result
        assert isinstance(result, ReasoningOutcome)
        return result


class _FakeRuntimeContext:
    """A fake ``open_direct_runtime`` context manager for offline testing."""

    def __init__(
        self,
        *,
        workspace_budget: object,
        ollama_host: object,
        model_resource: object,
        operation: _FakeOperation | None = None,
        entry_exception: BaseException | None = None,
    ) -> None:
        self.workspace_budget = workspace_budget
        self.ollama_host = ollama_host
        self.model_resource = model_resource
        self.operation = operation
        self.entry_exception = entry_exception
        self.aenter_call_count = 0
        self.aexit_call_count = 0

    async def __aenter__(self) -> _FakeOperation:
        self.aenter_call_count += 1
        if self.entry_exception is not None:
            raise self.entry_exception
        assert self.operation is not None
        return self.operation

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> bool:
        self.aexit_call_count += 1
        return False


def _patch_runtime(monkeypatch: pytest.MonkeyPatch, context: _FakeRuntimeContext) -> None:
    def _fake_open_direct_runtime(
        *, workspace_budget: object, ollama_host: object, model_resource: object
    ) -> _FakeRuntimeContext:
        context.workspace_budget = workspace_budget
        context.ollama_host = ollama_host
        context.model_resource = model_resource
        return context

    monkeypatch.setattr("noema._process.open_direct_runtime", _fake_open_direct_runtime)


# --- per-operation helper: shape and UUID generation (§33) --------------------


def test_execute_first_direct_operation_is_a_coroutine_function() -> None:
    assert inspect.iscoroutinefunction(_execute_first_direct_operation)


@pytest.mark.asyncio
async def test_execute_first_direct_operation_generates_two_distinct_uuid4_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixed_uuids = _patch_uuid_sequence(monkeypatch, 2)
    operation = _FakeOperation()

    await _execute_first_direct_operation(
        operation=operation, policy=_policy(), problem_statement="hello"
    )

    assert len(operation.execute_calls) == 1
    kwargs = operation.execute_calls[0]
    assert kwargs["task_ref"] == str(fixed_uuids[0])
    assert kwargs["problem_ref"] == str(fixed_uuids[1])
    assert kwargs["task_ref"] != kwargs["problem_ref"]


@pytest.mark.asyncio
async def test_execute_first_direct_operation_passes_exact_p2_mapping(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_uuid_sequence(monkeypatch, 2)
    operation = _FakeOperation()
    policy = _policy()

    result = await _execute_first_direct_operation(
        operation=operation, policy=policy, problem_statement="Explain this."
    )

    assert len(operation.execute_calls) == 1
    kwargs = operation.execute_calls[0]
    assert kwargs["role"] == policy.role
    assert kwargs["goal_ref"] is None
    assert kwargs["mode"] is policy.mode
    assert kwargs["required_slice_types"] == ()
    assert kwargs["forbidden_slice_types"] == ()
    assert kwargs["max_sensitivity"] is policy.max_sensitivity
    assert kwargs["minimum_trust"] is policy.minimum_trust
    assert kwargs["allowed_authorities"] == ()
    assert kwargs["max_age"] is None
    assert kwargs["max_tokens"] == policy.context_max_tokens
    assert kwargs["problem_statement"] == "Explain this."
    assert kwargs["budget"] is policy.cognitive_budget
    assert result is operation.results[0]


@pytest.mark.asyncio
async def test_execute_first_direct_operation_propagates_exception_unchanged_with_no_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_uuid_sequence(monkeypatch, 2)
    sentinel = ReasoningExecutionError("technical failure")
    operation = _FakeOperation(results=[sentinel])

    with pytest.raises(ReasoningExecutionError) as raised:
        await _execute_first_direct_operation(
            operation=operation, policy=_policy(), problem_statement="hello"
        )

    assert raised.value is sentinel
    assert len(operation.execute_calls) == 1


@pytest.mark.asyncio
async def test_execute_first_direct_operation_propagates_operation_valueerror_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_uuid_sequence(monkeypatch, 2)
    sentinel = ValueError("sentinel")
    operation = _FakeOperation(results=[sentinel])

    with pytest.raises(ValueError) as raised:
        await _execute_first_direct_operation(
            operation=operation, policy=_policy(), problem_statement="hello"
        )

    assert raised.value is sentinel
    assert not isinstance(raised.value, _ProcessConfigurationError)


# --- per-operation helper: repeated/fresh identity (§34) -----------------------


@pytest.mark.asyncio
async def test_execute_first_direct_operation_generates_fresh_refs_across_repeated_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixed_uuids = _patch_uuid_sequence(monkeypatch, 4)
    operation = _FakeOperation(results=[_completed_outcome(), _completed_outcome()])
    policy = _policy()

    await _execute_first_direct_operation(
        operation=operation, policy=policy, problem_statement="same problem"
    )
    await _execute_first_direct_operation(
        operation=operation, policy=policy, problem_statement="same problem"
    )

    assert len(operation.execute_calls) == 2
    first_kwargs, second_kwargs = operation.execute_calls
    assert first_kwargs["task_ref"] == str(fixed_uuids[0])
    assert first_kwargs["problem_ref"] == str(fixed_uuids[1])
    assert second_kwargs["task_ref"] == str(fixed_uuids[2])
    assert second_kwargs["problem_ref"] == str(fixed_uuids[3])
    assert {
        first_kwargs["task_ref"],
        first_kwargs["problem_ref"],
        second_kwargs["task_ref"],
        second_kwargs["problem_ref"],
    } == {str(value) for value in fixed_uuids}


# --- session executor: success (§35) -------------------------------------------


@pytest.mark.asyncio
async def test_execute_first_direct_session_opens_exactly_one_runtime_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_uuid_sequence(monkeypatch, 4)
    operation = _FakeOperation(results=[_completed_outcome(), _completed_outcome()])
    configuration = _configuration()
    context = _FakeRuntimeContext(
        workspace_budget=None, ollama_host=None, model_resource=None, operation=operation
    )
    _patch_runtime(monkeypatch, context)

    await _execute_first_direct_session(
        configuration=configuration, problem_statements=("first", "second")
    )

    assert context.aenter_call_count == 1
    assert context.aexit_call_count == 1
    assert context.workspace_budget is configuration.workspace_budget
    assert context.ollama_host == configuration.ollama_host
    assert context.model_resource is configuration.model_resource


@pytest.mark.asyncio
async def test_execute_first_direct_session_uses_same_policy_for_every_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_uuid_sequence(monkeypatch, 6)
    operation = _FakeOperation(
        results=[_completed_outcome(), _completed_outcome(), _completed_outcome()]
    )
    configuration = _configuration()
    context = _FakeRuntimeContext(
        workspace_budget=None, ollama_host=None, model_resource=None, operation=operation
    )
    _patch_runtime(monkeypatch, context)

    await _execute_first_direct_session(
        configuration=configuration, problem_statements=("a", "b", "c")
    )

    assert len(operation.execute_calls) == 3
    policy = configuration.invocation_policy
    for kwargs in operation.execute_calls:
        assert kwargs["role"] == policy.role
        assert kwargs["mode"] is policy.mode
        assert kwargs["max_sensitivity"] is policy.max_sensitivity
        assert kwargs["minimum_trust"] is policy.minimum_trust
        assert kwargs["max_tokens"] == policy.context_max_tokens
        assert kwargs["budget"] is policy.cognitive_budget


@pytest.mark.asyncio
async def test_execute_first_direct_session_executes_in_exact_problem_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_uuid_sequence(monkeypatch, 6)
    operation = _FakeOperation(
        results=[_completed_outcome(), _completed_outcome(), _completed_outcome()]
    )
    configuration = _configuration()
    context = _FakeRuntimeContext(
        workspace_budget=None, ollama_host=None, model_resource=None, operation=operation
    )
    _patch_runtime(monkeypatch, context)

    await _execute_first_direct_session(
        configuration=configuration, problem_statements=("first", "second", "third")
    )

    assert [kwargs["problem_statement"] for kwargs in operation.execute_calls] == [
        "first",
        "second",
        "third",
    ]


@pytest.mark.asyncio
async def test_execute_first_direct_session_returns_ordered_outcome_tuple(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_uuid_sequence(monkeypatch, 4)
    first_outcome = _completed_outcome()
    second_outcome = _completed_outcome()
    operation = _FakeOperation(results=[first_outcome, second_outcome])
    configuration = _configuration()
    context = _FakeRuntimeContext(
        workspace_budget=None, ollama_host=None, model_resource=None, operation=operation
    )
    _patch_runtime(monkeypatch, context)

    result = await _execute_first_direct_session(
        configuration=configuration, problem_statements=("first", "second")
    )

    assert isinstance(result, tuple)
    assert result == (first_outcome, second_outcome)


@pytest.mark.asyncio
async def test_execute_first_direct_session_generates_fresh_refs_per_operation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixed_uuids = _patch_uuid_sequence(monkeypatch, 4)
    operation = _FakeOperation(results=[_completed_outcome(), _completed_outcome()])
    configuration = _configuration()
    context = _FakeRuntimeContext(
        workspace_budget=None, ollama_host=None, model_resource=None, operation=operation
    )
    _patch_runtime(monkeypatch, context)

    await _execute_first_direct_session(
        configuration=configuration,
        problem_statements=("same problem", "same problem"),
    )

    first_kwargs, second_kwargs = operation.execute_calls
    assert first_kwargs["task_ref"] == str(fixed_uuids[0])
    assert first_kwargs["problem_ref"] == str(fixed_uuids[1])
    assert second_kwargs["task_ref"] == str(fixed_uuids[2])
    assert second_kwargs["problem_ref"] == str(fixed_uuids[3])


@pytest.mark.asyncio
async def test_execute_first_direct_session_with_one_problem_executes_exactly_one_operation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_uuid_sequence(monkeypatch, 2)
    operation = _FakeOperation()
    configuration = _configuration()
    context = _FakeRuntimeContext(
        workspace_budget=None, ollama_host=None, model_resource=None, operation=operation
    )
    _patch_runtime(monkeypatch, context)

    result = await _execute_first_direct_session(
        configuration=configuration, problem_statements=("hello",)
    )

    assert len(operation.execute_calls) == 1
    assert result == (operation.results[0],)


# --- session executor: failure (§36) -------------------------------------------


@pytest.mark.asyncio
async def test_execute_first_direct_session_reasoning_execution_error_aborts_at_k(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_uuid_sequence(monkeypatch, 6)
    sentinel = ReasoningExecutionError("technical failure")
    operation = _FakeOperation(results=[_completed_outcome(), sentinel])
    configuration = _configuration()
    context = _FakeRuntimeContext(
        workspace_budget=None, ollama_host=None, model_resource=None, operation=operation
    )
    _patch_runtime(monkeypatch, context)

    with pytest.raises(ReasoningExecutionError) as raised:
        await _execute_first_direct_session(
            configuration=configuration,
            problem_statements=("first", "second", "third"),
        )

    assert raised.value is sentinel
    assert len(operation.execute_calls) == 2
    assert context.aenter_call_count == 1
    assert context.aexit_call_count == 1


@pytest.mark.asyncio
async def test_execute_first_direct_session_domain_error_aborts_at_k(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_uuid_sequence(monkeypatch, 6)
    sentinel = DomainError("domain invariant violated")
    operation = _FakeOperation(results=[_completed_outcome(), sentinel])
    configuration = _configuration()
    context = _FakeRuntimeContext(
        workspace_budget=None, ollama_host=None, model_resource=None, operation=operation
    )
    _patch_runtime(monkeypatch, context)

    with pytest.raises(DomainError) as raised:
        await _execute_first_direct_session(
            configuration=configuration,
            problem_statements=("first", "second", "third"),
        )

    assert raised.value is sentinel
    assert len(operation.execute_calls) == 2
    assert context.aenter_call_count == 1
    assert context.aexit_call_count == 1


@pytest.mark.asyncio
async def test_execute_first_direct_session_unexpected_valueerror_aborts_at_k(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_uuid_sequence(monkeypatch, 6)
    sentinel = ValueError("unexpected defect")
    operation = _FakeOperation(results=[_completed_outcome(), sentinel])
    configuration = _configuration()
    context = _FakeRuntimeContext(
        workspace_budget=None, ollama_host=None, model_resource=None, operation=operation
    )
    _patch_runtime(monkeypatch, context)

    with pytest.raises(ValueError) as raised:
        await _execute_first_direct_session(
            configuration=configuration,
            problem_statements=("first", "second", "third"),
        )

    assert raised.value is sentinel
    assert not isinstance(raised.value, _ProcessConfigurationError)
    assert len(operation.execute_calls) == 2
    assert context.aenter_call_count == 1
    assert context.aexit_call_count == 1


# --- session executor: runtime-entry translation (§37) -------------------------


@pytest.mark.asyncio
async def test_execute_first_direct_session_translates_runtime_entry_valueerror(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = ValueError("ollama_host must be a non-empty string")
    context = _FakeRuntimeContext(
        workspace_budget=None,
        ollama_host=None,
        model_resource=None,
        entry_exception=original,
    )
    _patch_runtime(monkeypatch, context)

    with pytest.raises(_ProcessConfigurationError) as raised:
        await _execute_first_direct_session(
            configuration=_configuration(), problem_statements=("hello",)
        )

    assert str(raised.value) == str(original)
    assert raised.value.__cause__ is original


# --- session executor: valid semantic statuses (§38) ---------------------------


@pytest.mark.asyncio
async def test_execute_first_direct_session_continues_after_non_completed_valid_outcomes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_uuid_sequence(monkeypatch, 8)
    partial_outcome = ReasoningOutcome(
        problem_ref="problem:partial",
        strategy=ReasoningStrategy.DIRECT,
        status=ReasoningStatus.PARTIAL,
        conclusion="a partial answer",
        reason_summary="partial reasoning",
        information_needs=(InformationNeed(subject_ref="internal-ref-x", description="clarify"),),
    )
    unresolved_outcome = ReasoningOutcome(
        problem_ref="problem:unresolved",
        strategy=ReasoningStrategy.DIRECT,
        status=ReasoningStatus.UNRESOLVED,
        conclusion=None,
        reason_summary="could not resolve",
        information_needs=(),
    )
    completed_outcome = _completed_outcome()
    operation = _FakeOperation(results=[partial_outcome, unresolved_outcome, completed_outcome])
    configuration = _configuration()
    context = _FakeRuntimeContext(
        workspace_budget=None, ollama_host=None, model_resource=None, operation=operation
    )
    _patch_runtime(monkeypatch, context)

    result = await _execute_first_direct_session(
        configuration=configuration,
        problem_statements=("first", "second", "third"),
    )

    assert result == (partial_outcome, unresolved_outcome, completed_outcome)
    assert len(operation.execute_calls) == 3
