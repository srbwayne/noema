"""The shared result of a Prediction or Counterfactual derivation."""

from dataclasses import dataclass

from noema.cognition.domain.errors import InvalidPredictionCounterfactualResultError

from .prediction_counterfactual_status import PredictionCounterfactualStatus


@dataclass(frozen=True, slots=True, kw_only=True)
class PredictionCounterfactualResult:
    """Bind a derivation target to its semantic status and consequences.

    Shared by both Prediction and Counterfactual: no intrinsic property of a
    derived consequence identifies which operation produced it, so this
    result carries no discriminator of its own. ``status`` and
    ``consequences`` are cross-validated: ``DERIVED`` requires one or more
    consequence statements, and ``INSUFFICIENT_KNOWLEDGE`` requires zero.
    """

    target_ref: str
    status: PredictionCounterfactualStatus
    consequences: tuple[str, ...]

    def __post_init__(self) -> None:
        """Validate result invariants without coercion or normalization."""
        if not isinstance(self.target_ref, str) or not self.target_ref.strip():
            raise InvalidPredictionCounterfactualResultError(
                "target_ref must be a non-empty string"
            )
        if not isinstance(self.status, PredictionCounterfactualStatus):
            raise InvalidPredictionCounterfactualResultError(
                "status must be a PredictionCounterfactualStatus"
            )
        if not isinstance(self.consequences, tuple) or not all(
            isinstance(consequence, str) for consequence in self.consequences
        ):
            raise InvalidPredictionCounterfactualResultError(
                "consequences must be a tuple of string values"
            )
        if any(not consequence.strip() for consequence in self.consequences):
            raise InvalidPredictionCounterfactualResultError(
                "consequences must contain only non-empty strings"
            )
        if len(self.consequences) != len(set(self.consequences)):
            raise InvalidPredictionCounterfactualResultError(
                "consequences must not contain duplicates"
            )
        if not self._status_is_consistent():
            raise InvalidPredictionCounterfactualResultError(
                "status and consequences are inconsistent"
            )

    def _status_is_consistent(self) -> bool:
        has_consequences = bool(self.consequences)
        return (
            self.status is PredictionCounterfactualStatus.DERIVED
            and has_consequences
            or self.status is PredictionCounterfactualStatus.INSUFFICIENT_KNOWLEDGE
            and not has_consequences
        )
