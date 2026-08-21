"""The result of evaluating one Prediction / Counterfactual consequence."""

from dataclasses import dataclass

from noema.cognition.domain.errors import InvalidEvaluationResultError

from .evaluation_status import EvaluationStatus


@dataclass(frozen=True, slots=True, kw_only=True)
class EvaluationResult:
    """Bind a target scope and consequence to a semantic utility judgment.

    ``status`` and ``utility_judgment`` are cross-validated: ``JUDGED``
    requires a non-blank textual judgment, and ``NO_JUDGMENT`` requires
    ``None``.
    """

    target_ref: str
    consequence: str
    status: EvaluationStatus
    utility_judgment: str | None

    def __post_init__(self) -> None:
        """Validate result invariants without coercion or normalization."""
        if not isinstance(self.target_ref, str) or not self.target_ref.strip():
            raise InvalidEvaluationResultError("target_ref must be a non-empty string")
        if not isinstance(self.consequence, str) or not self.consequence.strip():
            raise InvalidEvaluationResultError("consequence must be a non-empty string")
        if not isinstance(self.status, EvaluationStatus):
            raise InvalidEvaluationResultError("status must be an EvaluationStatus")
        if self.utility_judgment is not None and (
            not isinstance(self.utility_judgment, str) or not self.utility_judgment.strip()
        ):
            raise InvalidEvaluationResultError(
                "utility_judgment must be None or a non-empty string"
            )
        if not self._status_is_consistent():
            raise InvalidEvaluationResultError("status and utility_judgment are inconsistent")

    def _status_is_consistent(self) -> bool:
        has_utility_judgment = self.utility_judgment is not None
        return (
            self.status is EvaluationStatus.JUDGED
            and has_utility_judgment
            or self.status is EvaluationStatus.NO_JUDGMENT
            and not has_utility_judgment
        )
