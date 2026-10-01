"""Generic application-layer contract for judging Context candidate relevance."""

from typing import Protocol, runtime_checkable

from noema.cognition.domain.context_composition import ContextCandidate


@runtime_checkable
class ContextRelevanceAuthority(Protocol):
    """Judge the relevance of ordered Context candidates to one current task.

    ADR-0041 defines this as the generic relevance integration seam: an
    authority receives the exact current ``task_ref`` and the exact ordered
    candidate tuple, and returns one relevance value per candidate in the
    same order -- ``None`` where no relevance judgment exists, otherwise a
    finite float in ``[0.0, 1.0]``. Input order is correlation authority
    only.

    The contract is independent of any particular relevance realization and
    of content resolution: an authority that needs candidate or task content
    resolves it through its own collaborators. Operational failures propagate
    unchanged; an authority never returns a partial result.
    """

    def judge(
        self,
        *,
        task_ref: str,
        candidates: tuple[ContextCandidate, ...],
    ) -> tuple[float | None, ...]:
        """Return one relevance value per candidate, in input order."""
        ...
