"""A bounded request for a future planning operation."""

from dataclasses import dataclass

from noema.cognition.domain.budget import CognitiveBudget
from noema.cognition.domain.context_composition import ContextPackage
from noema.cognition.domain.errors import InvalidPlanningRequestError


@dataclass(frozen=True, slots=True, kw_only=True)
class PlanningRequest:
    """Bind a goal to bounded context and cognitive budget for future planning.

    This request does not select context or consume budget; it references
    the ``ContextPackage`` and ``CognitiveBudget`` already composed for
    it, the same way ``ReasoningRequest`` references them for reasoning.
    """

    goal_ref: str
    goal_statement: str
    context: ContextPackage
    budget: CognitiveBudget

    def __post_init__(self) -> None:
        """Validate request inputs without coercion or duplicated context state."""
        if not isinstance(self.goal_ref, str) or not self.goal_ref.strip():
            raise InvalidPlanningRequestError("goal_ref must be a non-empty string")
        if not isinstance(self.goal_statement, str) or not self.goal_statement.strip():
            raise InvalidPlanningRequestError("goal_statement must be a non-empty string")
        if not isinstance(self.context, ContextPackage):
            raise InvalidPlanningRequestError("context must be a ContextPackage")
        if not isinstance(self.budget, CognitiveBudget):
            raise InvalidPlanningRequestError("budget must be a CognitiveBudget")
