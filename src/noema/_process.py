"""Process-private configuration and execution realization for the first
DIRECT one-shot CLI process.

This module is a top-level, process-private outer edge -- not a bounded
context, not a public API, and not the composition root (``noema.bootstrap``,
ADR-0029). It resolves already-frozen first-DIRECT process policy (P1
configuration source, P2 invocation contract, P3 execution shell) into
exactly the inputs ``noema.bootstrap.open_direct_runtime`` and
``DirectReasoningOperation.execute`` already require. No bounded-context
internal package may import this module; only ``noema.main`` does.
"""

from __future__ import annotations

import tomllib
from contextlib import AsyncExitStack
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from uuid import uuid4

from noema.bootstrap import open_direct_runtime
from noema.cognition.domain.budget import CognitiveBudget
from noema.cognition.domain.context_composition import (
    ContextSensitivity,
    ContextTrustLevel,
)
from noema.cognition.domain.modes import CognitiveMode
from noema.cognition.domain.reasoning import ReasoningOutcome
from noema.cognition.domain.workspace import WorkspaceBudget
from noema.model_router.domain import ModelCapability, ModelResource, ModelResourceCapabilities


class _ProcessConfigurationError(ValueError):
    """A private process-configuration transport/schema/conversion failure.

    Raised only within this process-private configuration boundary: strict
    TOML schema violations (missing/unknown tables or keys), transport-type
    mismatches, enum/capability conversion failures, invalid ``Decimal``
    syntax, and translated runtime-entry ``ValueError`` (an invalid Ollama
    host). Existing domain errors (``DomainError`` and its subtypes) are
    never wrapped into this type; they propagate unchanged from the domain
    value objects that raise them.
    """


@dataclass(frozen=True, slots=True, kw_only=True)
class _FirstDirectInvocationPolicy:
    """The six configured first-DIRECT cognitive-operation policy values."""

    role: str
    mode: CognitiveMode
    max_sensitivity: ContextSensitivity
    minimum_trust: ContextTrustLevel
    context_max_tokens: int
    cognitive_budget: CognitiveBudget


@dataclass(frozen=True, slots=True, kw_only=True)
class _FirstDirectProcessConfiguration:
    """The fully resolved configuration for one first-DIRECT process run."""

    workspace_budget: WorkspaceBudget
    ollama_host: str
    model_resource: ModelResourceCapabilities
    invocation_policy: _FirstDirectInvocationPolicy


_ROOT_TABLES = frozenset({"runtime", "direct"})
_RUNTIME_TABLES = frozenset({"workspace", "ollama", "model"})
_DIRECT_TABLES = frozenset({"policy", "budget"})

_WORKSPACE_KEYS = frozenset({"max_active_items", "max_working_items", "max_peripheral_items"})
_OLLAMA_KEYS = frozenset({"host"})
_MODEL_KEYS = frozenset({"resource_ref", "provider_ref", "model_ref", "capabilities"})
_POLICY_KEYS = frozenset({"role", "mode", "max_sensitivity", "minimum_trust", "context_max_tokens"})
_BUDGET_KEYS = frozenset(
    {
        "max_time_ms",
        "max_steps",
        "max_llm_calls",
        "max_tool_calls",
        "max_cost",
        "max_tokens",
        "max_search_depth",
    }
)

_CAPABILITY_VALUES = {capability.value: capability for capability in ModelCapability}
_MODE_VALUES = {mode.value: mode for mode in CognitiveMode}
_SENSITIVITY_VALUES = {sensitivity.value: sensitivity for sensitivity in ContextSensitivity}
_TRUST_VALUES = {trust.value: trust for trust in ContextTrustLevel}


def _require_table(data: dict[str, object], key: str, path: str) -> dict[str, object]:
    """Return the required table at ``key``, or raise a schema error."""
    if key not in data:
        raise _ProcessConfigurationError(f"missing required table: {path}")
    value = data[key]
    if not isinstance(value, dict):
        raise _ProcessConfigurationError(f"{path} must be a table")
    return value


def _require_no_unknown_keys(table: dict[str, object], allowed: frozenset[str], path: str) -> None:
    """Reject any key in ``table`` outside the exact ``allowed`` set."""
    unknown = sorted(set(table) - allowed)
    if unknown:
        raise _ProcessConfigurationError(f"unknown key(s) in {path}: {', '.join(unknown)}")


def _require_str(table: dict[str, object], key: str, path: str) -> str:
    """Return the required string transport value at ``path``.``key``."""
    if key not in table:
        raise _ProcessConfigurationError(f"missing required key: {path}.{key}")
    value = table[key]
    if not isinstance(value, str):
        raise _ProcessConfigurationError(f"{path}.{key} must be a string")
    return value


def _require_int(table: dict[str, object], key: str, path: str) -> int:
    """Return the required integer transport value at ``path``.``key``.

    Rejects ``bool`` explicitly -- ``bool`` is a subtype of ``int`` in
    Python, but is not an admissible transport value for any integer leaf
    in this schema.
    """
    if key not in table:
        raise _ProcessConfigurationError(f"missing required key: {path}.{key}")
    value = table[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise _ProcessConfigurationError(f"{path}.{key} must be an integer")
    return value


def _require_str_list(table: dict[str, object], key: str, path: str) -> list[str]:
    """Return the required list-of-strings transport value at ``path``.``key``."""
    if key not in table:
        raise _ProcessConfigurationError(f"missing required key: {path}.{key}")
    value = table[key]
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise _ProcessConfigurationError(f"{path}.{key} must be a list of strings")
    return value


def _convert_capabilities(raw: list[str], path: str) -> frozenset[ModelCapability]:
    """Convert exact capability-value strings, rejecting duplicates/unknowns."""
    if len(raw) != len(set(raw)):
        raise _ProcessConfigurationError(f"{path} must not contain duplicate capabilities")
    capabilities: set[ModelCapability] = set()
    for value in raw:
        capability = _CAPABILITY_VALUES.get(value)
        if capability is None:
            raise _ProcessConfigurationError(f"{path} contains an unknown capability: {value}")
        capabilities.add(capability)
    return frozenset(capabilities)


def _convert_mode(value: str, path: str) -> CognitiveMode:
    """Convert an exact ``CognitiveMode.value`` string, rejecting unknowns."""
    mode = _MODE_VALUES.get(value)
    if mode is None:
        raise _ProcessConfigurationError(f"{path} is not a known mode: {value}")
    return mode


def _convert_sensitivity(value: str, path: str) -> ContextSensitivity:
    """Convert an exact ``ContextSensitivity.value`` string, rejecting unknowns."""
    sensitivity = _SENSITIVITY_VALUES.get(value)
    if sensitivity is None:
        raise _ProcessConfigurationError(f"{path} is not a known sensitivity: {value}")
    return sensitivity


def _convert_trust(value: str, path: str) -> ContextTrustLevel:
    """Convert an exact ``ContextTrustLevel.value`` string, rejecting unknowns."""
    trust = _TRUST_VALUES.get(value)
    if trust is None:
        raise _ProcessConfigurationError(f"{path} is not a known trust level: {value}")
    return trust


def _convert_max_cost(value: str, path: str) -> Decimal:
    """Convert an exact decimal-text transport string to ``Decimal``."""
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise _ProcessConfigurationError(f"{path} is not a valid decimal string: {value}") from exc


def _load_first_direct_process_configuration(path: Path) -> _FirstDirectProcessConfiguration:
    """Load and strictly resolve one first-DIRECT process configuration file.

    Reads exactly the caller-supplied ``path`` with stdlib ``tomllib`` --
    no default path, no parent/home-directory search, no environment
    variable read or fallback, no config-file auto-creation, no override
    layer. Every one of the 20 required leaf keys must be present with the
    exact expected transport type; any missing key, unknown key, unknown
    table, or wrong transport type raises ``_ProcessConfigurationError``.
    Existing domain value objects (``WorkspaceBudget``, ``ModelResource``,
    ``ModelResourceCapabilities``, ``CognitiveBudget``) own their own
    semantic invariants; their domain errors propagate unchanged, never
    wrapped.
    """
    with path.open("rb") as file:
        data: dict[str, object] = tomllib.load(file)

    _require_no_unknown_keys(data, _ROOT_TABLES, "<root>")
    runtime_table = _require_table(data, "runtime", "runtime")
    direct_table = _require_table(data, "direct", "direct")

    _require_no_unknown_keys(runtime_table, _RUNTIME_TABLES, "runtime")
    workspace_table = _require_table(runtime_table, "workspace", "runtime.workspace")
    ollama_table = _require_table(runtime_table, "ollama", "runtime.ollama")
    model_table = _require_table(runtime_table, "model", "runtime.model")

    _require_no_unknown_keys(direct_table, _DIRECT_TABLES, "direct")
    policy_table = _require_table(direct_table, "policy", "direct.policy")
    budget_table = _require_table(direct_table, "budget", "direct.budget")

    _require_no_unknown_keys(workspace_table, _WORKSPACE_KEYS, "runtime.workspace")
    workspace_budget = WorkspaceBudget(
        max_active_items=_require_int(workspace_table, "max_active_items", "runtime.workspace"),
        max_working_items=_require_int(workspace_table, "max_working_items", "runtime.workspace"),
        max_peripheral_items=_require_int(
            workspace_table, "max_peripheral_items", "runtime.workspace"
        ),
    )

    _require_no_unknown_keys(ollama_table, _OLLAMA_KEYS, "runtime.ollama")
    ollama_host = _require_str(ollama_table, "host", "runtime.ollama")

    _require_no_unknown_keys(model_table, _MODEL_KEYS, "runtime.model")
    model_resource = ModelResource(
        resource_ref=_require_str(model_table, "resource_ref", "runtime.model"),
        provider_ref=_require_str(model_table, "provider_ref", "runtime.model"),
        model_ref=_require_str(model_table, "model_ref", "runtime.model"),
    )
    capabilities = _convert_capabilities(
        _require_str_list(model_table, "capabilities", "runtime.model"),
        "runtime.model.capabilities",
    )
    model_resource_capabilities = ModelResourceCapabilities(
        resource=model_resource,
        capabilities=capabilities,
    )

    _require_no_unknown_keys(policy_table, _POLICY_KEYS, "direct.policy")
    role = _require_str(policy_table, "role", "direct.policy")
    mode = _convert_mode(_require_str(policy_table, "mode", "direct.policy"), "direct.policy.mode")
    max_sensitivity = _convert_sensitivity(
        _require_str(policy_table, "max_sensitivity", "direct.policy"),
        "direct.policy.max_sensitivity",
    )
    minimum_trust = _convert_trust(
        _require_str(policy_table, "minimum_trust", "direct.policy"),
        "direct.policy.minimum_trust",
    )
    context_max_tokens = _require_int(policy_table, "context_max_tokens", "direct.policy")

    _require_no_unknown_keys(budget_table, _BUDGET_KEYS, "direct.budget")
    max_time_ms = _require_int(budget_table, "max_time_ms", "direct.budget")
    cognitive_budget = CognitiveBudget(
        max_time=timedelta(milliseconds=max_time_ms),
        max_steps=_require_int(budget_table, "max_steps", "direct.budget"),
        max_llm_calls=_require_int(budget_table, "max_llm_calls", "direct.budget"),
        max_tool_calls=_require_int(budget_table, "max_tool_calls", "direct.budget"),
        max_cost=_convert_max_cost(
            _require_str(budget_table, "max_cost", "direct.budget"), "direct.budget.max_cost"
        ),
        max_tokens=_require_int(budget_table, "max_tokens", "direct.budget"),
        max_search_depth=_require_int(budget_table, "max_search_depth", "direct.budget"),
    )

    invocation_policy = _FirstDirectInvocationPolicy(
        role=role,
        mode=mode,
        max_sensitivity=max_sensitivity,
        minimum_trust=minimum_trust,
        context_max_tokens=context_max_tokens,
        cognitive_budget=cognitive_budget,
    )

    return _FirstDirectProcessConfiguration(
        workspace_budget=workspace_budget,
        ollama_host=ollama_host,
        model_resource=model_resource_capabilities,
        invocation_policy=invocation_policy,
    )


async def _execute_first_direct(
    *,
    configuration: _FirstDirectProcessConfiguration,
    problem_statement: str,
) -> ReasoningOutcome:
    """Run exactly one first-DIRECT reasoning operation end to end.

    Opens exactly one ``open_direct_runtime`` context and performs exactly
    one ``DirectReasoningOperation.execute`` call, mapping every argument
    per the frozen P2 invocation contract: ``problem_statement`` is the
    caller-supplied user input; ``task_ref``/``problem_ref`` are two
    independently generated, opaque UUID4 strings; ``goal_ref`` is fixed to
    ``None`` (first-process policy, not yet goal-integrated);
    ``required_slice_types``, ``forbidden_slice_types``, and
    ``allowed_authorities`` are empty and ``max_age`` is ``None`` (derived
    from the current no-context-retrieval first-DIRECT contract); every
    other argument comes from the configured ``_FirstDirectInvocationPolicy``.

    A ``ValueError`` raised while entering the runtime context (for example,
    an invalid Ollama host) is translated into ``_ProcessConfigurationError``
    with the original exception preserved as its ``__cause__``. A
    ``ValueError`` -- or any other exception -- raised by
    ``operation.execute`` itself is outside that translation's scope and
    propagates completely unchanged.
    """
    task_ref = str(uuid4())
    problem_ref = str(uuid4())
    policy = configuration.invocation_policy

    async with AsyncExitStack() as stack:
        try:
            operation = await stack.enter_async_context(
                open_direct_runtime(
                    workspace_budget=configuration.workspace_budget,
                    ollama_host=configuration.ollama_host,
                    model_resource=configuration.model_resource,
                )
            )
        except ValueError as exc:
            raise _ProcessConfigurationError(str(exc)) from exc

        return await operation.execute(
            role=policy.role,
            task_ref=task_ref,
            goal_ref=None,
            mode=policy.mode,
            required_slice_types=(),
            forbidden_slice_types=(),
            max_sensitivity=policy.max_sensitivity,
            minimum_trust=policy.minimum_trust,
            allowed_authorities=(),
            max_age=None,
            max_tokens=policy.context_max_tokens,
            problem_ref=problem_ref,
            problem_statement=problem_statement,
            budget=policy.cognitive_budget,
        )
