from dataclasses import FrozenInstanceError, fields
from datetime import timedelta
from decimal import Decimal

import pytest

from noema.cognition.domain.budget import CognitiveBudget
from noema.cognition.domain.errors import InvalidCognitiveBudgetError


def cognitive_budget(
    *,
    max_time: timedelta = timedelta(seconds=10),
    max_steps: int = 20,
    max_llm_calls: int = 2,
    max_tool_calls: int = 5,
    max_cost: Decimal = Decimal("0.10"),
    max_tokens: int = 4000,
    max_search_depth: int = 3,
) -> CognitiveBudget:
    return CognitiveBudget(
        max_time=max_time,
        max_steps=max_steps,
        max_llm_calls=max_llm_calls,
        max_tool_calls=max_tool_calls,
        max_cost=max_cost,
        max_tokens=max_tokens,
        max_search_depth=max_search_depth,
    )


def test_cognitive_budget_has_exactly_the_official_limits() -> None:
    assert tuple(field.name for field in fields(CognitiveBudget)) == (
        "max_time",
        "max_steps",
        "max_llm_calls",
        "max_tool_calls",
        "max_cost",
        "max_tokens",
        "max_search_depth",
    )


def test_cognitive_budget_is_valid_and_structurally_equal() -> None:
    first = cognitive_budget()
    second = cognitive_budget()

    assert first == second
    assert first.max_time == timedelta(seconds=10)
    assert first.max_cost == Decimal("0.10")


def test_cognitive_budget_is_immutable() -> None:
    budget = cognitive_budget()

    with pytest.raises(FrozenInstanceError):
        budget.max_steps = 30


@pytest.mark.parametrize("max_time", [timedelta(microseconds=1), timedelta(seconds=10)])
def test_cognitive_budget_accepts_positive_max_time(max_time: timedelta) -> None:
    assert cognitive_budget(max_time=max_time).max_time == max_time


@pytest.mark.parametrize(
    "max_time",
    [timedelta(0), timedelta(seconds=-1), 0, 1.0, True, None],
)
def test_cognitive_budget_rejects_invalid_max_time(max_time: object) -> None:
    with pytest.raises(InvalidCognitiveBudgetError, match="max_time"):
        cognitive_budget(max_time=max_time)  # type: ignore[arg-type]


@pytest.mark.parametrize("max_steps", [1, 20])
def test_cognitive_budget_accepts_positive_max_steps(max_steps: int) -> None:
    assert cognitive_budget(max_steps=max_steps).max_steps == max_steps


@pytest.mark.parametrize("max_steps", [0, -1, True, False, 1.0, None])
def test_cognitive_budget_rejects_invalid_max_steps(max_steps: object) -> None:
    with pytest.raises(InvalidCognitiveBudgetError, match="max_steps"):
        cognitive_budget(max_steps=max_steps)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "field_name",
    ["max_llm_calls", "max_tool_calls", "max_tokens", "max_search_depth"],
)
@pytest.mark.parametrize("value", [0, 4])
def test_cognitive_budget_accepts_non_negative_counter_limits(
    field_name: str,
    value: int,
) -> None:
    values = {field_name: value}

    budget = CognitiveBudget(
        max_time=timedelta(seconds=10),
        max_steps=20,
        max_llm_calls=values.get("max_llm_calls", 2),
        max_tool_calls=values.get("max_tool_calls", 5),
        max_cost=Decimal("0.10"),
        max_tokens=values.get("max_tokens", 4000),
        max_search_depth=values.get("max_search_depth", 3),
    )

    assert getattr(budget, field_name) == value


@pytest.mark.parametrize(
    "field_name",
    ["max_llm_calls", "max_tool_calls", "max_tokens", "max_search_depth"],
)
@pytest.mark.parametrize("value", [-1, True, False, 1.0, None])
def test_cognitive_budget_rejects_invalid_counter_limits(
    field_name: str,
    value: object,
) -> None:
    values: dict[str, object] = {field_name: value}

    with pytest.raises(InvalidCognitiveBudgetError, match=field_name):
        CognitiveBudget(
            max_time=timedelta(seconds=10),
            max_steps=20,
            max_llm_calls=values.get("max_llm_calls", 2),  # type: ignore[arg-type]
            max_tool_calls=values.get("max_tool_calls", 5),  # type: ignore[arg-type]
            max_cost=Decimal("0.10"),
            max_tokens=values.get("max_tokens", 4000),  # type: ignore[arg-type]
            max_search_depth=values.get("max_search_depth", 3),  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("max_cost", [Decimal("0"), Decimal("0.01"), Decimal("100")])
def test_cognitive_budget_accepts_valid_max_cost(max_cost: Decimal) -> None:
    assert cognitive_budget(max_cost=max_cost).max_cost == max_cost


@pytest.mark.parametrize(
    "max_cost",
    [
        Decimal("-0.01"),
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("-Infinity"),
        0,
        0.0,
        "0",
        True,
        None,
    ],
)
def test_cognitive_budget_rejects_invalid_max_cost(max_cost: object) -> None:
    with pytest.raises(InvalidCognitiveBudgetError, match="max_cost"):
        cognitive_budget(max_cost=max_cost)  # type: ignore[arg-type]


def test_zero_resource_cognitive_budget_is_valid() -> None:
    budget = CognitiveBudget(
        max_time=timedelta(microseconds=1),
        max_steps=1,
        max_llm_calls=0,
        max_tool_calls=0,
        max_cost=Decimal("0"),
        max_tokens=0,
        max_search_depth=0,
    )

    assert budget.max_llm_calls == 0
    assert budget.max_tool_calls == 0
    assert budget.max_cost == Decimal("0")
    assert budget.max_tokens == 0
    assert budget.max_search_depth == 0
