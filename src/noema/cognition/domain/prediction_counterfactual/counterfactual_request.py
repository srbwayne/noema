"""A bounded request for a future counterfactual derivation."""

from dataclasses import dataclass

from noema.cognition.domain.errors import InvalidCounterfactualRequestError


@dataclass(frozen=True, slots=True, kw_only=True)
class CounterfactualRequest:
    """Bind a baseline, a derivation target, and explicit hypothetical divergences."""

    baseline_ref: str
    target_ref: str
    target_statement: str
    divergence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        """Validate request inputs without coercion or normalization."""
        if not isinstance(self.baseline_ref, str) or not self.baseline_ref.strip():
            raise InvalidCounterfactualRequestError("baseline_ref must be a non-empty string")
        if not isinstance(self.target_ref, str) or not self.target_ref.strip():
            raise InvalidCounterfactualRequestError("target_ref must be a non-empty string")
        if not isinstance(self.target_statement, str) or not self.target_statement.strip():
            raise InvalidCounterfactualRequestError("target_statement must be a non-empty string")
        if not isinstance(self.divergence_refs, tuple) or not all(
            isinstance(reference, str) for reference in self.divergence_refs
        ):
            raise InvalidCounterfactualRequestError(
                "divergence_refs must be a tuple of string values"
            )
        if not self.divergence_refs:
            raise InvalidCounterfactualRequestError(
                "divergence_refs must contain at least one reference"
            )
        if any(not reference.strip() for reference in self.divergence_refs):
            raise InvalidCounterfactualRequestError(
                "divergence_refs must contain only non-empty strings"
            )
        if len(self.divergence_refs) != len(set(self.divergence_refs)):
            raise InvalidCounterfactualRequestError("divergence_refs must not contain duplicates")
