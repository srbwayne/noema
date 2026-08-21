"""A bounded request to evaluate one Prediction / Counterfactual consequence."""

from dataclasses import dataclass

from noema.cognition.domain.errors import InvalidEvaluationRequestError


@dataclass(frozen=True, slots=True, kw_only=True)
class EvaluationRequest:
    """Bind a target scope, an exact consequence, and a normative statement."""

    target_ref: str
    consequence: str
    normative_statement: str

    def __post_init__(self) -> None:
        """Validate request inputs without coercion or normalization."""
        if not isinstance(self.target_ref, str) or not self.target_ref.strip():
            raise InvalidEvaluationRequestError("target_ref must be a non-empty string")
        if not isinstance(self.consequence, str) or not self.consequence.strip():
            raise InvalidEvaluationRequestError("consequence must be a non-empty string")
        if not isinstance(self.normative_statement, str) or not self.normative_statement.strip():
            raise InvalidEvaluationRequestError("normative_statement must be a non-empty string")
