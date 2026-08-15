"""A structured result of a future reasoning operation."""

from dataclasses import dataclass

from noema.cognition.domain.errors import InvalidReasoningOutcomeError

from .information_need import InformationNeed
from .reasoning_status import ReasoningStatus
from .reasoning_strategy import ReasoningStrategy


@dataclass(frozen=True, slots=True, kw_only=True)
class ReasoningOutcome:
    """Represent a communicable conclusion and any remaining information needs."""

    problem_ref: str
    strategy: ReasoningStrategy
    status: ReasoningStatus
    conclusion: str | None
    reason_summary: str
    information_needs: tuple[InformationNeed, ...]

    def __post_init__(self) -> None:
        """Validate outcome types and the semantic status matrix."""
        if not isinstance(self.problem_ref, str) or not self.problem_ref.strip():
            raise InvalidReasoningOutcomeError("problem_ref must be a non-empty string")
        if not isinstance(self.strategy, ReasoningStrategy):
            raise InvalidReasoningOutcomeError("strategy must be a ReasoningStrategy")
        if not isinstance(self.status, ReasoningStatus):
            raise InvalidReasoningOutcomeError("status must be a ReasoningStatus")
        if self.conclusion is not None and (
            not isinstance(self.conclusion, str) or not self.conclusion.strip()
        ):
            raise InvalidReasoningOutcomeError("conclusion must be None or a non-empty string")
        if not isinstance(self.reason_summary, str) or not self.reason_summary.strip():
            raise InvalidReasoningOutcomeError("reason_summary must be a non-empty string")
        if not isinstance(self.information_needs, tuple):
            raise InvalidReasoningOutcomeError("information_needs must be a tuple")
        if any(not isinstance(need, InformationNeed) for need in self.information_needs):
            raise InvalidReasoningOutcomeError(
                "information_needs must contain only InformationNeed values"
            )
        if len(self.information_needs) != len(set(self.information_needs)):
            raise InvalidReasoningOutcomeError(
                "information_needs must not contain structural duplicates"
            )
        if not self._status_is_consistent():
            raise InvalidReasoningOutcomeError(
                "status, conclusion, and information_needs are inconsistent"
            )

    def _status_is_consistent(self) -> bool:
        has_conclusion = self.conclusion is not None
        has_information_needs = bool(self.information_needs)
        return (
            self.status is ReasoningStatus.COMPLETED
            and has_conclusion
            and not has_information_needs
            or self.status is ReasoningStatus.PARTIAL
            and has_conclusion
            and has_information_needs
            or self.status is ReasoningStatus.NEEDS_INFORMATION
            and not has_conclusion
            and has_information_needs
            or self.status is ReasoningStatus.UNRESOLVED
            and not has_conclusion
            and not has_information_needs
        )
