from dataclasses import FrozenInstanceError, fields
from datetime import timedelta
from decimal import Decimal
from typing import get_type_hints

import pytest

from noema.cognition.domain.budget import CognitiveBudget
from noema.cognition.domain.context import ContextStamp
from noema.cognition.domain.context_composition import (
    ContextPackage,
    ContextRequest,
    ContextSensitivity,
    ContextTrustLevel,
)
from noema.cognition.domain.errors import (
    InvalidPlanError,
    InvalidPlanningRequestError,
    InvalidPlanStepError,
)
from noema.cognition.domain.modes import CognitiveMode
from noema.cognition.domain.planning import Plan, PlanningRequest, PlanStep
from noema.shared.domain import DomainError


def context_package() -> ContextPackage:
    context_request = ContextRequest(
        role="planner",
        task_ref="task:123",
        goal_ref=None,
        mode=CognitiveMode.DELIBERATE,
        required_slice_types=(),
        forbidden_slice_types=(),
        max_sensitivity=ContextSensitivity.INTERNAL,
        minimum_trust=ContextTrustLevel.UNVERIFIED,
        allowed_authorities=(),
        max_age=None,
        max_tokens=100,
        context_stamp=ContextStamp(
            workspace_version=1,
            situation_version=1,
            identity_version=1,
            goal_version=1,
            policy_version=1,
        ),
    )
    return ContextPackage(request=context_request, slices=())


def cognitive_budget() -> CognitiveBudget:
    return CognitiveBudget(
        max_time=timedelta(seconds=1),
        max_steps=1,
        max_llm_calls=0,
        max_tool_calls=0,
        max_cost=Decimal("0"),
        max_tokens=0,
        max_search_depth=0,
    )


def planning_request(**changes: object) -> PlanningRequest:
    values: dict[str, object] = {
        "goal_ref": "goal:123",
        "goal_statement": "Prepare release candidate.",
        "context": context_package(),
        "budget": cognitive_budget(),
    }
    values.update(changes)
    return PlanningRequest(**values)


def plan_step(**changes: object) -> PlanStep:
    values: dict[str, object] = {
        "step_ref": "step:a",
        "description": "Do the thing.",
        "depends_on": frozenset(),
    }
    values.update(changes)
    return PlanStep(**values)


# ---------- PlanningRequest ----------


def test_planning_request_is_frozen_slotted_and_has_no_dict() -> None:
    request = planning_request()
    assert not hasattr(request, "__dict__")
    with pytest.raises(FrozenInstanceError):
        request.goal_ref = "other"  # type: ignore[misc]


def test_planning_request_has_exact_fields() -> None:
    assert tuple(field.name for field in fields(PlanningRequest)) == (
        "goal_ref",
        "goal_statement",
        "context",
        "budget",
    )


def test_planning_request_constructor_is_keyword_only() -> None:
    with pytest.raises(TypeError):
        PlanningRequest(  # type: ignore[misc]
            "goal:123", "Do it.", context_package(), cognitive_budget()
        )


def test_planning_request_has_exact_type_hints() -> None:
    hints = get_type_hints(PlanningRequest)
    assert hints == {
        "goal_ref": str,
        "goal_statement": str,
        "context": ContextPackage,
        "budget": CognitiveBudget,
    }


@pytest.mark.parametrize("invalid_goal_ref", [None, 123, object()])
def test_planning_request_rejects_non_string_goal_ref(invalid_goal_ref: object) -> None:
    with pytest.raises(InvalidPlanningRequestError, match="goal_ref must be a non-empty string"):
        planning_request(goal_ref=invalid_goal_ref)


@pytest.mark.parametrize("blank_goal_ref", ["", " ", "\t", "\n"])
def test_planning_request_rejects_blank_goal_ref(blank_goal_ref: str) -> None:
    with pytest.raises(InvalidPlanningRequestError, match="goal_ref must be a non-empty string"):
        planning_request(goal_ref=blank_goal_ref)


def test_planning_request_preserves_goal_ref_exactly() -> None:
    request = planning_request(goal_ref="  goal:123  ")
    assert request.goal_ref == "  goal:123  "


@pytest.mark.parametrize("invalid_goal_statement", [None, 123, object()])
def test_planning_request_rejects_non_string_goal_statement(
    invalid_goal_statement: object,
) -> None:
    with pytest.raises(
        InvalidPlanningRequestError, match="goal_statement must be a non-empty string"
    ):
        planning_request(goal_statement=invalid_goal_statement)


@pytest.mark.parametrize("blank_goal_statement", ["", " ", "\t", "\n"])
def test_planning_request_rejects_blank_goal_statement(blank_goal_statement: str) -> None:
    with pytest.raises(
        InvalidPlanningRequestError, match="goal_statement must be a non-empty string"
    ):
        planning_request(goal_statement=blank_goal_statement)


def test_planning_request_preserves_goal_statement_whitespace() -> None:
    request = planning_request(goal_statement="  Prepare release candidate.  ")
    assert request.goal_statement == "  Prepare release candidate.  "


@pytest.mark.parametrize("invalid_context", [None, {}, object(), "context"])
def test_planning_request_rejects_non_context_package(invalid_context: object) -> None:
    with pytest.raises(InvalidPlanningRequestError, match="context must be a ContextPackage"):
        planning_request(context=invalid_context)


def test_planning_request_preserves_context_identity() -> None:
    the_context = context_package()
    request = planning_request(context=the_context)
    assert request.context is the_context


@pytest.mark.parametrize("invalid_budget", [None, {}, object(), "budget"])
def test_planning_request_rejects_non_cognitive_budget(invalid_budget: object) -> None:
    with pytest.raises(InvalidPlanningRequestError, match="budget must be a CognitiveBudget"):
        planning_request(budget=invalid_budget)


def test_planning_request_preserves_budget_identity() -> None:
    the_budget = cognitive_budget()
    request = planning_request(budget=the_budget)
    assert request.budget is the_budget


def test_planning_request_is_hashable() -> None:
    hash(planning_request())


def test_planning_request_structural_equality() -> None:
    the_context = context_package()
    the_budget = cognitive_budget()
    first = planning_request(context=the_context, budget=the_budget)
    second = planning_request(context=the_context, budget=the_budget)
    assert first == second
    assert hash(first) == hash(second)


# ---------- PlanStep ----------


def test_plan_step_is_frozen_slotted_and_has_no_dict() -> None:
    step = plan_step()
    assert not hasattr(step, "__dict__")
    with pytest.raises(FrozenInstanceError):
        step.step_ref = "other"  # type: ignore[misc]


def test_plan_step_has_exact_fields() -> None:
    assert tuple(field.name for field in fields(PlanStep)) == (
        "step_ref",
        "description",
        "depends_on",
    )


def test_plan_step_constructor_is_keyword_only() -> None:
    with pytest.raises(TypeError):
        PlanStep("step:a", "Do it.", frozenset())  # type: ignore[misc]


def test_plan_step_has_exact_type_hints() -> None:
    hints = get_type_hints(PlanStep)
    assert hints == {
        "step_ref": str,
        "description": str,
        "depends_on": frozenset[str],
    }


@pytest.mark.parametrize("invalid_step_ref", [None, 123, object()])
def test_plan_step_rejects_non_string_step_ref(invalid_step_ref: object) -> None:
    with pytest.raises(InvalidPlanStepError, match="step_ref must be a non-empty string"):
        plan_step(step_ref=invalid_step_ref)


@pytest.mark.parametrize("blank_step_ref", ["", " ", "\t", "\n"])
def test_plan_step_rejects_blank_step_ref(blank_step_ref: str) -> None:
    with pytest.raises(InvalidPlanStepError, match="step_ref must be a non-empty string"):
        plan_step(step_ref=blank_step_ref)


def test_plan_step_preserves_step_ref_exactly() -> None:
    step = plan_step(step_ref="  step:a  ")
    assert step.step_ref == "  step:a  "


@pytest.mark.parametrize("invalid_description", [None, 123, object()])
def test_plan_step_rejects_non_string_description(invalid_description: object) -> None:
    with pytest.raises(InvalidPlanStepError, match="description must be a non-empty string"):
        plan_step(description=invalid_description)


@pytest.mark.parametrize("blank_description", ["", " ", "\t", "\n"])
def test_plan_step_rejects_blank_description(blank_description: str) -> None:
    with pytest.raises(InvalidPlanStepError, match="description must be a non-empty string"):
        plan_step(description=blank_description)


def test_plan_step_preserves_description_whitespace() -> None:
    step = plan_step(description="  Do the thing.  ")
    assert step.description == "  Do the thing.  "


@pytest.mark.parametrize("invalid_depends_on", [None, set(), (), [], "step:a"])
def test_plan_step_rejects_non_frozenset_depends_on(invalid_depends_on: object) -> None:
    with pytest.raises(InvalidPlanStepError, match="depends_on must be a frozenset"):
        plan_step(depends_on=invalid_depends_on)


@pytest.mark.parametrize("invalid_item", [None, 123, object()])
def test_plan_step_rejects_non_string_depends_on_items(invalid_item: object) -> None:
    with pytest.raises(InvalidPlanStepError, match="depends_on items must be strings"):
        plan_step(depends_on=frozenset({invalid_item}))


@pytest.mark.parametrize("blank_dependency", ["", " ", "\t", "\n"])
def test_plan_step_rejects_blank_depends_on_items(blank_dependency: str) -> None:
    with pytest.raises(InvalidPlanStepError, match="depends_on items must be non-empty strings"):
        plan_step(depends_on=frozenset({blank_dependency}))


def test_plan_step_rejects_self_dependency() -> None:
    with pytest.raises(InvalidPlanStepError, match="step cannot depend on itself"):
        plan_step(step_ref="step:a", depends_on=frozenset({"step:a"}))


def test_plan_step_accepts_empty_depends_on() -> None:
    step = plan_step(depends_on=frozenset())
    assert step.depends_on == frozenset()


def test_plan_step_structural_equality() -> None:
    first = plan_step(depends_on=frozenset({"step:x", "step:y"}))
    second = plan_step(depends_on=frozenset({"step:y", "step:x"}))
    assert first == second
    assert hash(first) == hash(second)


# ---------- Plan ----------


def test_plan_is_frozen_slotted_and_has_no_dict() -> None:
    plan = Plan(goal_ref="goal:123", steps=frozenset())
    assert not hasattr(plan, "__dict__")
    with pytest.raises(FrozenInstanceError):
        plan.goal_ref = "other"  # type: ignore[misc]


def test_plan_has_exact_fields() -> None:
    assert tuple(field.name for field in fields(Plan)) == ("goal_ref", "steps")


def test_plan_constructor_is_keyword_only() -> None:
    with pytest.raises(TypeError):
        Plan("goal:123", frozenset())  # type: ignore[misc]


def test_plan_has_exact_type_hints() -> None:
    hints = get_type_hints(Plan)
    assert hints == {
        "goal_ref": str,
        "steps": frozenset[PlanStep],
    }


@pytest.mark.parametrize("invalid_goal_ref", [None, 123, object()])
def test_plan_rejects_non_string_goal_ref(invalid_goal_ref: object) -> None:
    with pytest.raises(InvalidPlanError, match="goal_ref must be a non-empty string"):
        Plan(goal_ref=invalid_goal_ref, steps=frozenset())  # type: ignore[arg-type]


@pytest.mark.parametrize("blank_goal_ref", ["", " ", "\t", "\n"])
def test_plan_rejects_blank_goal_ref(blank_goal_ref: str) -> None:
    with pytest.raises(InvalidPlanError, match="goal_ref must be a non-empty string"):
        Plan(goal_ref=blank_goal_ref, steps=frozenset())


def test_plan_preserves_goal_ref_exactly() -> None:
    plan = Plan(goal_ref="  goal:123  ", steps=frozenset())
    assert plan.goal_ref == "  goal:123  "


@pytest.mark.parametrize("invalid_steps", [None, set(), (), [], "step:a"])
def test_plan_rejects_non_frozenset_steps(invalid_steps: object) -> None:
    with pytest.raises(InvalidPlanError, match="steps must be a frozenset"):
        Plan(goal_ref="goal:123", steps=invalid_steps)  # type: ignore[arg-type]


@pytest.mark.parametrize("invalid_item", [None, "step:a", 123, object()])
def test_plan_rejects_non_plan_step_items(invalid_item: object) -> None:
    with pytest.raises(InvalidPlanError, match="steps must contain only PlanStep values"):
        Plan(goal_ref="goal:123", steps=frozenset({invalid_item}))


def test_plan_accepts_empty_steps() -> None:
    plan = Plan(goal_ref="goal:123", steps=frozenset())
    assert plan.steps == frozenset()


def test_plan_accepts_single_step() -> None:
    step = plan_step(step_ref="step:a", depends_on=frozenset())
    plan = Plan(goal_ref="goal:123", steps=frozenset({step}))
    assert plan.steps == frozenset({step})


def test_plan_accepts_independent_steps_without_precedence() -> None:
    step_a = plan_step(step_ref="step:a", depends_on=frozenset())
    step_b = plan_step(step_ref="step:b", depends_on=frozenset({"step:a"}))
    step_c = plan_step(step_ref="step:c", depends_on=frozenset({"step:a"}))
    plan = Plan(goal_ref="goal:123", steps=frozenset({step_a, step_b, step_c}))
    assert plan.steps == frozenset({step_a, step_b, step_c})


def test_plan_rejects_duplicate_step_ref() -> None:
    step_a = plan_step(step_ref="step:a", description="First.", depends_on=frozenset())
    step_a_again = plan_step(step_ref="step:a", description="Second.", depends_on=frozenset())
    with pytest.raises(InvalidPlanError, match="step_ref values must be unique"):
        Plan(goal_ref="goal:123", steps=frozenset({step_a, step_a_again}))


def test_plan_rejects_missing_dependency() -> None:
    step = plan_step(step_ref="step:a", depends_on=frozenset({"step:missing"}))
    with pytest.raises(
        InvalidPlanError, match="step dependencies must reference steps in the same plan"
    ):
        Plan(goal_ref="goal:123", steps=frozenset({step}))


def test_plan_rejects_two_node_cycle() -> None:
    step_a = plan_step(step_ref="step:a", depends_on=frozenset({"step:b"}))
    step_b = plan_step(step_ref="step:b", depends_on=frozenset({"step:a"}))
    with pytest.raises(InvalidPlanError, match="plan dependencies must be acyclic"):
        Plan(goal_ref="goal:123", steps=frozenset({step_a, step_b}))


def test_plan_rejects_three_node_cycle() -> None:
    step_a = plan_step(step_ref="step:a", depends_on=frozenset({"step:c"}))
    step_b = plan_step(step_ref="step:b", depends_on=frozenset({"step:a"}))
    step_c = plan_step(step_ref="step:c", depends_on=frozenset({"step:b"}))
    with pytest.raises(InvalidPlanError, match="plan dependencies must be acyclic"):
        Plan(goal_ref="goal:123", steps=frozenset({step_a, step_b, step_c}))


def test_plan_accepts_longer_acyclic_graph() -> None:
    step_a = plan_step(step_ref="step:a", depends_on=frozenset())
    step_b = plan_step(step_ref="step:b", depends_on=frozenset({"step:a"}))
    step_c = plan_step(step_ref="step:c", depends_on=frozenset({"step:b"}))
    step_d = plan_step(step_ref="step:d", depends_on=frozenset({"step:b", "step:c"}))
    plan = Plan(goal_ref="goal:123", steps=frozenset({step_a, step_b, step_c, step_d}))
    assert plan.steps == frozenset({step_a, step_b, step_c, step_d})


def test_plan_is_hashable() -> None:
    step = plan_step(step_ref="step:a", depends_on=frozenset())
    hash(Plan(goal_ref="goal:123", steps=frozenset({step})))


def test_plan_structural_equality() -> None:
    step_a = plan_step(step_ref="step:a", depends_on=frozenset())
    step_b = plan_step(step_ref="step:b", depends_on=frozenset({"step:a"}))
    first = Plan(goal_ref="goal:123", steps=frozenset({step_a, step_b}))
    second = Plan(goal_ref="goal:123", steps=frozenset({step_b, step_a}))
    assert first == second
    assert hash(first) == hash(second)


def test_plan_equality_is_independent_of_construction_order() -> None:
    step_a = plan_step(step_ref="step:a", depends_on=frozenset())
    step_b = plan_step(step_ref="step:b", depends_on=frozenset({"step:a"}))
    step_c = plan_step(step_ref="step:c", depends_on=frozenset({"step:a"}))

    plan_a = Plan(goal_ref="goal:123", steps=frozenset({step_a, step_b, step_c}))
    plan_b = Plan(goal_ref="goal:123", steps=frozenset({step_c, step_b, step_a}))

    assert plan_a == plan_b
    assert hash(plan_a) == hash(plan_b)


# ---------- errors ----------


@pytest.mark.parametrize(
    "error_type",
    [InvalidPlanningRequestError, InvalidPlanStepError, InvalidPlanError],
)
def test_planning_errors_inherit_directly_from_domain_error(
    error_type: type[DomainError],
) -> None:
    assert error_type.__bases__ == (DomainError,)


# ---------- public surface ----------


def test_planning_package_exports_expected_public_surface() -> None:
    from noema.cognition.domain import planning

    assert planning.__all__ == ["Plan", "PlanStep", "PlanningRequest"]


def test_planning_package_does_not_export_forward_looking_names() -> None:
    from noema.cognition.domain import planning

    forbidden = {"Planner", "PlannerEngine", "PlanningStatus", "PlanningOutcome"}
    public_members = {name for name in vars(planning) if not name.startswith("_")}
    assert public_members.isdisjoint(forbidden)
