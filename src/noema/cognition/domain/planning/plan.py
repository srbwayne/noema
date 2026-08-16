"""A structural, provider-neutral composition of plan steps toward a goal."""

from dataclasses import dataclass

from noema.cognition.domain.errors import InvalidPlanError

from .plan_step import PlanStep


@dataclass(frozen=True, slots=True, kw_only=True)
class Plan:
    """Represent a structural decomposition of a goal into dependent steps.

    ``steps`` is a frozenset because a plan expresses dependency structure,
    not execution order. Only ``PlanStep.depends_on`` constrains the
    partial order between steps; two steps that share no direct or
    transitive dependency relation carry no precedence between them, and
    none may be inferred from ``step_ref``, hashing, or insertion order.
    An empty plan is structurally valid and carries no semantic meaning
    beyond "no steps" — it does not itself represent success, failure, or
    an unresolved goal.
    """

    goal_ref: str
    steps: frozenset[PlanStep]

    def __post_init__(self) -> None:
        """Validate goal_ref, steps membership, uniqueness, resolution, and acyclicity."""
        if not isinstance(self.goal_ref, str) or not self.goal_ref.strip():
            raise InvalidPlanError("goal_ref must be a non-empty string")
        if type(self.steps) is not frozenset:
            raise InvalidPlanError("steps must be a frozenset")
        for step in self.steps:
            if not isinstance(step, PlanStep):
                raise InvalidPlanError("steps must contain only PlanStep values")

        step_refs = tuple(step.step_ref for step in self.steps)
        if len(set(step_refs)) != len(step_refs):
            raise InvalidPlanError("step_ref values must be unique")

        known_refs = set(step_refs)
        for step in self.steps:
            if not step.depends_on <= known_refs:
                raise InvalidPlanError("step dependencies must reference steps in the same plan")

        if self._has_cycle():
            raise InvalidPlanError("plan dependencies must be acyclic")

    def _has_cycle(self) -> bool:
        dependencies = {step.step_ref: step.depends_on for step in self.steps}
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(step_ref: str) -> bool:
            if step_ref in visiting:
                return True
            if step_ref in visited:
                return False
            visiting.add(step_ref)
            for dependency_ref in dependencies[step_ref]:
                if visit(dependency_ref):
                    return True
            visiting.discard(step_ref)
            visited.add(step_ref)
            return False

        return any(visit(step_ref) for step_ref in dependencies)
