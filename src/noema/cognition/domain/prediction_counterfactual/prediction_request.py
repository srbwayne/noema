"""A bounded request for a future prediction derivation."""

from dataclasses import dataclass

from noema.cognition.domain.errors import InvalidPredictionRequestError


@dataclass(frozen=True, slots=True, kw_only=True)
class PredictionRequest:
    """Bind a baseline and a derivation target for prediction, without divergence."""

    baseline_ref: str
    target_ref: str
    target_statement: str

    def __post_init__(self) -> None:
        """Validate request inputs without coercion or normalization."""
        if not isinstance(self.baseline_ref, str) or not self.baseline_ref.strip():
            raise InvalidPredictionRequestError("baseline_ref must be a non-empty string")
        if not isinstance(self.target_ref, str) or not self.target_ref.strip():
            raise InvalidPredictionRequestError("target_ref must be a non-empty string")
        if not isinstance(self.target_statement, str) or not self.target_statement.strip():
            raise InvalidPredictionRequestError("target_statement must be a non-empty string")
