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
    """Compose the least bounded context sufficient for an explicit request.

    Eligibility is evaluated in two distinct phases sharing the same
    non-relevance guardrails (forbidden type, sensitivity, trust, age,
    instruction authority). A candidate with a known ``relevance`` must
    satisfy ``policy.minimum_relevance`` to be eligible for either phase.
    A candidate with unknown relevance (``relevance is None``, meaning no
    relevance judgment exists) may compete for required coverage only
    while its slice type is explicitly listed in
    ``request.required_slice_types`` -- required-type authority is
    coverage-bound: it never carries over to optional enrichment, and a
    surplus unknown-relevance candidate that does not win a required slot
    is never selected as optional enrichment.
    """

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
        required_eligible = tuple(
            (position, candidate)
            for position, candidate in enumerate(candidates)
            if self._is_required_coverage_eligible(request, candidate)
        )

        required = self._select_required(request, required_eligible)
        if len(required) > self.policy.max_slices:
            raise ContextCompositionUnsatisfiedError("required coverage exceeds policy max_slices")

        selected_positions = {position for position, _ in required}
        selected_slices = [candidate.context_slice for _, candidate in required]
        total_size = sum(context_slice.content_size for context_slice in selected_slices)
        if total_size > request.max_total_content_size:
            raise ContextCompositionUnsatisfiedError(
                "required coverage exceeds request max_total_content_size"
            )

        optional = sorted(
            (
                (position, candidate)
                for position, candidate in enumerate(candidates)
                if position not in selected_positions
                and self._is_optional_enrichment_eligible(request, candidate)
            ),
            key=self._optional_sort_key,
        )
        for _, candidate in optional:
            if len(selected_slices) == self.policy.max_slices:
                break
            context_slice = candidate.context_slice
            if total_size + context_slice.content_size > request.max_total_content_size:
                continue
            selected_slices.append(context_slice)
            total_size += context_slice.content_size

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

    def _is_base_eligible(
        self,
        request: ContextRequest,
        candidate: ContextCandidate,
    ) -> bool:
        """Evaluate the non-relevance guardrails shared by both composition phases."""
        context_slice = candidate.context_slice
        if context_slice.slice_type in request.forbidden_slice_types:
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

    def _is_required_coverage_eligible(
        self,
        request: ContextRequest,
        candidate: ContextCandidate,
    ) -> bool:
        """Evaluate eligibility to satisfy an explicitly required slice type.

        A known relevance score must still satisfy ``minimum_relevance``. An
        unknown relevance score (``None``) is eligible only when the
        candidate's slice type is explicitly required -- the consumer's
        explicit requirement supplies positive authority in the specific
        absence of a relevance judgment; it never overrides a known,
        below-threshold score.
        """
        if not self._is_base_eligible(request, candidate):
            return False
        if candidate.relevance is not None:
            return candidate.relevance >= self.policy.minimum_relevance
        return candidate.context_slice.slice_type in request.required_slice_types

    def _is_optional_enrichment_eligible(
        self,
        request: ContextRequest,
        candidate: ContextCandidate,
    ) -> bool:
        """Evaluate eligibility for discretionary enrichment.

        Unknown relevance is never eligible here: required-type authority is
        coverage-bound and does not extend to optional enrichment, so a
        surplus unknown-relevance candidate of a required type is excluded
        once another candidate has satisfied that requirement.
        """
        if not self._is_base_eligible(request, candidate):
            return False
        relevance = candidate.relevance
        return relevance is not None and relevance >= self.policy.minimum_relevance

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
    ) -> tuple[int, int, int, tuple[int, float | None], int, timedelta, int]:
        position, candidate = indexed_candidate
        context_slice = candidate.context_slice
        return (
            context_slice.content_size,
            self._sensitivity_rank(context_slice.sensitivity),
            -self._trust_rank(context_slice.trust),
            self._required_relevance_sort_key(candidate.relevance),
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
        relevance = candidate.relevance
        if relevance is None:
            raise InvalidContextComposerError(
                "optional ranking requires a candidate with known relevance"
            )
        return (
            -relevance,
            -self._trust_rank(context_slice.trust),
            self._sensitivity_rank(context_slice.sensitivity),
            self._unknown_age_rank(candidate.age),
            candidate.age if candidate.age is not None else timedelta.max,
            context_slice.content_size,
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

    @staticmethod
    def _required_relevance_sort_key(relevance: float | None) -> tuple[int, float | None]:
        """Rank known relevance ahead of unknown without a numeric sentinel.

        Known relevance never compares against unknown relevance directly:
        the leading discriminator (0 for known, 1 for unknown) always
        differs between the two groups, so the second element -- an actual
        score for known values, ``None`` for unknown -- is only ever
        compared within a single group, where it is either two floats or
        two ``None`` values, never one of each.
        """
        if relevance is None:
            return (1, None)
        return (0, -relevance)
