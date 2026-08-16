"""A single intended unit of work within a future plan."""

from dataclasses import dataclass

from noema.cognition.domain.errors import InvalidPlanStepError


@dataclass(frozen=True, slots=True, kw_only=True)
class PlanStep:
    """Describe one intended step and the steps it depends on.

    ``depends_on`` expresses partial order only: which other steps in the
    same plan this step depends on. It carries no sequence number, stage,
    or global position — a step referenced by two different dependents is
    not thereby ordered relative to them.
    """

    step_ref: str
    description: str
    depends_on: frozenset[str]

    def __post_init__(self) -> None:
        """Validate step_ref, description, and depends_on without coercion."""
        if not isinstance(self.step_ref, str) or not self.step_ref.strip():
            raise InvalidPlanStepError("step_ref must be a non-empty string")
        if not isinstance(self.description, str) or not self.description.strip():
            raise InvalidPlanStepError("description must be a non-empty string")
        if type(self.depends_on) is not frozenset:
            raise InvalidPlanStepError("depends_on must be a frozenset")
        for dependency_ref in self.depends_on:
            if not isinstance(dependency_ref, str):
                raise InvalidPlanStepError("depends_on items must be strings")
            if not dependency_ref.strip():
                raise InvalidPlanStepError("depends_on items must be non-empty strings")
        if self.step_ref in self.depends_on:
            raise InvalidPlanStepError("step cannot depend on itself")
