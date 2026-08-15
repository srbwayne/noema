"""Deterministic selection of bounded context packages."""

from dataclasses import dataclass
from datetime import timedelta

from noema.cognition.domain.errors import (
    ContextCompositionUnsatisfiedError,
    InvalidContextComposerError,
)

from .context_candidate import ContextCandidate
from .context_composition_policy import ContextCompositionPolicy
from .context_package import ContextPackage
from .context_request import ContextRequest
from .context_sensitivity import ContextSensitivity
from .context_trust_level import ContextTrustLevel

_SENSITIVITY_PRECEDENCE = (
    ContextSensitivity.PUBLIC,
    ContextSensitivity.INTERNAL,
    ContextSensitivity.PRIVATE,
    ContextSensitivity.SECRET,
)
_TRUST_PRECEDENCE = (
    ContextTrustLevel.UNTRUSTED,
    ContextTrustLevel.UNVERIFIED,
    ContextTrustLevel.TRUSTED,
)

type _IndexedCandidate = tuple[int, ContextCandidate]


@dataclass(frozen=True, slots=True, kw_only=True)
class ContextComposer:
    """Compose the least bounded context sufficient for an explicit request."""

    policy: ContextCompositionPolicy

    def __post_init__(self) -> None:
        """Require an explicit composition policy."""
        if not isinstance(self.policy, ContextCompositionPolicy):
            raise InvalidContextComposerError("policy must be a ContextCompositionPolicy")

    def compose(
        self,
        *,
        request: ContextRequest,
        candidates: tuple[ContextCandidate, ...],
    ) -> ContextPackage:
        """Select required coverage, then bounded optional enrichment."""
        self._validate_inputs(request, candidates)
        eligible = tuple(
            (position, candidate)
            for position, candidate in enumerate(candidates)
            if self._is_eligible(request, candidate)
        )

        required = self._select_required(request, eligible)
        if len(required) > self.policy.max_slices:
            raise ContextCompositionUnsatisfiedError("required coverage exceeds policy max_slices")

        selected_positions = {position for position, _ in required}
        selected_slices = [candidate.context_slice for _, candidate in required]
        total_tokens = sum(context_slice.token_estimate for context_slice in selected_slices)
        if total_tokens > request.max_tokens:
            raise ContextCompositionUnsatisfiedError("required coverage exceeds request max_tokens")

        optional = sorted(
            (
                indexed_candidate
                for indexed_candidate in eligible
                if indexed_candidate[0] not in selected_positions
            ),
            key=self._optional_sort_key,
        )
        for _, candidate in optional:
            if len(selected_slices) == self.policy.max_slices:
                break
            context_slice = candidate.context_slice
            if total_tokens + context_slice.token_estimate > request.max_tokens:
                continue
            selected_slices.append(context_slice)
            total_tokens += context_slice.token_estimate

        return ContextPackage(request=request, slices=tuple(selected_slices))

    @staticmethod
    def _validate_inputs(request: object, candidates: object) -> None:
        if not isinstance(request, ContextRequest):
            raise InvalidContextComposerError("request must be a ContextRequest")
        if not isinstance(candidates, tuple):
            raise InvalidContextComposerError("candidates must be a tuple")
        if any(not isinstance(candidate, ContextCandidate) for candidate in candidates):
            raise InvalidContextComposerError(
                "candidates must contain only ContextCandidate values"
            )
        context_slices = tuple(candidate.context_slice for candidate in candidates)
        if len(context_slices) != len(set(context_slices)):
            raise InvalidContextComposerError(
                "candidates must not contain structural duplicate context slices"
            )

    def _is_eligible(
        self,
        request: ContextRequest,
        candidate: ContextCandidate,
    ) -> bool:
        context_slice = candidate.context_slice
        if context_slice.slice_type in request.forbidden_slice_types:
            return False
        if candidate.relevance < self.policy.minimum_relevance:
            return False
        if self._sensitivity_rank(context_slice.sensitivity) > self._sensitivity_rank(
            request.max_sensitivity
        ):
            return False
        if self._trust_rank(context_slice.trust) < self._trust_rank(request.minimum_trust):
            return False
        if request.max_age is not None and (
            candidate.age is None or candidate.age > request.max_age
        ):
            return False
        return (
            context_slice.instruction_authority is None
            or context_slice.instruction_authority in request.allowed_authorities
        )

    def _select_required(
        self,
        request: ContextRequest,
        eligible: tuple[_IndexedCandidate, ...],
    ) -> list[_IndexedCandidate]:
        selected: list[_IndexedCandidate] = []
        for required_type in request.required_slice_types:
            matching = (
                indexed_candidate
                for indexed_candidate in eligible
                if indexed_candidate[1].context_slice.slice_type is required_type
            )
            chosen = min(matching, key=self._required_sort_key, default=None)
            if chosen is None:
                raise ContextCompositionUnsatisfiedError(
                    f"required slice type {required_type.name} has no eligible candidate"
                )
            selected.append(chosen)
        return selected

    def _required_sort_key(
        self,
        indexed_candidate: _IndexedCandidate,
    ) -> tuple[int, int, int, float, int, timedelta, int]:
        position, candidate = indexed_candidate
        context_slice = candidate.context_slice
        return (
            context_slice.token_estimate,
            self._sensitivity_rank(context_slice.sensitivity),
            -self._trust_rank(context_slice.trust),
            -candidate.relevance,
            self._unknown_age_rank(candidate.age),
            candidate.age if candidate.age is not None else timedelta.max,
            position,
        )

    def _optional_sort_key(
        self,
        indexed_candidate: _IndexedCandidate,
    ) -> tuple[float, int, int, int, timedelta, int, int]:
        position, candidate = indexed_candidate
        context_slice = candidate.context_slice
        return (
            -candidate.relevance,
            -self._trust_rank(context_slice.trust),
            self._sensitivity_rank(context_slice.sensitivity),
            self._unknown_age_rank(candidate.age),
            candidate.age if candidate.age is not None else timedelta.max,
            context_slice.token_estimate,
            position,
        )

    @staticmethod
    def _sensitivity_rank(sensitivity: ContextSensitivity) -> int:
        return _SENSITIVITY_PRECEDENCE.index(sensitivity)

    @staticmethod
    def _trust_rank(trust: ContextTrustLevel) -> int:
        return _TRUST_PRECEDENCE.index(trust)

    @staticmethod
    def _unknown_age_rank(age: timedelta | None) -> int:
        return 1 if age is None else 0
