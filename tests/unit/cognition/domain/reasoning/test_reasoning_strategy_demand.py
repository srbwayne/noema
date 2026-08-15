from dataclasses import MISSING, FrozenInstanceError, fields, replace

import pytest

from noema.cognition.domain.errors import InvalidReasoningStrategyDemandError
from noema.cognition.domain.reasoning import ReasoningStrategyDemand

REQUIREMENT_FIELDS = (
    "requires_decomposition",
    "requires_hypothesis_testing",
    "requires_causal_reasoning",
    "requires_comparison",
    "requires_search",
    "requires_counterfactual",
    "requires_critique",
    "requires_tool_assistance",
    "requires_multi_model",
)


def demand(**changes: object) -> ReasoningStrategyDemand:
    values: dict[str, object] = {field_name: False for field_name in REQUIREMENT_FIELDS}
    values.update(changes)
    return ReasoningStrategyDemand(**values)


def test_reasoning_strategy_demand_has_exact_required_fields() -> None:
    contract_fields = fields(ReasoningStrategyDemand)
    assert tuple(field.name for field in contract_fields) == REQUIREMENT_FIELDS
    assert all(
        field.default is MISSING and field.default_factory is MISSING for field in contract_fields
    )


@pytest.mark.parametrize("field_name", REQUIREMENT_FIELDS)
@pytest.mark.parametrize("value", [True, False])
def test_reasoning_strategy_demand_accepts_strict_booleans(
    field_name: str,
    value: bool,
) -> None:
    assert getattr(demand(**{field_name: value}), field_name) is value


@pytest.mark.parametrize("field_name", REQUIREMENT_FIELDS)
@pytest.mark.parametrize("value", [0, 1, None, "true", [], {}])
def test_reasoning_strategy_demand_rejects_non_booleans(
    field_name: str,
    value: object,
) -> None:
    with pytest.raises(InvalidReasoningStrategyDemandError, match=field_name):
        demand(**{field_name: value})


def test_reasoning_strategy_demand_accepts_multiple_requirements() -> None:
    current = demand(requires_causal_reasoning=True, requires_counterfactual=True)
    assert current.requires_causal_reasoning is True
    assert current.requires_counterfactual is True


def test_reasoning_strategy_demand_is_frozen_slotted_keyword_only_and_equal() -> None:
    first = demand()
    second = replace(first)
    assert first == second
    assert not hasattr(first, "__dict__")
    with pytest.raises(FrozenInstanceError):
        first.requires_search = True
    with pytest.raises(TypeError):
        ReasoningStrategyDemand(False, False, False, False, False, False, False, False, False)
