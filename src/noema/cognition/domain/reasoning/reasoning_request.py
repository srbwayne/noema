"""An explicit bounded request for future reasoning execution."""

from dataclasses import dataclass

from noema.cognition.domain.budget import CognitiveBudget
from noema.cognition.domain.context_composition import ContextPackage
from noema.cognition.domain.errors import InvalidReasoningRequestError

from .reasoning_strategy import ReasoningStrategy


@dataclass(frozen=True, slots=True, kw_only=True)
class ReasoningRequest:
    """Bind a problem to bounded context, strategy, and cognitive budget."""

    problem_ref: str
    problem_statement: str
    context: ContextPackage
    strategy: ReasoningStrategy
    budget: CognitiveBudget

    def __post_init__(self) -> None:
        """Validate request inputs without coercion or duplicated context state."""
        if not isinstance(self.problem_ref, str) or not self.problem_ref.strip():
            raise InvalidReasoningRequestError("problem_ref must be a non-empty string")
        if not isinstance(self.problem_statement, str) or not self.problem_statement.strip():
            raise InvalidReasoningRequestError("problem_statement must be a non-empty string")
        if not isinstance(self.context, ContextPackage):
            raise InvalidReasoningRequestError("context must be a ContextPackage")
        if not isinstance(self.strategy, ReasoningStrategy):
            raise InvalidReasoningRequestError("strategy must be a ReasoningStrategy")
        if not isinstance(self.budget, CognitiveBudget):
            raise InvalidReasoningRequestError("budget must be a CognitiveBudget")
